"""Repository root resolution for data files and prompts."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the project root (parent of ``src``)."""
    return Path(__file__).resolve().parents[2]


def resolve_project_path(candidate: Path) -> Path:
    """Resolve a path relative to CWD when it exists, else relative to repo root."""
    if candidate.is_absolute():
        return candidate
    cwd_path = Path.cwd() / candidate
    if cwd_path.exists():
        return cwd_path
    return repo_root() / candidate
