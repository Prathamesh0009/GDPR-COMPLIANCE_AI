"""Full-text GDPR article and recital assembly for reasoning context."""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from gdpr_ai.config import settings
from gdpr_ai.paths import resolve_project_path
from gdpr_ai.retrieval.article_map import primary_article_number

logger = logging.getLogger(__name__)

_EURLEX_GDPR_HTML = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679"


def _data_path(path: Path) -> Path:
    return resolve_project_path(path)


@lru_cache(maxsize=4)
def _load_yaml(path_str: str) -> dict[str, Any]:
    p = Path(path_str)
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=2)
def _load_json_articles(path_str: str) -> list[dict[str, Any]]:
    p = Path(path_str)
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def load_article_store() -> dict[str, dict[str, Any]]:
    """Return article number -> {title, full_text, chapter, section}."""
    path = _data_path(settings.gdpr_articles_fulltext_path)
    data = _load_yaml(str(path.resolve()))
    articles_raw = data.get("articles")
    articles = articles_raw if isinstance(articles_raw, dict) else {}
    out: dict[str, dict[str, Any]] = {}
    for k, v in articles.items():
        key = primary_article_number(str(k))
        if isinstance(v, dict):
            out[key] = v
    return out


def load_recital_store() -> dict[str, dict[str, Any]]:
    """Return recital number -> {title, full_text, ...}."""
    path = _data_path(settings.gdpr_recitals_fulltext_path)
    data = _load_yaml(str(path.resolve()))
    rec_raw = data.get("recitals")
    rec = rec_raw if isinstance(rec_raw, dict) else {}
    out: dict[str, dict[str, Any]] = {}
    for k, v in rec.items():
        if isinstance(v, dict):
            out[str(k)] = v
    return out


def _article_from_scrape_json(num: str) -> str | None:
    path = _data_path(settings.gdpr_raw_articles_json_path)
    arts = _load_json_articles(str(path.resolve()))
    for a in arts:
        if str(a.get("article_number", "")).strip() == num:
            return str(a.get("text", "")).strip() or None
    return None


def get_article_text(article_number: str) -> str | None:
    """Return consolidated article body text for GDPR articles."""
    num = primary_article_number(article_number)
    store = load_article_store().get(num)
    if store:
        txt = str(store.get("full_text", "")).strip()
        if txt:
            return txt
    scraped = _article_from_scrape_json(num)
    if scraped:
        return scraped
    return None


def get_article_title(article_number: str) -> str:
    num = primary_article_number(article_number)
    store = load_article_store().get(num)
    if store and store.get("title"):
        return str(store["title"])
    arts = _load_json_articles(str(_data_path(settings.gdpr_raw_articles_json_path).resolve()))
    for a in arts:
        if str(a.get("article_number", "")).strip() == num:
            return str(a.get("title", "")).strip() or f"Article {num}"
    return f"Article {num}"


def get_recital_text(recital_number: str) -> str | None:
    """Return recital text if present in store or scraped recitals JSON."""
    n = str(recital_number).strip()
    store = load_recital_store().get(n)
    if store:
        t = str(store.get("full_text", "")).strip()
        if t:
            return t
    path = _data_path(settings.gdpr_raw_recitals_json_path)
    p = Path(str(path.resolve()))
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, list):
        return None
    for r in raw:
        if str(r.get("number", "")) == n:
            return str(r.get("text", "")).strip() or None
    return None


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def assemble_context(
    articles: set[str],
    *,
    max_tokens: int = 30000,
    priority_order: list[str] | None = None,
) -> str:
    """Build a single block of full article text, optionally honoring priority_order first."""
    ordered: list[str] = []
    if priority_order:
        seen: set[str] = set()
        for a in priority_order:
            n = primary_article_number(a)
            if n not in seen and n in {primary_article_number(x) for x in articles}:
                ordered.append(n)
                seen.add(n)
        for a in sorted({primary_article_number(x) for x in articles}):
            if a not in seen:
                ordered.append(a)
                seen.add(a)
    else:
        ordered = sorted({primary_article_number(x) for x in articles}, key=int)

    parts: list[str] = []
    budget = max_tokens
    for num in ordered:
        title = get_article_title(num)
        body = get_article_text(num)
        if not body:
            logger.debug("No full text for article %s; skipping in assembly", num)
            continue
        block = f"--- Article {num}: {title} ---\n{body.strip()}\n"
        cost = _approx_tokens(block)
        if cost > budget:
            truncated = block[: budget * 4]
            parts.append(truncated + "\n[... truncated ...]\n")
            break
        parts.append(block)
        budget -= cost
    return "\n".join(parts)


def assemble_recitals(recitals: set[str]) -> str:
    """Concatenate recital texts."""
    parts: list[str] = []
    for r in sorted(recitals, key=lambda x: int(re.sub(r"\D", "", x) or 0)):
        txt = get_recital_text(r)
        if txt:
            parts.append(f"--- Recital {r} ---\n{txt.strip()}\n")
    return "\n".join(parts)


def eurlex_source_url() -> str:
    """Canonical EUR-Lex HTML URL for GDPR (CELEX:32016R0679)."""
    return _EURLEX_GDPR_HTML
