#!/usr/bin/env python3
"""Build EDPB consent-guidance-shaped JSON (scrape or curated fallback)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx
from _http import DEFAULT_HEADERS
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "consent_guidance.json"

EDPB_URL = (
    "https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/"
    "guidelines-052020-consent-under-regulation-2016679_en"
)

FALLBACK: dict = {
    "document_id": "EDPB-Guidelines-05-2020",
    "source_url": EDPB_URL,
    "sections": [
        {
            "heading": "Valid consent conditions",
            "text": (
                "Consent must be freely given, specific, informed and unambiguous (Article 4(11) "
                "and Article 7 GDPR). Bundling consent with non-negotiable terms can invalidate "
                "consent if refusal would deny the core service without necessity. Consent "
                "requests must be clearly distinguishable from other matters."
            ),
        },
        {
            "heading": "Granularity and withdrawal",
            "text": (
                "Consent should be granular per purpose where appropriate. Withdrawal must be "
                "as easy as giving consent; controllers should document consent records including "
                "time, method, and information shown."
            ),
        },
        {
            "heading": "Consent versus legitimate interests",
            "text": (
                "Where Article 6(1)(f) legitimate interests is considered, a balancing test is "
                "required: necessity, reasonable expectations, impact on data subjects, and "
                "safeguards. Consent may still be appropriate where interests are not balanced "
                "in the data subject's favour or where national law requires consent."
            ),
        },
        {
            "heading": "Children's consent",
            "text": (
                "Article 8: where information society services are offered directly to a child, "
                "consent of the holder of parental responsibility may be required depending on "
                "Member State age between 13 and 16."
            ),
        },
    ],
}


def _try_scrape() -> dict | None:
    try:
        with httpx.Client(timeout=30.0, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
            r = client.get(EDPB_URL)
            r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("EDPB consent page fetch failed: %s", exc)
        return None
    soup = BeautifulSoup(r.text, "lxml")
    main = soup.find("article") or soup.find("div", class_="content") or soup.body
    if main is None:
        return None
    paragraphs = [p.get_text(" ", strip=True) for p in main.find_all("p")]
    text = "\n\n".join(p for p in paragraphs if p)
    if len(text) < 200:
        return None
    return {
        "document_id": "EDPB-Guidelines-05-2020-scraped",
        "source_url": str(r.url),
        "sections": [
            {"heading": "EDPB consent guidelines (scraped excerpt)", "text": text[:12000]},
        ],
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    data = _try_scrape() or FALLBACK
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %s", OUT)


if __name__ == "__main__":
    main()
