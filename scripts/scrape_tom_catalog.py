#!/usr/bin/env python3
"""Build a curated TOM catalog JSON mapped to GDPR Article 32 (offline)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "tom_catalog.json"

ENTRIES = [
    {
        "category": "access_control",
        "gdpr_article": "Art. 32",
        "description": (
            "Restrict access to personal data on a need-to-know basis using role-based "
            "access control, least privilege, and periodic access reviews."
        ),
        "implementation_examples": [
            "SSO with MFA for administrative interfaces",
            "Separate production credentials from developer laptops",
        ],
        "publisher": "GDPR AI curated (Art. 32 alignment)",
    },
    {
        "category": "encryption",
        "gdpr_article": "Art. 32",
        "description": (
            "Encrypt personal data at rest and in transit where appropriate to the risk, "
            "using modern algorithms and key management."
        ),
        "implementation_examples": [
            "TLS 1.2+ for all public endpoints",
            "Database volume encryption + application-layer encryption for highly sensitive fields",
        ],
        "publisher": "GDPR AI curated (Art. 32 alignment)",
    },
    {
        "category": "pseudonymisation",
        "gdpr_article": "Art. 32",
        "description": (
            "Separate identifying data from processing datasets where feasible to reduce "
            "risk (Article 32(1)(a)); document key management and re-identification controls."
        ),
        "implementation_examples": [
            "Tokenised user identifiers in analytics pipelines",
            "Salted hashes for duplicate detection where direct identifiers are unnecessary",
        ],
        "publisher": "GDPR AI curated (Art. 32 alignment)",
    },
    {
        "category": "availability_and_resilience",
        "gdpr_article": "Art. 32",
        "description": (
            "Ensure ongoing confidentiality, integrity, availability and resilience of "
            "processing systems — backups, redundancy, disaster recovery testing."
        ),
        "implementation_examples": [
            "Geo-redundant backups with encrypted snapshots",
            "RTO/RPO targets documented and tested annually",
        ],
        "publisher": "GDPR AI curated (Art. 32 alignment)",
    },
    {
        "category": "logging_and_monitoring",
        "gdpr_article": "Art. 32",
        "description": (
            "Detect security events affecting personal data; retain audit logs with "
            "appropriate access controls and retention aligned to purpose."
        ),
        "implementation_examples": [
            "Centralised logs with tamper-evident storage",
            "Alerting on privileged actions and authentication failures",
        ],
        "publisher": "GDPR AI curated (Art. 32 alignment)",
    },
    {
        "category": "vendor_and_subprocessor_management",
        "gdpr_article": "Art. 28",
        "description": (
            "Written contracts with processors, due diligence, and documented instructions; "
            "sub-processor change processes."
        ),
        "implementation_examples": [
            "DPA schedules with SCCs where applicable",
            "Annual security review questionnaire for critical vendors",
        ],
        "publisher": "GDPR AI curated (Art. 28 alignment)",
    },
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
        "entries": ENTRIES,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote %s", OUT)


if __name__ == "__main__":
    main()
