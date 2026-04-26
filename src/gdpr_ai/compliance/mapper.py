"""Map a ``DataMap`` to retrieved legal chunks (GDPR corpus + v2 collections)."""
from __future__ import annotations

import logging

from gdpr_ai.compliance.schemas import DataMap
from gdpr_ai.config import settings
from gdpr_ai.models import ClassifiedTopics, ExtractedEntities, RetrievedChunk
from gdpr_ai.retriever import retrieve, retrieve_multi_collection

logger = logging.getLogger(__name__)


def _dedupe_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Drop duplicate chunk ids while preserving order."""
    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for c in chunks:
        if c.chunk_id in seen:
            continue
        seen.add(c.chunk_id)
        out.append(c)
    return out


def _base_entities_topics(query: str) -> tuple[ExtractedEntities, ClassifiedTopics]:
    """Minimal retrieval context for the main GDPR collection."""
    entities = ExtractedEntities(
        jurisdiction="EU",
        summary=query[:2000],
    )
    topics = ClassifiedTopics(topics=["gdpr"], rationale="compliance mapping")
    return entities, topics


def map_articles(data_map: DataMap) -> dict[str, list[RetrievedChunk]]:
    """For each aspect of the system, retrieve GDPR + auxiliary guidance chunks."""
    article_map: dict[str, list[RetrievedChunk]] = {}
    snapshot = data_map.model_dump_json(ensure_ascii=False)

    for cat in data_map.data_categories:
        q = (
            f"GDPR and EDPB requirements for processing {cat.name} "
            f"(sensitivity {cat.sensitivity.value}, volume {cat.volume.value}) "
            f"for data subjects: {', '.join(cat.subjects)}. Context: {snapshot[:1500]}"
        )
        article_map[f"category:{cat.name}"] = _retrieve_merged(q)

    for purpose in data_map.processing_purposes:
        q = (
            f"Lawful basis, transparency, and compliance for processing purpose "
            f"\"{purpose.purpose}\" involving data categories {purpose.data_categories}. "
            f"Claimed basis: {purpose.legal_basis_claimed or 'unspecified'}."
        )
        article_map[f"purpose:{purpose.purpose}"] = _retrieve_merged(q)

    for flow in data_map.data_flows:
        border = (
            f"cross-border to {flow.destination_country}" if flow.crosses_border else "domestic"
        )
        q = (
            f"Data transfer and security requirements for flow {flow.source} -> "
            f"{flow.destination} ({border}) for categories {flow.data_categories}."
        )
        article_map[f"flow:{flow.source}->{flow.destination}"] = _retrieve_merged(q)

    for tp in data_map.third_parties:
        q = (
            f"Controller and processor obligations for third party {tp.name} "
            f"as {tp.role.value} for {tp.purpose}."
        )
        article_map[f"third_party:{tp.name}"] = _retrieve_merged(q)

    for store in data_map.storage:
        q = (
            f"Security and storage limitation for location {store.location} "
            f"({store.country}), retention {store.retention_period or 'unspecified'}."
        )
        article_map[f"storage:{store.location}"] = _retrieve_merged(q)

    if data_map.has_automated_decision_making or data_map.uses_ai_ml:
        q = (
            "GDPR automated decision-making Article 22, DPIA Article 35, transparency; "
            "EU AI Act deployer obligations for high-risk systems and personal data."
        )
        article_map["automation_and_ai"] = _retrieve_merged(q)

    if data_map.processes_children_data:
        q = "Children's data Article 8 GDPR consent and information society services."
        article_map["children"] = _retrieve_merged(q)

    return article_map


def _retrieve_merged(query: str) -> list[RetrievedChunk]:
    """Combine main GDPR index retrieval with v2 auxiliary collections."""
    entities, topics = _base_entities_topics(query)
    try:
        main = retrieve(query, topics, entities, top_k=max(8, settings.top_k // 2))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Main retrieval failed: %s", exc)
        main = []
    try:
        aux = retrieve_multi_collection(
            query,
            top_k_per_collection=6,
            top_k=12,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Auxiliary retrieval failed: %s", exc)
        aux = []
    merged = _dedupe_chunks(main + aux)
    return merged[: max(settings.top_k, 20)]
