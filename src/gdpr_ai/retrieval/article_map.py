"""Layer 1: deterministic topic and keyword to GDPR article mapping."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from gdpr_ai.config import settings
from gdpr_ai.paths import resolve_project_path

logger = logging.getLogger(__name__)

_KEYWORD_TO_TOPICS: dict[str, list[str]] | None = None


def _data_path(path: Path) -> Path:
    return resolve_project_path(path)


@lru_cache(maxsize=2)
def _load_raw_map(path_str: str) -> dict[str, Any]:
    p = Path(path_str)
    if not p.exists():
        return {"topics": {}, "topic_aliases": {}}
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"topics": {}, "topic_aliases": {}}
    data.setdefault("topics", {})
    data.setdefault("topic_aliases", {})
    return data


def load_article_map() -> dict[str, Any]:
    """Load the article map YAML into memory. Cached per resolved file path."""
    path = _data_path(settings.gdpr_article_map_path)
    if not path.exists():
        logger.warning("Article map missing at %s; deterministic layer returns empty sets", path)
        return {"topics": {}, "topic_aliases": {}}
    return _load_raw_map(str(path.resolve()))


def _keyword_index() -> dict[str, list[str]]:
    """Build reverse lookup keyword (lowercase) -> topic keys."""
    global _KEYWORD_TO_TOPICS
    if _KEYWORD_TO_TOPICS is None:
        idx: dict[str, list[str]] = {}
        data = load_article_map()
        for topic_key, spec in data.get("topics", {}).items():
            for kw in spec.get("keywords", []) or []:
                k = str(kw).strip().lower()
                if not k:
                    continue
                idx.setdefault(k, []).append(topic_key)
        _KEYWORD_TO_TOPICS = idx
    return _KEYWORD_TO_TOPICS


def resolve_topic_key(topic_slug: str) -> str | None:
    """Map classifier topic slug to YAML topic key via aliases."""
    data = load_article_map()
    aliases: dict[str, str] = data.get("topic_aliases", {})
    topics: dict[str, Any] = data.get("topics", {})
    t = topic_slug.strip()
    if t in aliases:
        return aliases[t]
    t_underscore = t.replace("-", "_")
    if t_underscore in topics:
        return t_underscore
    if t in topics:
        return t
    return aliases.get(t.replace("_", "-"))


def resolve_articles(
    topics: list[str],
    keywords: list[str],
    *,
    text_blob: str | None = None,
) -> tuple[set[str], set[str], set[str], set[str]]:
    """
    Match topics and keywords against the article map.

    Returns (gdpr_article_refs, recitals, bdsg_sections, ttdsg_sections) as string sets.
    """
    data = load_article_map()
    topic_defs: dict[str, Any] = data.get("topics", {})
    gdpr: set[str] = set()
    recitals: set[str] = set()
    bdsg: set[str] = set()
    ttdsg: set[str] = set()

    seen_topics: set[str] = set()
    for slug in topics:
        key = resolve_topic_key(slug)
        if not key or key not in topic_defs or key in seen_topics:
            continue
        seen_topics.add(key)
        spec = topic_defs[key]
        gdpr.update(str(x) for x in spec.get("gdpr_articles", []) or [])
        recitals.update(str(x) for x in spec.get("gdpr_recitals", []) or [])
        bdsg.update(str(x) for x in spec.get("bdsg_sections", []) or [])
        ttdsg.update(str(x) for x in spec.get("ttdsg_sections", []) or [])

    idx = _keyword_index()
    blob = " ".join(keywords).lower()
    if text_blob:
        blob = f"{blob} {text_blob.lower()}"
    for kw, topic_keys in idx.items():
        if kw in blob:
            for key in topic_keys:
                if key not in topic_defs:
                    continue
                spec = topic_defs[key]
                gdpr.update(str(x) for x in spec.get("gdpr_articles", []) or [])
                recitals.update(str(x) for x in spec.get("gdpr_recitals", []) or [])
                bdsg.update(str(x) for x in spec.get("bdsg_sections", []) or [])
                ttdsg.update(str(x) for x in spec.get("ttdsg_sections", []) or [])

    return gdpr, recitals, bdsg, ttdsg


def get_topic_for_keyword(keyword: str) -> list[str]:
    """Return topic keys whose keyword list contains ``keyword`` (case-insensitive)."""
    k = keyword.strip().lower()
    if not k:
        return []
    return list(dict.fromkeys(_keyword_index().get(k, [])))


def primary_article_number(ref: str) -> str:
    """Normalize an article reference to its leading numeric id for graph lookup."""
    s = ref.strip()
    m = re.match(r"^(\d+)", s)
    return m.group(1) if m else s
