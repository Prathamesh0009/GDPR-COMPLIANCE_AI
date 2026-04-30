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
    """Layer 1–3 orchestration: map → expand → optional semantic merge."""
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

    priority_list = sorted(mapped_norm, key=int) + sorted(graph_only, key=int)

    full_block = assemble_context(
        all_art,
        max_tokens=max_tok,
        priority_order=priority_list,
    )
    ft_chunks = _fulltext_chunks_for_articles(all_art, tier="map+graph", block=full_block)

    meta: dict[str, Any] = {
        "mapped_article_count": len(mapped_norm),
        "expanded_article_count": len(all_art),
        "recital_count": len(recitals),
    }

    semantic: list[RetrievedChunk] = []
    sem_arts: set[str] = set()
    if use_semantic_fallback and settings.deterministic_semantic_fallback:
        semantic = semantic_retrieve_fn(query, topics, entities, top_k=max(6, k // 2))
        for c in semantic:
            lbl = str(c.metadata.get("article_number", ""))
            m = re.search(r"(\d+)", lbl)
            if m:
                sem_arts.add(m.group(1))

    out_chunks = (ft_chunks + semantic)[:k]

    return RetrievalResult(
        chunks=out_chunks,
        articles_from_map=mapped_norm,
        articles_from_graph=graph_only,
        articles_from_semantic=sem_arts,
        all_articles=all_art | sem_arts,
        full_text_context=full_block,
        recitals=set(recitals),
        retrieval_metadata=meta,
    )
