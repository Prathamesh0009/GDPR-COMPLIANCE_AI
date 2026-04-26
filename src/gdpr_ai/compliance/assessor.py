"""LLM-backed compliance assessment with citation filtering."""
from __future__ import annotations

import json
import logging
from typing import Any

from gdpr_ai.compliance.schemas import ComplianceAssessment, DataMap, Finding
from gdpr_ai.config import settings
from gdpr_ai.llm.client import LLMResult, complete_text, extract_json_object
from gdpr_ai.models import RetrievedChunk
from gdpr_ai.prompts import render_prompt

logger = logging.getLogger(__name__)


def _chunks_json(chunks: list[RetrievedChunk]) -> str:
    """Serialise chunks for the assessment prompt."""
    payload = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "metadata": c.metadata,
        }
        for c in chunks
    ]
    return json.dumps(payload, ensure_ascii=False)


def _flatten_chunks(article_map: dict[str, list[RetrievedChunk]]) -> list[RetrievedChunk]:
    """Dedupe chunks from mapper output."""
    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for _k, lst in article_map.items():
        for c in lst:
            if c.chunk_id in seen:
                continue
            seen.add(c.chunk_id)
            out.append(c)
    return out


def _article_grounded(article_ref: str, chunks: list[RetrievedChunk]) -> bool:
    """Return True if ``article_ref`` is supported by chunk text or metadata."""
    a = article_ref.strip().lower()
    if not a:
        return False
    for c in chunks:
        if a in c.text.lower():
            return True
        meta = c.metadata
        if a in str(meta.get("article_number", "")).lower():
            return True
        if a in str(meta.get("full_citation", "")).lower():
            return True
    return False


def _filter_findings(
    findings: list[Finding],
    chunks: list[RetrievedChunk],
) -> list[Finding]:
    """Drop relevant_articles strings that are not evidenced by retrieved chunks."""
    fixed: list[Finding] = []
    for f in findings:
        arts = [x for x in f.relevant_articles if _article_grounded(x, chunks)]
        fixed.append(f.model_copy(update={"relevant_articles": arts}))
    return fixed


async def assess_compliance(
    data_map: DataMap,
    article_map: dict[str, list[RetrievedChunk]],
) -> tuple[ComplianceAssessment, LLMResult]:
    """Produce a grounded compliance assessment from retrieved legal chunks."""
    chunks = _flatten_chunks(article_map)
    schema = json.dumps(ComplianceAssessment.model_json_schema(), ensure_ascii=False, indent=2)
    user = render_prompt(
        "compliance_assess",
        schema=schema,
        data_map_json=data_map.model_dump_json(),
        chunks_json=_chunks_json(chunks),
    )
    res = await complete_text(
        model=settings.model_reasoning,
        system="You output only JSON. Obey citation rules in the user prompt.",
        user=user,
        max_tokens=settings.max_tokens,
        temperature=0.0,
    )
    data: dict[str, Any]
    try:
        data = extract_json_object(res.text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Assessment JSON parse failed, retrying once: %s", exc)
        repair_user = (
            user
            + "\n\nYour previous answer was not valid JSON. Reply again with ONLY one JSON object."
        )
        res = await complete_text(
            model=settings.model_reasoning,
            system="You output only JSON.",
            user=repair_user,
            max_tokens=min(settings.max_tokens, 8192),
            temperature=0.0,
        )
        data = extract_json_object(res.text)

    data["data_map"] = data_map.model_dump()
    assessment = ComplianceAssessment.model_validate(data)
    cleaned_findings = _filter_findings(assessment.findings, chunks)
    assessment = assessment.model_copy(update={"findings": cleaned_findings})
    return assessment, res
