#!/usr/bin/env python3
"""Build EU AI Act article excerpts JSON (EUR-Lex scrape with curated fallback)."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import httpx
from _http import DEFAULT_HEADERS
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "ai_act_articles.json"

CELEX_HTML = (
    "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
)

# Short official-style excerpts; expand via scrape when possible.
FALLBACK_ARTICLES = [
    {
        "article_number": "10",
        "title": "Data and data governance",
        "text": (
            "High-risk AI systems shall be designed and developed following rights-based "
            "principles, with training, validation and testing data subject to appropriate "
            "data governance practices. Relevant for alignment with GDPR data quality and "
            "lawful processing expectations when personal data are used in AI pipelines."
        ),
    },
    {
        "article_number": "13",
        "title": "Transparency and provision of information to deployers",
        "text": (
            "Providers shall ensure high-risk AI systems are accompanied by instructions for "
            "use containing required transparency elements so deployers can interpret "
            "system output and comply with obligations — intersecting with GDPR transparency "
            "when outputs affect individuals."
        ),
    },
    {
        "article_number": "14",
        "title": "Human oversight",
        "text": (
            "High-risk AI systems shall be designed to be effectively overseen by natural "
            "persons during the period in which the system is in use — relevant where "
            "automated processing impacts data subjects."
        ),
    },
    {
        "article_number": "26",
        "title": "Obligations of deployers of high-risk AI systems",
        "text": (
            "Deployers shall assign human oversight, monitor operation, keep logs where "
            "required, and perform fundamental rights impact assessment where applicable — "
            "overlapping in practice with DPIA-style analysis under GDPR for high-risk "
            "processing of personal data."
        ),
    },
    {
        "article_number": "27",
        "title": "Fundamental rights impact assessment for high-risk AI systems",
        "text": (
            "Deployers shall perform an assessment of the impact on fundamental rights "
            "prior to putting a high-risk system into use — distinct from but complementary "
            "to GDPR DPIA where personal data processing presents high risk."
        ),
    },
]


def _extract_articles_from_html(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    text_blocks: list[str] = []
    for node in soup.find_all(["p", "div"]):
        t = node.get_text(" ", strip=True)
        if len(t) > 40 and re.match(r"Article\s+\d+", t):
            text_blocks.append(t)
    if not text_blocks:
        return []
    wanted = {"10", "13", "14", "26", "27"}
    out: list[dict[str, str]] = []
    for block in text_blocks:
        m = re.match(r"Article\s+(\d+)\s*[—\-]?\s*(.*)", block, re.I)
        if not m:
            continue
        num, rest = m.group(1), m.group(2)
        if num not in wanted:
            continue
        title = rest.split(".")[0][:200] if rest else ""
        out.append({"article_number": num, "title": title.strip(), "text": block[:8000]})
    return out


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    articles: list[dict[str, str]] = []
    try:
        with httpx.Client(timeout=45.0, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
            r = client.get(CELEX_HTML)
            r.raise_for_status()
            articles = _extract_articles_from_html(r.text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("EUR-Lex AI Act fetch/parse failed: %s", exc)
    if len(articles) < 3:
        logger.info("Using curated AI Act excerpts (scrape yielded %s articles)", len(articles))
        articles = [
            {**a, "source_url": CELEX_HTML} for a in FALLBACK_ARTICLES
        ]
    else:
        for a in articles:
            a.setdefault("source_url", CELEX_HTML)
    payload = {"source_url": CELEX_HTML, "articles": articles}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %s (%s articles)", OUT, len(articles))


if __name__ == "__main__":
    main()
