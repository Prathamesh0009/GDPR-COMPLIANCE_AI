#!/usr/bin/env python3
"""Fetch or synthesise EDPB-style DPIA guidance JSON into ``data/raw/dpia_guidance.json``."""
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
OUT = RAW / "dpia_guidance.json"

# Curated fallback aligned with EDPB WP 248 structure (offline build).
FALLBACK: dict = {
    "document_id": "EDPB-Guidelines-WP248-rev01",
    "source_url": "https://www.edpb.europa.eu/system/files/2021-10/edpb_guidelines_201901_wp248_rev01_en.pdf",
    "sections": [
        {
            "heading": "When is a DPIA required",
            "text": (
                "A data protection impact assessment (DPIA) is required when processing "
                "is likely to result in a high risk to the rights and freedoms of natural persons. "
                "Article 35(3) GDPR lists examples: systematic evaluation based on automated "
                "processing including profiling; large-scale processing of special categories; "
                "systematic monitoring of publicly accessible areas. Supervisory authorities "
                "may publish lists of processing operations requiring a DPIA (Article 35(4))."
            ),
        },
        {
            "heading": "Minimum content of a DPIA",
            "text": (
                "Article 35(7) requires: a systematic description of processing operations and "
                "purposes; assessment of necessity and proportionality; assessment of risks to "
                "data subjects; measures to address risks including safeguards and security "
                "measures. The controller should consult the processor where processing is "
                "carried out on its behalf. Prior consultation with the supervisory authority "
                "is required when residual high risk remains (Article 36)."
            ),
        },
        {
            "heading": "Necessity and proportionality",
            "text": (
                "The DPIA should demonstrate that personal data processing is necessary for "
                "the stated purposes and proportionate to the aims, applying data minimisation "
                "(Article 5(1)(c)) and evaluating less intrusive alternatives where feasible."
            ),
        },
        {
            "heading": "Risk assessment methodology",
            "text": (
                "Identify likelihood and severity of physical, material or non-material damage "
                "to data subjects. Consider confidentiality, integrity, availability breaches, "
                "discrimination, identity theft, financial loss, reputational harm, loss of "
                "control over personal data. Document mitigation measures and residual risk."
            ),
        },
    ],
}

NEWSROOM_URL = (
    "https://ec.europa.eu/newsroom/article29/items/611236/printable"
    "?language=en&itemType=256"
)


def _try_scrape_ec_newsroom() -> dict | None:
    try:
        with httpx.Client(timeout=30.0, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
            r = client.get(NEWSROOM_URL)
            r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("EC newsroom fetch failed: %s", exc)
        return None
    soup = BeautifulSoup(r.text, "lxml")
    main = soup.find("article") or soup.find("main") or soup.body
    if main is None:
        return None
    paragraphs = [p.get_text(" ", strip=True) for p in main.find_all("p")]
    text = "\n\n".join(p for p in paragraphs if p)
    if len(text) < 200:
        return None
    return {
        "document_id": "EC-Article29-DPIA-newsroom",
        "source_url": str(r.url),
        "sections": [{"heading": "DPIA guidance (scraped excerpt)", "text": text[:12000]}],
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    data = _try_scrape_ec_newsroom() or FALLBACK
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %s", OUT)


if __name__ == "__main__":
    main()
