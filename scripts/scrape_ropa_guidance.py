#!/usr/bin/env python3
"""Build Article 30 RoPA template JSON and optional excerpt from ``gdpr_articles.json``."""
from __future__ import annotations

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
GDPR_ART = RAW / "gdpr_articles.json"
OUT = RAW / "ropa_template.json"

CONTROLLER_FIELDS = [
    {
        "field": "Name and contact details of the controller",
        "description": "Identity and contact data for the controller (and joint controllers).",
        "example": "ACME GmbH, privacy@acme.example",
    },
    {
        "field": "Purposes of processing",
        "description": "Each distinct purpose for which personal data are processed.",
        "example": "Customer billing, product analytics, support ticketing",
    },
    {
        "field": "Categories of data subjects",
        "description": "Whose data is processed (customers, employees, children, etc.).",
        "example": "Customers, website visitors",
    },
    {
        "field": "Categories of personal data",
        "description": "Types of data (contact, financial, health, etc.).",
        "example": "Email, IP address, payment card metadata",
    },
    {
        "field": "Categories of recipients",
        "description": "Who receives the data (processors, joint controllers, third parties).",
        "example": "Cloud host EU, payment processor, email vendor",
    },
    {
        "field": "Transfers to third countries",
        "description": "Destinations and safeguards (SCCs, adequacy, BCRs).",
        "example": "US processor — SCCs 2021 + TIA on file",
    },
    {
        "field": "Retention periods",
        "description": "Criteria used to determine how long data are stored.",
        "example": "Invoices 10 years; marketing consents until withdrawal + audit trail",
    },
    {
        "field": "Technical and organisational measures (Article 32)",
        "description": "Summary of security measures; detail may live in separate TOM register.",
        "example": "Encryption at rest, RBAC, logging, backup encryption",
    },
]

PROCESSOR_FIELDS = [
    {
        "field": "Name and contact details of processor and each controller",
        "description": "Processor identity and controller(s) on whose behalf processing occurs.",
        "example": "Processor X processes for Controller Y",
    },
    {
        "field": "Categories of processing",
        "description": "Processing carried out on behalf of the controller.",
        "example": "Hosting, database administration, email delivery",
    },
    {
        "field": "Transfers to third countries",
        "description": "Processor transfers and documented safeguards.",
        "example": "Sub-processor in UK — adequacy + DPA schedule",
    },
    {
        "field": "Technical and organisational measures",
        "description": "Measures required under Article 32 as implemented for the processing.",
        "example": "ISO27001 controls mapped to processing environments",
    },
]


def _article30_excerpt(articles: list[dict]) -> str:
    for art in articles:
        if str(art.get("article_number")) == "30":
            title = str(art.get("title", ""))
            body = str(art.get("text", ""))
            return f"Article 30 GDPR — {title}\n\n{body}".strip()
    return ""


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    excerpt = ""
    if GDPR_ART.exists():
        data = json.loads(GDPR_ART.read_text(encoding="utf-8"))
        excerpt = _article30_excerpt(data)
    else:
        logger.warning("Missing %s — RoPA excerpt will be empty", GDPR_ART)
    payload = {
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
        "controller_record_fields": CONTROLLER_FIELDS,
        "processor_record_fields": PROCESSOR_FIELDS,
        "article_30_excerpt": excerpt,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %s", OUT)


if __name__ == "__main__":
    main()
