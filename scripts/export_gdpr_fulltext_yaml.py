#!/usr/bin/env python3
"""Export GDPR article and recital YAML from scraped JSON under ``data/raw/``."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW_ART = ROOT / "data" / "raw" / "gdpr_articles.json"
RAW_REC = ROOT / "data" / "raw" / "gdpr_recitals.json"
OUT_ART = ROOT / "data" / "gdpr_articles_fulltext.yaml"
OUT_REC = ROOT / "data" / "gdpr_recitals_fulltext.yaml"

logger = logging.getLogger(__name__)


def _export_articles() -> int:
    """Write ``data/gdpr_articles_fulltext.yaml``; return article count."""
    if not RAW_ART.exists():
        msg = f"Missing {RAW_ART}; run scripts/scrape_gdpr.py or extract_articles_from_chroma.py."
        raise SystemExit(msg)
    rows = json.loads(RAW_ART.read_text(encoding="utf-8"))
    articles: dict[str, dict[str, str | None]] = {}
    for a in rows:
        num = str(a.get("article_number", "")).strip()
        if not num.isdigit():
            continue
        articles[num] = {
            "title": str(a.get("title", "")).strip(),
            "chapter": str(a.get("chapter", "")).strip(),
            "section": None,
            "full_text": str(a.get("text", "")).strip(),
        }
    payload = {"articles": articles}
    OUT_ART.parent.mkdir(parents=True, exist_ok=True)
    OUT_ART.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    return len(articles)


def _export_recitals() -> int:
    """Write ``data/gdpr_recitals_fulltext.yaml``; return recital count."""
    if not RAW_REC.exists():
        logger.warning("No %s; skipping recitals YAML.", RAW_REC)
        return 0
    rows = json.loads(RAW_REC.read_text(encoding="utf-8"))
    recitals: dict[str, dict[str, str]] = {}
    for r in rows:
        num = str(r.get("number", r.get("recital_number", ""))).strip()
        if not num.isdigit():
            continue
        body = str(r.get("text", "")).strip()
        recitals[num] = {"full_text": body}
    payload = {"recitals": recitals}
    OUT_REC.parent.mkdir(parents=True, exist_ok=True)
    OUT_REC.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    return len(recitals)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    n_art = _export_articles()
    logger.info("Wrote %s articles to %s", n_art, OUT_ART)
    n_rec = _export_recitals()
    if n_rec:
        logger.info("Wrote %s recitals to %s", n_rec, OUT_REC)


if __name__ == "__main__":
    main()
