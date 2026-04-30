"""
Extract GDPR article (and recital) text from existing ChromaDB chunks.

Reassembles chunked articles by metadata. Use when EUR-Lex scraping is unavailable.
Run: uv run python scripts/extract_articles_from_chroma.py
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import chromadb

from gdpr_ai.config import settings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
RAW_ART_OUT = ROOT / "data" / "raw" / "gdpr_articles.json"
RAW_REC_OUT = ROOT / "data" / "raw" / "gdpr_recitals.json"


def _meta_str(meta: dict[str, Any] | None, key: str) -> str:
    if not meta or key not in meta:
        return ""
    v = meta[key]
    return "" if v is None else str(v).strip()


def _gdpr_chunk(meta: dict[str, Any] | None) -> bool:
    src = _meta_str(meta, "source").lower()
    return "gdpr" in src


def _chunk_sort_key(meta: dict[str, Any] | None) -> tuple[int, str]:
    raw = _meta_str(meta, "chunk_index")
    try:
        return (int(raw), "")
    except ValueError:
        return (10**9, raw)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    path = settings.chroma_path.resolve()
    if not path.exists():
        logger.error("Chroma path missing: %s", path)
        raise SystemExit(1)
    client = chromadb.PersistentClient(path=str(path))
    try:
        coll = client.get_collection(settings.chroma_collection)
    except Exception as exc:
        logger.error("Open collection failed: %s", exc)
        raise SystemExit(1) from exc

    total = coll.count()
    if total == 0:
        logger.error("Chroma collection %s is empty.", settings.chroma_collection)
        raise SystemExit(1)
    batch = 5000
    article_parts: dict[str, list[tuple[tuple[int, str], str, dict[str, Any]]]] = defaultdict(list)
    recital_parts: dict[str, list[tuple[tuple[int, str], str, dict[str, Any]]]] = defaultdict(list)

    for offset in range(0, total, batch):
        chunk = coll.get(
            include=["documents", "metadatas"],
            limit=min(batch, total - offset),
            offset=offset,
        )
        ids = chunk.get("ids") or []
        docs = chunk.get("documents") or []
        metas = chunk.get("metadatas") or []
        for _cid, doc, meta in zip(ids, docs, metas, strict=True):
            if not doc or not meta:
                continue
            if not _gdpr_chunk(meta):
                continue
            art = _meta_str(meta, "article_number")
            rnum_meta = _meta_str(meta, "recital_number")
            m_rec_inline = re.search(r"recital\s*\(?\s*(\d+)", art, re.I)
            kind_recital = _meta_str(meta, "kind").lower() == "recital"
            is_recital = bool(rnum_meta) or bool(m_rec_inline) or kind_recital
            if is_recital:
                rnum = rnum_meta
                if not rnum and m_rec_inline:
                    rnum = m_rec_inline.group(1)
                if not rnum:
                    continue
                key = str(int(rnum)) if rnum.isdigit() else rnum
                recital_parts[key].append((_chunk_sort_key(meta), doc, meta))
                continue
            if art:
                m_art = re.search(r"(?i)art(?:icle)?\.?\s*(\d+)", art)
                if not m_art:
                    m_art = re.search(r"^(\d+)$", art.strip())
                if not m_art:
                    continue
                num = m_art.group(1)
                article_parts[num].append((_chunk_sort_key(meta), doc, meta))

    articles_json: list[dict[str, str]] = []
    for num in sorted(article_parts.keys(), key=int):
        parts = sorted(article_parts[num], key=lambda x: x[0])
        text = "\n\n".join(p[1].strip() for p in parts if p[1].strip())
        title = ""
        chapter = ""
        if parts:
            t = _meta_str(parts[0][2], "title")
            if t:
                title = t
            c = _meta_str(parts[0][2], "chapter")
            if c:
                chapter = c
        articles_json.append(
            {"article_number": num, "title": title, "chapter": chapter, "text": text},
        )

    recitals_json: list[dict[str, str]] = []
    for num in sorted(recital_parts.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        parts = sorted(recital_parts[num], key=lambda x: x[0])
        text = "\n\n".join(p[1].strip() for p in parts if p[1].strip())
        recitals_json.append({"number": num, "text": text})

    RAW_ART_OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_ART_OUT.write_text(
        json.dumps(articles_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Wrote %s articles to %s", len(articles_json), RAW_ART_OUT)

    if recitals_json:
        RAW_REC_OUT.write_text(
            json.dumps(recitals_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Wrote %s recitals to %s", len(recitals_json), RAW_REC_OUT)

    have = {a["article_number"] for a in articles_json}
    missing = [str(i) for i in range(1, 100) if str(i) not in have]
    if missing:
        logger.warning(
            "Missing %s GDPR articles from Chroma: %s",
            len(missing),
            ", ".join(missing[:20]),
        )
        if len(missing) > 20:
            logger.warning("(trimmed listing; total missing %s)", len(missing))


if __name__ == "__main__":
    main()
