"""Orchestrate deterministic map, graph expansion, full-text chunks, and semantic fallback."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from gdpr_ai.config import settings
from gdpr_ai.models import ClassifiedTopics, ExtractedEntities, RetrievedChunk
from gdpr_ai.retrieval.article_map import primary_article_number, resolve_articles
from gdpr_ai.retrieval.article_store import assemble_context, eurlex_source_url
from gdpr_ai.retrieval.cross_ref_graph import expand_articles

logger = logging.getLogger(__name__)


def _article_nums_from_chunks(chunks: list[RetrievedChunk]) -> set[str]:
    """Extract primary numeric article ids referenced in chunk metadata."""
    out: set[str] = set()
    for c in chunks:
        lbl = str(c.metadata.get("article_number", ""))
        m = re.search(r"(\d+)", lbl)
        if m:
            out.add(m.group(1))
        assembled = str(c.metadata.get("assembled_articles", ""))
        for part in re.split(r"[\n,]+", assembled):
            p = part.strip()
            if p.isdigit():
                out.add(p)
    return out


def _dedupe_chunks_by_id(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Preserve order; drop duplicate chunk ids."""
    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for c in chunks:
        if c.chunk_id in seen:
            continue
        seen.add(c.chunk_id)
        out.append(c)
    return out


def _with_retrieval_source(chunk: RetrievedChunk, source: str) -> RetrievedChunk:
    """Return a copy of chunk with ``retrieval_source`` set (explainability)."""
    meta = dict(chunk.metadata)
    meta["retrieval_source"] = source
    return chunk.model_copy(update={"metadata": meta})


@dataclass
class RetrievalResult:
    """Outputs of the v4 retrieval path plus explainability metadata."""

    chunks: list[RetrievedChunk]
    articles_from_map: set[str] = field(default_factory=set)
    articles_from_graph: set[str] = field(default_factory=set)
    articles_from_semantic: set[str] = field(default_factory=set)
    all_articles: set[str] = field(default_factory=set)
    full_text_context: str = ""
    recitals: set[str] = field(default_factory=set)
    retrieval_metadata: dict[str, Any] = field(default_factory=dict)


def _entity_keywords(entities: ExtractedEntities) -> list[str]:
    parts: list[str] = []
    parts.extend(entities.actors)
    parts.extend(entities.data_types)
    parts.extend(entities.processing_activities)
    parts.extend(entities.legal_bases_mentioned)
    if entities.summary:
        parts.append(entities.summary)
    return parts


def _synthetic_chunk(
    *,
    chunk_id: str,
    article_num: str,
    text: str,
    tier: str,
    recital_nums: list[str] | None = None,
) -> RetrievedChunk:
    label = f"Art. {primary_article_number(article_num)}"
    meta: dict[str, str] = {
        "article_number": label,
        "source": "gdpr_fulltext",
        "source_url": eurlex_source_url(),
        "topic_tags": "",
        "retrieval_tier": tier,
        "full_citation": f"{label} GDPR",
    }
    if recital_nums:
        meta["recitals"] = ",".join(recital_nums)
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata=meta,
        similarity_score=1.0,
        dense_score=1.0,
        bm25_score=0.0,
    )


def _fulltext_chunks_for_articles(
    articles: set[str],
    *,
    tier: str,
    block: str,
) -> list[RetrievedChunk]:
    """One synthetic chunk holding the assembled multi-article block."""
    if not block.strip():
        return []
    nums = sorted({primary_article_number(a) for a in articles}, key=int)
    cid = f"fulltext:gdpr:{'-'.join(nums[:12])}" + (":more" if len(nums) > 12 else "")
    joined = "\n".join(nums)
    ch = _synthetic_chunk(
        chunk_id=cid,
        article_num=nums[0] if nums else "0",
        text=block,
        tier=tier,
    )
    ch.metadata["assembled_articles"] = joined[:2000]
    return [ch]


def retrieve_deterministic(
    query: str,
    topics: ClassifiedTopics,
    entities: ExtractedEntities,
    *,
    semantic_retrieve_fn: Callable[..., list[RetrievedChunk]],
    top_k: int | None = None,
    use_semantic_fallback: bool = True,
    graph_depth: int | None = None,
    max_context_tokens: int | None = None,
) -> RetrievalResult:
    """Layer 1–3 orchestration: map → expand → always merge hybrid semantic when enabled.

    When ``use_semantic_fallback`` is True (default from ``retrieve()``), runs full ``top_k``
    semantic retrieval and unions it with deterministic map/graph articles. Deterministic
    full-text chunks are added only for articles not already covered by semantic chunk
    metadata, so chunk/RAG-shaped context is preserved while map-only articles are
    supplemented with assembled GDPR full text.
    """
    k = top_k if top_k is not None else settings.top_k
    depth = settings.deterministic_graph_depth if graph_depth is None else graph_depth
    max_tok = (
        settings.deterministic_max_context_tokens
        if max_context_tokens is None
        else max_context_tokens
    )

    kw = _entity_keywords(entities)
    gdpr_map, recitals, _bdsg, _ttdsg = resolve_articles(topics.topics or [], kw, text_blob=query)
    mapped_norm = {primary_article_number(a) for a in gdpr_map}
    expanded = expand_articles(mapped_norm, depth=depth)
    graph_only = expanded - mapped_norm
    all_art = set(mapped_norm) | set(expanded)

    semantic: list[RetrievedChunk] = []
    sem_arts: set[str] = set()
    if use_semantic_fallback:
        semantic = semantic_retrieve_fn(query, topics, entities, top_k=k)
        sem_arts = _article_nums_from_chunks(semantic)

    all_article_union = all_art | sem_arts
    sem_only = sem_arts - all_art
    priority_list = (
        sorted(mapped_norm, key=int)
        + sorted(graph_only, key=int)
        + sorted(sem_only, key=int)
    )

    full_block = assemble_context(
        all_article_union,
        max_tokens=max_tok,
        priority_order=priority_list,
    )

    meta: dict[str, Any] = {
        "mapped_article_count": len(mapped_norm),
        "expanded_article_count": len(all_art),
        "recital_count": len(recitals),
    }

    article_sources: dict[str, list[str]] = {}
    for a in sem_arts:
        article_sources.setdefault(a, []).append("semantic")
    for a in mapped_norm:
        article_sources.setdefault(a, []).append("map")
    for a in graph_only:
        article_sources.setdefault(a, []).append("graph")
    for key, paths in article_sources.items():
        article_sources[key] = sorted(frozenset(paths))
    meta["article_sources"] = article_sources

    extra_arts = all_art - sem_arts
    supp_chunks: list[RetrievedChunk] = []
    if extra_arts:
        supp_block = assemble_context(
            extra_arts,
            max_tokens=max_tok,
            priority_order=sorted(extra_arts, key=int),
        )
        raw_supp = _fulltext_chunks_for_articles(extra_arts, tier="map+graph", block=supp_block)
        supp_chunks = [_with_retrieval_source(c, "deterministic_map_graph") for c in raw_supp]

    semantic_tagged = [_with_retrieval_source(c, "semantic") for c in semantic]
    out_chunks = _dedupe_chunks_by_id(semantic_tagged + supp_chunks)

    return RetrievalResult(
        chunks=out_chunks,
        articles_from_map=mapped_norm,
        articles_from_graph=graph_only,
        articles_from_semantic=sem_arts,
        all_articles=all_article_union,
        full_text_context=full_block,
        recitals=set(recitals),
        retrieval_metadata=meta,
    )
