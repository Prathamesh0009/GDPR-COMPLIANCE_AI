#!/usr/bin/env python3
"""Export ``data/gdpr_articles_fulltext.yaml`` from scraped ``data/raw/gdpr_articles.json``."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "gdpr_articles.json"
OUT = ROOT / "data" / "gdpr_articles_fulltext.yaml"


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"Missing {RAW}; run scripts/scrape_gdpr.py first.")
    rows = json.loads(RAW.read_text(encoding="utf-8"))
    articles: dict[str, dict] = {}
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    print(f"Wrote {len(articles)} articles to {OUT}")


if __name__ == "__main__":
    main()
