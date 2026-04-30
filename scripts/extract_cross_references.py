"""
Parse GDPR (and optionally BDSG/TTDSG) full text to infer GDPR cross-references.

Writes ``data/gdpr_cross_references_auto.yaml`` and merges into
``data/gdpr_cross_references.yaml`` (union with hand curation, preserves descriptions).

Run: uv run python scripts/extract_cross_references.py
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FULLTEXT = ROOT / "data" / "gdpr_articles_fulltext.yaml"
HAND_PATH = ROOT / "data" / "gdpr_cross_references.yaml"
AUTO_OUT = ROOT / "data" / "gdpr_cross_references_auto.yaml"
RAW_BDSG = ROOT / "data" / "raw" / "bdsg_sections.json"
RAW_TTDSG = ROOT / "data" / "raw" / "ttdsg_sections.json"

logger = logging.getLogger(__name__)

_RANGE_RE = re.compile(r"\bArticles?\s+(\d+)\s+to\s+(\d+)\b", re.IGNORECASE)
_ART_RE = re.compile(r"\bArticle[s]?\s+(\d+)", re.IGNORECASE)


def _extract_gdpr_refs(text: str) -> set[str]:
    """Collect numeric GDPR article ids between 1 and 99 from *text*."""
    refs: set[str] = set()
    for ma, mb in _RANGE_RE.findall(text):
        lo, hi = int(ma), int(mb)
        if lo > hi:
            lo, hi = hi, lo
        for n in range(max(1, lo), min(99, hi) + 1):
            refs.add(str(n))
    for m in _ART_RE.finditer(text):
        n = int(m.group(1))
        if 1 <= n <= 99:
            refs.add(str(n))
    return refs


def _edges_from_yaml(path: Path) -> dict[str, set[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    articles = data.get("articles") if isinstance(data, dict) else None
    if not isinstance(articles, dict):
        return {}
    out: dict[str, set[str]] = defaultdict(set)
    for num, spec in articles.items():
        key = str(num).strip()
        if not key.isdigit():
            continue
        body = ""
        if isinstance(spec, dict):
            body = str(spec.get("full_text", ""))
        refs = _extract_gdpr_refs(body)
        refs.discard(key)
        out[key] = set(refs)
    return dict(out)


def _load_hand(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"cross_references": {}, "bdsg_cross_references": {}, "ttdsg_cross_references": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _law_gdpr_edges(
    rows: list[dict[str, Any]],
    text_key: str,
    id_key: str,
) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        sec = str(row.get(id_key, "")).strip()
        text = str(row.get(text_key, ""))
        if not sec or not text:
            continue
        for r in _extract_gdpr_refs(text):
            out[sec].add(r)
    return dict(out)


def _merge_cross_refs(
    hand: dict[str, Any],
    auto_edges: dict[str, set[str]],
) -> dict[str, Any]:
    cross = dict(hand.get("cross_references") or {})
    for src, tgt in auto_edges.items():
        cur = cross.get(src)
        if isinstance(cur, dict):
            existing = {str(x) for x in (cur.get("references") or [])}
            merged = sorted(existing | tgt, key=int)
            new_block: dict[str, Any] = {"references": merged}
            if cur.get("description"):
                new_block["description"] = cur["description"]
            cross[src] = new_block
        else:
            cross[src] = {"references": sorted(tgt, key=int)}
    return cross


def _merge_law(
    hand_section: dict[str, Any],
    auto_edges: dict[str, set[str]],
    gdpr_key: str,
) -> dict[str, Any]:
    out = dict(hand_section or {})
    for sec, tgts in auto_edges.items():
        cur = out.get(sec)
        if isinstance(cur, dict):
            exist = {str(x) for x in (cur.get(gdpr_key) or [])}
            merged = sorted(exist | tgts, key=int)
            block = dict(cur)
            block[gdpr_key] = merged
            out[sec] = block
        else:
            out[sec] = {gdpr_key: sorted(tgts, key=int)}
    return out


def _stats(edges: dict[str, set[str]]) -> None:
    flat: list[tuple[str, str]] = [(a, b) for a, ts in edges.items() for b in ts]
    logger.info("Total directed edges: %s", len(flat))
    inc: Counter[str] = Counter()
    for _a, ts in edges.items():
        for b in ts:
            inc[b] += 1
    top_out = sorted(edges.items(), key=lambda x: len(x[1]), reverse=True)[:8]
    top_in = inc.most_common(8)
    logger.info("Articles with most outgoing refs: %s", [(k, len(v)) for k, v in top_out])
    logger.info("Articles with most incoming refs: %s", top_in)


def _diff_against_hand(hand_cross: dict[str, Any], auto: dict[str, set[str]]) -> None:
    new_pairs = 0
    for src, tgts in auto.items():
        h = hand_cross.get(src)
        hand_refs: set[str] = set()
        if isinstance(h, dict):
            hand_refs = {str(x) for x in (h.get("references") or [])}
        for t in tgts:
            if t not in hand_refs:
                new_pairs += 1
    logger.info("New (src,tgt) pairs vs hand cross_references: %s", new_pairs)


def _validate_cross_yaml(data: dict[str, Any]) -> None:
    refs_block = data.get("cross_references") or {}
    all_articles = {str(i) for i in range(1, 100)}
    for src, spec in refs_block.items():
        if not isinstance(spec, dict):
            continue
        for ref in spec.get("references") or []:
            base = str(ref).split("(")[0].strip()
            if base not in all_articles:
                logger.warning("Article %s references non-existent Article %s", src, base)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not FULLTEXT.exists():
        raise SystemExit(f"Missing {FULLTEXT}; run export_gdpr_fulltext_yaml.py first.")

    auto_edges = _edges_from_yaml(FULLTEXT)
    _stats(auto_edges)

    ref_items = sorted(auto_edges.items(), key=lambda x: int(x[0]))
    auto_payload = {
        "cross_references": {k: {"references": sorted(v, key=int)} for k, v in ref_items}
    }
    AUTO_OUT.write_text(
        yaml.safe_dump(auto_payload, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    logger.info("Wrote %s", AUTO_OUT)

    hand = _load_hand(HAND_PATH)
    _diff_against_hand(hand.get("cross_references") or {}, auto_edges)

    merged_cross = _merge_cross_refs(hand, auto_edges)
    out_doc = dict(hand)
    out_doc["cross_references"] = dict(
        sorted(merged_cross.items(), key=lambda kv: int(str(kv[0]))),
    )

    if RAW_BDSG.exists():
        bdsg_rows = json.loads(RAW_BDSG.read_text(encoding="utf-8"))
        if isinstance(bdsg_rows, list):
            auto_bdsg = _law_gdpr_edges(
                [r for r in bdsg_rows if isinstance(r, dict)],
                text_key="text_en",
                id_key="section_number",
            )
            out_doc["bdsg_cross_references"] = _merge_law(
                dict(out_doc.get("bdsg_cross_references") or {}),
                auto_bdsg,
                "references_gdpr",
            )

    if RAW_TTDSG.exists():
        tt_rows = json.loads(RAW_TTDSG.read_text(encoding="utf-8"))
        if isinstance(tt_rows, list):
            auto_tt = _law_gdpr_edges(
                [r for r in tt_rows if isinstance(r, dict)],
                text_key="text_en",
                id_key="section_number",
            )
            out_doc["ttdsg_cross_references"] = _merge_law(
                dict(out_doc.get("ttdsg_cross_references") or {}),
                auto_tt,
                "references_gdpr",
            )

    HAND_PATH.write_text(
        yaml.safe_dump(out_doc, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    logger.info("Updated %s", HAND_PATH)
    _validate_cross_yaml(out_doc)


if __name__ == "__main__":
    main()
