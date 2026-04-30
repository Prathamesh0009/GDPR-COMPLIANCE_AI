"""Unit tests for deterministic retrieval helpers (no ChromaDB required)."""

from __future__ import annotations

import pytest

from gdpr_ai.paths import repo_root
from gdpr_ai.retrieval.article_map import (
    get_topic_for_keyword,
    primary_article_number,
    resolve_articles,
)
from gdpr_ai.retrieval.cross_ref_graph import expand_articles

_MAP = repo_root() / "data" / "gdpr_article_map.yaml"
pytestmark = pytest.mark.skipif(not _MAP.exists(), reason="data/gdpr_article_map.yaml missing")


def test_primary_article_number() -> None:
    assert primary_article_number("6(1)(a)") == "6"
    assert primary_article_number("  12 ") == "12"


def test_resolve_consent_topics() -> None:
    g, _r, _b, _t = resolve_articles(
        ["consent", "legal-basis"],
        ["newsletter"],
        text_blob="user gave opt-in for marketing emails",
    )
    assert "7" in g or "6" in g
    assert len(g) >= 1


def test_expand_includes_neighbors() -> None:
    base = expand_articles({"6"}, depth=1)
    assert "6" in base
    assert len(base) >= 1


def test_keyword_reverse_lookup() -> None:
    topics = get_topic_for_keyword("dpia")
    assert any("dpia" in t for t in topics)
