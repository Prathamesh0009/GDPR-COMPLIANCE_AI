"""
End-to-end exercise of deterministic retrieval (Layers 1–3).

Run: uv run python scripts/test_deterministic_pipeline.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from gdpr_ai.models import ClassifiedTopics, ExtractedEntities, RetrievedChunk
from gdpr_ai.retrieval.article_map import primary_article_number, resolve_articles
from gdpr_ai.retrieval.deterministic_retriever import retrieve_deterministic

logger = logging.getLogger(__name__)


def _norm_gdpr(expected: set[str]) -> set[str]:
    return {primary_article_number(x) for x in expected}


def _empty_semantic(
    _query: str,
    _topics: ClassifiedTopics,
    _entities: ExtractedEntities,
    *,
    top_k: int = 10,
) -> list[RetrievedChunk]:
    return []


@dataclass(frozen=True)
class _Scenario:
    name: str
    query: str
    topics: list[str]
    entities: ExtractedEntities
    expected_gdpr: set[str]
    expected_bdsg: set[str]


def _precision_recall(got: set[str], expected: set[str]) -> tuple[float, float]:
    if not expected:
        return (1.0, 1.0)
    tp = len(got & expected)
    prec = tp / len(got) if got else 0.0
    rec = tp / len(expected)
    return (prec, rec)


def _run_scenarios() -> None:
    scenarios: list[_Scenario] = [
        _Scenario(
            name="simple_marketing_consent",
            query="A company sends marketing emails without obtaining consent",
            topics=["consent", "direct-marketing", "legal-basis"],
            entities=ExtractedEntities(
                processing_activities=["direct marketing", "email"],
                legal_bases_mentioned=["consent"],
            ),
            expected_gdpr=_norm_gdpr({"6(1)(a)", "7", "21(2)", "21(3)"}),
            expected_bdsg=set(),
        ),
        _Scenario(
            name="employment_transfer_us",
            query=(
                "An employer monitors employee emails and shares the data "
                "with a US-based cloud provider"
            ),
            topics=["employment", "transfers", "controller-processor", "security-of-processing"],
            entities=ExtractedEntities(
                processing_activities=["email monitoring", "cloud hosting"],
                jurisdiction="Germany",
            ),
            expected_gdpr=_norm_gdpr(
                {"6", "9", "26", "28", "32", "44", "45", "46", "47", "48", "49", "88"},
            ),
            expected_bdsg={"26"},
        ),
        _Scenario(
            name="children_genetics_research_transfer",
            query=(
                "A hospital uses AI to process children's genetic data for research "
                "and shares results with universities in India and Brazil"
            ),
            topics=[
                "children",
                "special-categories",
                "research",
                "transfers",
                "dpia",
                "security-of-processing",
            ],
            entities=ExtractedEntities(
                data_types=["genetic data", "children data"],
                special_categories_present=True,
                processing_activities=["research", "international sharing"],
            ),
            expected_gdpr=_norm_gdpr(
                {"5", "6", "8", "9", "22", "25", "30", "32", "35", "44", "45", "46", "89"},
            ),
            expected_bdsg=set(),
        ),
        _Scenario(
            name="certification_bodies",
            query="What are the requirements for certification bodies under GDPR?",
            topics=["gdpr"],
            entities=ExtractedEntities(
                summary="certification bodies accreditation monitoring GDPR",
            ),
            expected_gdpr=_norm_gdpr({"42", "43"}),
            expected_bdsg=set(),
        ),
        _Scenario(
            name="dpo_bdsg_small_employer",
            query=(
                "Does a company need a DPO under BDSG if it has 15 employees "
                "processing personal data in Germany?"
            ),
            topics=["dpo", "employment", "germany"],
            entities=ExtractedEntities(
                actors=["company"],
                processing_activities=["processing personal data"],
                jurisdiction="Germany",
            ),
            expected_gdpr=_norm_gdpr({"37", "38", "39"}),
            expected_bdsg={"38"},
        ),
    ]

    prec_sum, rec_sum, n = 0.0, 0.0, 0
    for sc in scenarios:
        topics = ClassifiedTopics(topics=sc.topics)
        _gdpr_m, _rec, bdsg_m, _tt = resolve_articles(
            sc.topics,
            [],
            text_blob=f"{sc.query} {sc.entities.summary}",
        )
        res = retrieve_deterministic(
            sc.query,
            topics,
            sc.entities,
            semantic_retrieve_fn=_empty_semantic,
            use_semantic_fallback=False,
            graph_depth=2,
        )
        got_g = {primary_article_number(a) for a in res.all_articles}
        layer1 = {primary_article_number(a) for a in res.articles_from_map}
        layer2 = {primary_article_number(a) for a in res.articles_from_graph}
        layer3 = {primary_article_number(a) for a in res.articles_from_semantic}

        logger.info("=== %s ===", sc.name)
        logger.info("Layer 1 (map): %s", sorted(layer1, key=int))
        logger.info("Layer 2 (graph): %s", sorted(layer2, key=int))
        logger.info("Layer 3 (semantic): %s", sorted(layer3, key=int))
        logger.info("Merged articles: %s", sorted(got_g, key=int))
        logger.info("Mapped BDSG (resolve_articles): %s", sorted(bdsg_m))
        preview = (res.full_text_context or "").replace("\n", " ")[:200]
        logger.info("Context preview: %s…", preview)
        logger.info("Metadata: %s", res.retrieval_metadata)

        p, r = _precision_recall(got_g, sc.expected_gdpr)
        prec_sum += p
        rec_sum += r
        n += 1
        logger.info(
            "GDPR precision %.3f recall %.3f (expected %s)",
            p,
            r,
            sorted(sc.expected_gdpr, key=int),
        )
        if sc.expected_bdsg:
            ok_b = sc.expected_bdsg <= bdsg_m
            logger.info(
                "BDSG expected %s — resolve contains all: %s",
                sorted(sc.expected_bdsg),
                ok_b,
            )

    logger.info(
        "Mean GDPR precision %.3f | mean recall %.3f",
        prec_sum / max(1, n),
        rec_sum / max(1, n),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _run_scenarios()


if __name__ == "__main__":
    main()
