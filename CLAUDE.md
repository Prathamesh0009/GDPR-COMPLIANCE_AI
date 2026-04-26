# CLAUDE.md — Project conventions for GDPR AI

## Project overview

GDPR AI is a RAG-powered tool that identifies violated GDPR articles from
natural-language scenarios. German-market focus (GDPR + BDSG + TTDSG).
English-only runtime. Closed personal project for v1, may open up later.

See README.md for full context.

## Language & environment

- Python 3.11 (pinned via uv)
- Dependency manager: uv (never pip, never poetry)
- Package layout: src/gdpr_ai/ (src layout)
- Environment vars via pydantic-settings, loaded from .env

## Code style

- Type hints required for all function signatures and class attributes
- Pydantic v2 models for all structured data (inputs, outputs, chunks)
- Docstrings for all public functions (one-line minimum, longer if complex)
- Line length: 100 chars (ruff config in pyproject.toml)
- Prefer explicit over clever — this is a legal reasoning tool, clarity matters
- No bare except — always except SomeSpecificException
- Logging via Python stdlib logging, never print() outside CLI scripts

## Project structure

- scripts/ — one-off build scripts (scraping, chunking, indexing). Not part of the package.
- src/gdpr_ai/ — the actual package
  - config.py — settings loaded from .env (includes v2 Chroma collection names, `SQLITE_PATH`)
  - models.py — Pydantic models for violation pipeline I/O
  - pipeline.py — v1 orchestration (extract → classify → retrieve → reason → validate)
  - retriever.py — hybrid retrieval; multi-collection helpers for v2
  - knowledge/ — embeddings, chunking, BM25, v2 auxiliary chunk builders
  - compliance/ — v2 intake, article mapping, assessment, document generation
  - api/ — FastAPI app and `/api/v1` routes (analyze, documents, projects)
  - db/ — application SQLite schema and `AppRepository` (projects, analyses, documents)
  - llm/ — provider SDK wrapper
  - prompts.py — loads versioned `.txt` prompts from the repo `prompts/` tree
  - templates/ — Jinja2 markdown templates for v2 documents
  - cli.py — Typer entry point (`analyze`, `assess`, `serve`, stats/history, …)
  - logger.py / logging_schema.py — query log (includes `analysis_mode`: violation vs compliance)
- gold/ — `test_scenarios.yaml` (unified v1 + v2 scenarios), `baseline.json` (eval regression targets)
- tests/ — unit + integration + `run_eval.py` (unified eval), `eval_models.py`, `eval_scoring.py`, `test_eval_harness.py`
- data/ — raw scraped data, processed chunks, Chroma DB, optional `app.db` (gitignored)
- docs/ — ADRs and design notes

## Git workflow

- main = stable, only merged from develop at release points
- develop = default working branch
- feature/* branches off develop, merge back to develop
- NEVER push directly to main
- Always create feature/<short-name> before touching code for a new feature
- Commit messages: Conventional Commits
  - feat: new feature
  - fix: bug fix
  - docs: documentation only
  - chore: tooling, configs, scaffolding
  - refactor: code restructure, no behavior change
  - test: tests only
- One logical change per commit. Prefer small commits.

## Dependencies

- Never add a new dependency without justifying why and checking license
- Update pyproject.toml, run `uv sync` after
- Commit both pyproject.toml and uv.lock together

Runtime libraries beyond the v1 stack include **jinja2** (document rendering), **fastapi** and **uvicorn** (local API), and **aiosqlite** (application DB).

## Knowledge base sources

All scraping targets documented in README's "Knowledge Sources" section.
German-origin text (BDSG, TTDSG, DSK) is translated to English ONCE at
index build time via the configured translation model. Runtime is English-only.

Sources and licenses:
- GDPR (EUR-Lex) — public EU law
- BDSG, TTDSG (gesetze-im-internet.de) — public German law
- EDPB Guidelines — EU reuse policy
- DSK, BfDI, BayLDA, LfDI BW — public German guidance
- GDPRhub — CC BY-NC-SA 4.0 (noncommercial, attribution, share-alike)
- Enforcement Tracker — free with attribution

Attribution for every chunk MUST be preserved in metadata (source, URL, license).

## Testing

- Unit tests for parsers, chunkers, validators
- Integration tests for pipeline stages (mocked LLM responses)
- Gold scenarios: `gold/test_scenarios.yaml` — `mode: violation_analysis` (SC-V-*) and `compliance_assessment` (SC-C-*)
- `tests/run_eval.py` — unified harness: article recall/precision, law recall (v1), finding coverage/accuracy and document markers (v2); `--dry-run`, `--check-baseline`, `--replay`
- Every prompt/retrieval change should be measured on the full gold set or the relevant mode slice

## What to NOT do

- Do not push to main directly
- Do not add new dependencies without asking
- Do not call the Anthropic API during scraping or chunking scripts
  (those must run offline, no credits used)
- Do not commit data/ contents — too large, regeneratable
- Do not commit .env — contains the API key
- Do not use print() in library code — use logging
- Do not skip type hints
- Do not write long Python scripts without breaking into functions
- Do not skip attribution/metadata on scraped chunks

## When unsure

Ask clarifying questions before generating code. Better to pause and clarify
than to generate 200 lines that go in the wrong direction.
