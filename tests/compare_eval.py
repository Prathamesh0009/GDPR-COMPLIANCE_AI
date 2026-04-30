#!/usr/bin/env python3
"""Compare two JSON evaluation outputs (article lists / simple metrics)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _articles(obj: dict[str, Any]) -> set[str]:
    arts = obj.get("expected_articles") or obj.get("articles") or []
    if isinstance(arts, str):
        return {arts}
    return {str(x) for x in arts if x}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    args = p.parse_args()
    a = json.loads(args.before.read_text(encoding="utf-8"))
    b = json.loads(args.after.read_text(encoding="utf-8"))
    print("before keys:", sorted(a.keys()))
    print("after keys:", sorted(b.keys()))
    if "per_scenario" in a and "per_scenario" in b:
        keys = sorted(set(a["per_scenario"]) | set(b["per_scenario"]))
        for k in keys[:50]:
            pa = a["per_scenario"].get(k, {})
            pb = b["per_scenario"].get(k, {})
            print(k, "articles before", _articles(pa), "after", _articles(pb))


if __name__ == "__main__":
    main()
