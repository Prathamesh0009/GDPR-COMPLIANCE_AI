"""Layer 2: cross-reference graph expansion for GDPR articles."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from gdpr_ai.config import settings
from gdpr_ai.paths import resolve_project_path
from gdpr_ai.retrieval.article_map import primary_article_number


def _data_path(path: Path) -> Path:
    return resolve_project_path(path)


@lru_cache(maxsize=2)
def _load_cross_ref(path_str: str) -> dict[str, Any]:
    p = Path(path_str)
    if not p.exists():
        return {"cross_references": {}, "bdsg_cross_references": {}, "ttdsg_cross_references": {}}
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"cross_references": {}, "bdsg_cross_references": {}, "ttdsg_cross_references": {}}
    data.setdefault("cross_references", {})
    data.setdefault("bdsg_cross_references", {})
    data.setdefault("ttdsg_cross_references", {})
    return data


def load_cross_ref_graph() -> dict[str, set[str]]:
    """Return GDPR article -> referenced GDPR articles (direct edges only)."""
    path = _data_path(settings.gdpr_cross_references_path)
    raw = _load_cross_ref(str(path.resolve()))
    out: dict[str, set[str]] = {}
    for art, spec in (raw.get("cross_references") or {}).items():
        key = primary_article_number(str(art))
        refs: set[str] = set()
        if isinstance(spec, dict):
            for r in spec.get("references", []) or []:
                refs.add(primary_article_number(str(r)))
        out[key] = refs
    return out


def bdsg_to_gdpr_refs() -> dict[str, set[str]]:
    """BDSG section -> GDPR article numbers."""
    path = _data_path(settings.gdpr_cross_references_path)
    raw = _load_cross_ref(str(path.resolve()))
    out: dict[str, set[str]] = {}
    for sec, spec in (raw.get("bdsg_cross_references") or {}).items():
        refs: set[str] = set()
        if isinstance(spec, dict):
            for r in spec.get("references_gdpr", []) or []:
                refs.add(primary_article_number(str(r)))
        out[str(sec)] = refs
    return out


def ttdsg_to_gdpr_refs() -> dict[str, set[str]]:
    """TTDSG section -> GDPR article numbers."""
    path = _data_path(settings.gdpr_cross_references_path)
    raw = _load_cross_ref(str(path.resolve()))
    out: dict[str, set[str]] = {}
    for sec, spec in (raw.get("ttdsg_cross_references") or {}).items():
        refs: set[str] = set()
        if isinstance(spec, dict):
            for r in spec.get("references_gdpr", []) or []:
                refs.add(primary_article_number(str(r)))
        out[str(sec)] = refs
    return out


def expand_articles(articles: set[str], depth: int = 1) -> set[str]:
    """Expand by following GDPR cross-reference edges ``depth`` times."""
    graph = load_cross_ref_graph()
    out = {primary_article_number(a) for a in articles}
    frontier = set(out)
    for _ in range(max(0, depth)):
        nxt: set[str] = set()
        for art in frontier:
            nxt.update(graph.get(art, set()))
        frontier = nxt - out
        out.update(nxt)
        if not frontier:
            break
    return out


def get_references_for(article: str) -> set[str]:
    """Articles that ``article`` references (one hop)."""
    g = load_cross_ref_graph()
    return set(g.get(primary_article_number(article), set()))


def get_referenced_by(article: str) -> set[str]:
    """Articles that reference ``article`` (reverse lookup)."""
    target = primary_article_number(article)
    out: set[str] = set()
    for src, refs in load_cross_ref_graph().items():
        if target in refs:
            out.add(src)
    return out
