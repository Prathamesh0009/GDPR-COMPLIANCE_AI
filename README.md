# GDPR AI

A RAG-powered, AI-native system for identifying GDPR article violations from real-world scenarios, built with a German-market focus.

GDPR AI is designed as a specialized compliance reasoning tool that demonstrates how modern AI systems can outperform generic chatbots by combining domain-specific knowledge bases, hybrid retrieval, and strict grounding. The system focuses on building an accurate, fast, low-cost violation-detection engine rather than a generic privacy chatbot.

## 🎯 Project Overview

GDPR AI addresses the common problem of GDPR interpretation for real-world scenarios in the European and particularly the German market. Founders, developers, DPOs, students, and compliance-curious engineers face difficulties with:

- Navigating 99 articles and 173 recitals of GDPR plus national add-ons (BDSG, TTDSG)
- Distinguishing overlapping articles (e.g. security breach scenarios that touch Art. 5, 32, 33, 34 simultaneously)
- Identifying German-specific overlays like BDSG §26 for employment contexts
- Getting accurate sub-clause citations (e.g. Art. 6(1)(a) vs just "Article 6")
- Avoiding article-number hallucinations common in generic LLMs
- Anchoring violations to real enforcement decisions and fine precedents

GDPR AI solves this by providing:

- ✅ Scenario-based violation analysis via natural-language input
- ✅ Strictly grounded article citations (no hallucinations)
- ✅ German-market specialization (GDPR + BDSG + TTDSG)
- ✅ Enforcement-case anchoring (GDPRhub + enforcementtracker)
- ✅ Low-cost operation (<€5/month at personal usage levels)
- ✅ Extensibility for document analysis, multi-turn reasoning, and UI layers

## 🌐 Language Policy

GDPR AI is an **English-only system** from the user's perspective:

- All CLI input, prompts, and output are in English
- Structured reports, article summaries, and explanations are generated in English
- All knowledge base content is stored and retrieved in English

German-origin legal sources (BDSG, TTDSG, DSK guidance) are **translated to English once during the knowledge base build**, then indexed and queried entirely in English. This preserves the German-market specialization without introducing bilingual complexity into the runtime pipeline. Multilingual UI and retrieval are explicitly out of scope for v1 and deferred to a future version.

## 🏗️ Architecture

GDPR AI follows a four-stage retrieval-augmented generation pipeline with clear separation of concerns:

```
User Scenario (English)
    ↓
[1. Extract]  Claude Haiku — pull entities (data subject, data type, purpose, basis, jurisdiction)
    ↓
[2. Classify] Claude Haiku — map to GDPR topic taxonomy → retrieval scope filter
    ↓
[3. Retrieve] ChromaDB + BM25 hybrid search over knowledge base → top-15 chunks
    ↓
[4. Reason]   Claude Sonnet — produce structured report grounded ONLY in retrieved chunks
    ↓
[Validate]    Hallucination guard — every cited article must exist in retrieved set
    ↓
Structured Report (English)
```

### Key Components

- **Extract Stage** — Lightweight entity extraction from free-text scenarios using Claude Haiku
- **Classify Stage** — Topic taxonomy mapping (legal basis, consent, rights, security, transfers, employment, etc.) to scope retrieval
- **Retrieve Stage** — Hybrid dense (embeddings) + sparse (BM25) search over pre-indexed legal corpus with metadata filtering
- **Reason Stage** — Claude Sonnet generates structured output with strict grounding on retrieved chunks
- **Validation Layer** — Regex + parser rejects hallucinated article numbers, enforces JSON schema, retries on failure
- **Knowledge Base** — Pre-indexed ChromaDB with GDPR and English translations of BDSG, TTDSG, DSK guidance, plus EDPB guidelines and enforcement decisions
- **Translation Stage (indexing-time only)** — One-time machine translation of German source documents via Claude Haiku during the knowledge base build
- **CLI Interface** — Command-line entry point for v1; API + web UI planned for v2
- **Evaluation Harness** — Gold test set with article-level precision/recall scoring for every pipeline change

## 🛠️ Technology Stack

### Core

- **Python 3.11+** with FastAPI (web layer, when v2 UI arrives)
- **Typer** for CLI entry points
- **Pydantic v2** for request/response models and settings
- **Rich** for terminal formatting

### AI & Retrieval

- **Anthropic Claude API** — Haiku (fast/cheap) for extract + classify + one-time translation, Sonnet (smart) for reasoning
- **ChromaDB** — embedded vector database (no server required for v1)
- **BAAI/bge-m3** via `sentence-transformers` — strong semantic embeddings for legal English
- **rank-bm25** — sparse keyword retrieval for hybrid search
- **(Future) bge-reranker-v2-m3** — cross-encoder re-ranking for v2

### Data & Scraping

- **httpx** — async HTTP client for scraping
- **BeautifulSoup4 + lxml** — HTML parsing for EUR-Lex, gesetze-im-internet, GDPRhub
- **SQLite** — query logs, feedback, evaluation results

### Dev Tooling

- **uv** — fast Python package manager and virtualenv manager
- **Ruff** — linting and formatting
- **mypy** — type checking
- **pytest** + **pytest-asyncio** — testing framework

### Infrastructure (v1 → v2 progression)

- **v1**: Runs fully local, no servers required
- **v2**: Docker for containerization, Hetzner VPS (~€5/mo) or AWS Fargate for hosting, Cloudflare for edge delivery
- **Later**: GitHub Actions for CI/CD, structured logging, observability

## 📚 Documentation

This project includes comprehensive documentation covering the entire design, build, and evaluation process:

### Phase 0: Overview

- **Problem Statement** — Why generic LLMs fail at precise GDPR reasoning and what gap GDPR AI fills
- **Why GDPR AI** — Design motivation, user personas, unique value proposition vs ChatGPT / Claude / Copilot
- **Target Users** — Closed scope (project owner) for v1, expandable to SMEs, DPOs, developers, and legal researchers
- **Scope Decisions** — English-only UI, text-only input for v1, no PDF/URL analysis until v2

### Phase 1: Requirements

- **Functional Requirements** — English scenario input, article identification, scenario-specific explanations, structured report output
- **Non-Functional Requirements** — <5s latency per query, <€0.05 per query cost, zero hallucinated article numbers, reproducible evaluation results
- **Constraints & Assumptions** — English-only runtime, German sources translated once during indexing, no legal advice (informational only), noncommercial use only until commercial licensing is secured for CC BY-NC-SA sources
- **Out of Scope (v1)** — Document upload, website scanning, multi-turn conversations, multilingual UI or retrieval

### Phase 2: Architecture

- **High-Level Architecture** — Four-stage pipeline with retrieval grounding
- **Technical Stack Mapping** — Rationale for each technology choice (Claude vs other LLMs, ChromaDB vs Pinecone, bge-m3 vs OpenAI embeddings)
- **Data & Knowledge Model Design** — Chunking strategy, metadata schema, topic taxonomy
- **Translation Strategy** — One-time Claude Haiku translation of German sources during indexing; quality spot-check against original for key legal terms
- **Prompt Design** — Versioned prompts stored as text files, ADR-tracked changes
- **Retrieval Strategy** — Hybrid dense + sparse, metadata filtering, top-K tuning
- **Validation & Grounding** — Hallucination guards, citation verification, retry logic
- **Security & Privacy** — No user data storage by default, opt-in logging, API key security

### Phase 3: Execution & Build Strategy

- **Knowledge Base Construction** — Scraping scripts for EUR-Lex, gesetze-im-internet, GDPRhub, enforcementtracker
- **Translation Pipeline** — One-time build step translating German sources to English before chunking
- **Chunking & Embedding Pipeline** — One-time build process, refresh cadence, delta updates
- **Pipeline Implementation** — Extract, classify, retrieve, reason, validate modules
- **CLI Entry Point** — Typer-based commands, Rich-formatted output
- **Testing Strategy** — Gold set evaluation, unit tests for parsers, integration tests for pipeline
- **Evaluation Harness** — Precision/recall per article, latency tracking, cost tracking
- **Feedback Loop** — Thumbs up/down capture, weak-chunk identification, prompt iteration workflow
- **Logging & Observability** — SQLite-backed query log, structured logs, performance metrics

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (managed via `uv`)
- **uv** package manager
- **Anthropic API key** (console.anthropic.com)
- **Git**
- **~1GB free disk space** (for embedding models + knowledge base)

### Environment Variables

Copy `.env.example` to `.env` and set your values:

```bash
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL_FAST=claude-haiku-4-5-20251001
CLAUDE_MODEL_SMART=claude-sonnet-4-6
CHROMA_PATH=./data/chroma
SQLITE_PATH=./data/gdpr_ai.db
EMBEDDING_MODEL=BAAI/bge-m3
LOG_LEVEL=INFO
```

### Installation

```bash
# Clone the repository
git clone git@github.com:prathameshpatil/gdpr-ai.git
cd gdpr-ai

# Install Python 3.11 via uv if needed
uv python install 3.11
uv python pin 3.11

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# edit .env — add ANTHROPIC_API_KEY

# Smoke test
uv run gdpr-check version
```

### Building the Knowledge Base (one-time, ~1 hour)

```bash
# Scrape raw sources (includes German originals)
uv run python scripts/scrape_gdpr.py
uv run python scripts/scrape_bdsg.py
uv run python scripts/scrape_ttdsg.py
uv run python scripts/scrape_gdprhub.py

# One-time translation of German sources to English
uv run python scripts/translate_german_sources.py

# Chunk, embed, and build the ChromaDB index
uv run python scripts/chunk_and_embed.py
uv run python scripts/build_index.py
```

### Running Queries

```bash
uv run gdpr-check "A German hospital accidentally emails patient test results to the wrong patient."
```

## 🌿 Branching & Development Workflow

We use a simple branch model to keep `main` stable and integrate work in one place:

- **main** — Stable branch. Only updated by merging from `develop` when a milestone is complete (e.g. a phase or release).
- **develop** — Default working branch. Day-to-day development and feature integration happen here.
- **Feature branches** — Create from `develop` (e.g. `feature/scrape-gdprhub`). When the feature is done, merge into `develop` only (not into `main`).

**Flow**: `feature/*` → `develop` → (when a set of code is complete) → `main`

This setup keeps `main` shippable while all new work is integrated and tested on `develop`.

## 🎯 Key Features

### MVP Features (v1)

- ✅ Free-text English scenario input via CLI
- ✅ Entity extraction (data subject, data type, purpose, legal basis, jurisdiction)
- ✅ Topic classification against GDPR taxonomy
- ✅ Hybrid retrieval (dense embeddings + BM25) over English knowledge base
- ✅ German legal sources (BDSG, TTDSG, DSK) translated to English once during indexing
- ✅ Strict grounding — no article number can be cited unless retrieved
- ✅ Structured English report output: article number + short definition + scenario-specific explanation
- ✅ Enforcement-case anchoring (GDPRhub + enforcementtracker references)
- ✅ Gold-set evaluation harness with precision/recall scoring
- ✅ Query logging and cost tracking via SQLite
- ✅ German-specific overlays (BDSG §26 for employment, TTDSG for tracking) available in English

### Future Enhancements (v2+)

- 🔜 Web UI (Next.js frontend) with scenario history and exportable PDF reports
- 🔜 FastAPI HTTP layer for programmatic access
- 🔜 Multi-turn reasoning with clarifying questions when scenario is ambiguous
- 🔜 Agentic retrieval (ReAct-style) — LLM decides what to search next based on gaps
- 🔜 Cross-encoder re-ranking for sharper top-K results
- 🔜 Document upload (privacy policies, DPAs) with completeness checks against Art. 13/14
- 🔜 Website / URL analysis with cookie and tracking detection
- 🔜 Multilingual UI and retrieval (German first, then French, Italian, Spanish)
- 🔜 Knowledge graph layer (articles → cases → fines → related articles)
- 🔜 Automated weekly refresh of GDPRhub enforcement decisions
- 🔜 Feedback-driven prompt optimization

## 🔒 Security & Privacy

GDPR AI itself handles sensitive compliance queries, so privacy-by-design is a first-class concern:

- **Local-first**: v1 runs entirely on your machine. No user data leaves the host except LLM calls to Anthropic.
- **No telemetry**: No usage analytics, no third-party tracking, no external logging in v1.
- **Anthropic API data policy**: LLM calls are subject to Anthropic's data retention terms. Review them before sharing sensitive scenarios.
- **SQLite logs are local**: Query logs are stored on-disk and never transmitted.
- **API key security**: Keys live in `.env` (gitignored), never committed, never logged.
- **No PII collection**: The CLI does not ask for user identity, email, or any personal info.
- **Input sanitization**: Scenarios are treated as untrusted input and sanitized before reaching prompts.

## 🧪 Testing & Evaluation

The project follows an evaluation-first development strategy:

- **Gold Test Set** — 30+ hand-curated English scenarios with expected article citations, committed to the repo. Grows over time.
- **Unit Tests** — Parsers, chunkers, validators, translation verifier, prompt formatters
- **Integration Tests** — End-to-end pipeline runs against mocked Claude responses
- **Evaluation Harness** — Runs pipeline against gold set, reports article-level precision/recall, latency, cost per query
- **Regression Gate** — Every prompt or retrieval change must not drop precision/recall below the last baseline
- **Hallucination Tests** — Adversarial scenarios designed to trigger article-number hallucinations; the validator must catch them
- **Translation Quality Check** — Spot-check sampled translated chunks against the original German to verify legal term accuracy

### Running Evaluations

```bash
uv run pytest tests/                    # unit + integration
uv run python tests/run_eval.py         # gold-set precision/recall
```

## 📊 Observability

Even in v1 (local CLI), observability is baked in:

- **Structured query logs** — Every query logged to SQLite with inputs, retrieved chunks, final output, latency, and token costs
- **Cost tracking** — Per-query cost computed from Claude token usage, aggregated daily
- **Performance metrics** — Latency breakdown per pipeline stage (extract / classify / retrieve / reason)
- **Feedback capture** — Thumbs up/down on outputs stored alongside query logs
- **Weak-chunk analysis** — Identifies which knowledge chunks frequently fail to support correct answers

Observability in v2 will extend to distributed tracing (OpenTelemetry), CloudWatch dashboards (if AWS-hosted), and alerting on evaluation regressions.

## 📖 Knowledge Sources

The knowledge base is built from authoritative legal and regulatory sources, with a German-market priority. German-language sources are translated to English once during the indexing build, and the runtime knowledge base is entirely English.

### Primary Legal Text

| Source | Coverage | Original Language | In KB | License | Publisher |
|--------|----------|-------------------|-------|---------|-----------|
| GDPR (Regulation (EU) 2016/679) | 99 articles + 173 recitals | EN (official) | EN | Public domain (EU law) | European Union — via EUR-Lex |
| BDSG (Bundesdatenschutzgesetz) | German federal data protection law | DE | EN (translated at indexing) | Public domain (German federal law) | Federal Ministry of Justice, Germany — via gesetze-im-internet.de |
| TTDSG / TDDDG | German telemedia data protection | DE | EN (translated at indexing) | Public domain (German federal law) | Federal Ministry of Justice, Germany — via gesetze-im-internet.de |

### Regulatory Guidance

| Source | Publisher | License / Terms | Notes |
|--------|-----------|-----------------|-------|
| EDPB Guidelines (~30) | European Data Protection Board | EU reuse policy (free reuse with attribution) | English originals; no translation needed |
| DSK Kurzpapiere (~20) | Datenschutzkonferenz (conference of German DPAs) | Public German guidance (attribution expected) | Translated to English during indexing |
| BfDI Guidance | Bundesbeauftragte für den Datenschutz und die Informationsfreiheit (German federal DPA) | Public German guidance (attribution expected) | Translated to English during indexing |
| BayLDA Guidance | Bayerisches Landesamt für Datenschutzaufsicht (Bavarian state DPA) | Public German guidance (attribution expected) | Translated to English during indexing |
| LfDI BW Guidance | Landesbeauftragter für den Datenschutz und die Informationsfreiheit Baden-Württemberg | Public German guidance (attribution expected) | Translated to English during indexing |

### Enforcement Decisions

| Source | Publisher | License / Terms | Notes |
|--------|-----------|-----------------|-------|
| GDPRhub.eu | noyb — European Center for Digital Rights | **CC BY-NC-SA 4.0** | Case summaries in English; noncommercial use only; derivatives must share alike with attribution |
| GDPR Enforcement Tracker | CMS Hasche Sigle Partnerschaft von Rechtsanwälten und Steuerberatern mbB | Free public resource with terms of use (attribution required; no bulk extraction/redistribution without permission) | Structured fine database |

**Landmark cases included by default** (case summaries adapted from GDPRhub under CC BY-NC-SA 4.0):

- Deutsche Wohnen — €14.5M (Art. 5, 25)
- 1&1 Telecom — €9.5M (Art. 32)
- H&M Nürnberg — €35.3M (Art. 5, 6 — employee surveillance)
- Notebooksbilliger — €10.4M (Art. 6, video surveillance)
- Vodafone — €12M (Art. 5, 6, 28)

### Refresh Cadence

- Legal text: re-scrape quarterly (laws change slowly)
- Enforcement cases: re-scrape monthly (new decisions frequent)
- Translation step re-run only on new or changed German content
- Deltas are re-embedded and merged into the existing ChromaDB collection

## 📜 Licensing & Attribution

GDPR AI combines content from multiple sources with different license terms. This section makes the obligations explicit.

### Project code license

The GDPR AI **source code** (pipeline, scrapers, CLI, scripts, tests) is licensed under the **MIT License**. See `LICENSE` in the repository root.

### Knowledge base content — source-by-source terms

The knowledge base is a composite work that includes content under different licenses. When redistributing any part of the KB, preserve these attributions.

#### 1. GDPR / Regulation (EU) 2016/679

- **Source**: EUR-Lex (https://eur-lex.europa.eu)
- **Publisher**: European Union
- **Status**: Official EU legal text — public domain for reuse under the European Commission's reuse policy (Decision 2011/833/EU)
- **Attribution used in this project**:
  > GDPR text sourced from EUR-Lex (https://eur-lex.europa.eu). © European Union, 1998–present. Only European Union legislation published in the electronic Official Journal of the European Union is deemed authentic.

#### 2. BDSG (Bundesdatenschutzgesetz)

- **Source**: gesetze-im-internet.de (https://www.gesetze-im-internet.de/bdsg_2018)
- **Publisher**: Federal Ministry of Justice, Federal Republic of Germany, in cooperation with juris GmbH
- **Status**: German federal law — public text; redistribution permitted with attribution
- **Attribution used in this project**:
  > BDSG text sourced from gesetze-im-internet.de, provided by the Federal Ministry of Justice in cooperation with juris GmbH. English translation produced by GDPR AI using Claude (Anthropic) and has no legal status. Only the German original is authoritative.

#### 3. TTDSG / TDDDG

- **Source**: gesetze-im-internet.de (https://www.gesetze-im-internet.de/ttdsg)
- **Publisher**: Federal Ministry of Justice, Federal Republic of Germany
- **Status**: German federal law — public text; redistribution permitted with attribution
- **Attribution used in this project**:
  > TTDSG / TDDDG text sourced from gesetze-im-internet.de, provided by the Federal Ministry of Justice. English translation produced by GDPR AI using Claude (Anthropic) and has no legal status.

#### 4. EDPB Guidelines

- **Source**: edpb.europa.eu (https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en)
- **Publisher**: European Data Protection Board
- **Status**: Covered by the European Commission reuse policy
- **Attribution used in this project**:
  > EDPB Guidelines sourced from the European Data Protection Board (https://www.edpb.europa.eu). © European Union.

#### 5. DSK Kurzpapiere

- **Source**: datenschutzkonferenz-online.de (https://www.datenschutzkonferenz-online.de)
- **Publisher**: Datenschutzkonferenz (conference of independent German federal and state DPAs)
- **Status**: Public guidance; redistribution permitted with attribution
- **Attribution used in this project**:
  > DSK Kurzpapiere sourced from datenschutzkonferenz-online.de, © Datenschutzkonferenz. English translation produced by GDPR AI using Claude (Anthropic) and has no legal status.

#### 6. BfDI / BayLDA / LfDI BW Guidance

- **Sources**:
  - https://www.bfdi.bund.de
  - https://www.lda.bayern.de
  - https://www.baden-wuerttemberg.datenschutz.de
- **Publishers**: German federal and state data protection authorities
- **Status**: Public guidance; redistribution permitted with attribution
- **Attribution used in this project**:
  > Guidance sourced from the respective German data protection authority (BfDI, BayLDA, LfDI BW). English translation produced by GDPR AI using Claude (Anthropic) and has no legal status.

#### 7. GDPRhub — Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)

- **Source**: gdprhub.eu (https://gdprhub.eu)
- **Publisher**: noyb — European Center for Digital Rights
- **Status**: All content on GDPRhub is licensed under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
- **Obligations this project complies with**:
  - **BY (Attribution)** — every knowledge base chunk derived from GDPRhub retains the source URL and publisher in its metadata; this README and the runtime report output credit GDPRhub
  - **NC (NonCommercial)** — GDPR AI is used only noncommercially; the project does not charge users, does not include ads, and is not offered as a paid SaaS
  - **SA (ShareAlike)** — any redistribution of the GDPRhub-derived portion of the knowledge base must be under CC BY-NC-SA 4.0; adapted summaries indexed from GDPRhub are treated as adapted material under the same terms
- **Attribution used in this project**:
  > Case summaries and decision analyses adapted from GDPRhub (https://gdprhub.eu), © noyb — European Center for Digital Rights, licensed under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). Content adapted (summarized, chunked, and embedded) for retrieval-augmented generation. Changes: formatting, summarization, translation of incidental German terms to English. Original content available at the source URL stored with each chunk.
- **Commercial use note**: If this project ever becomes commercial (paid users, ads, paid API, or inclusion in a commercial product), GDPRhub-derived content must either be (a) removed, or (b) re-licensed via noyb by contacting `info@noyb.eu`. GDPRhub also offers an API for approved third parties.

#### 8. GDPR Enforcement Tracker

- **Source**: enforcementtracker.com (https://www.enforcementtracker.com)
- **Publisher**: CMS Hasche Sigle Partnerschaft von Rechtsanwälten und Steuerberatern mbB
- **Status**: Free public resource under the site's terms of use; attribution required; bulk extraction and systematic redistribution require permission from CMS
- **Obligations this project complies with**:
  - Attribution in the README and in retrieved chunk metadata
  - Only non-bulk, non-systematic use in v1 (personal research tool)
- **Attribution used in this project**:
  > Fine and enforcement metadata sourced from the GDPR Enforcement Tracker (https://www.enforcementtracker.com), © CMS Hasche Sigle. Data used for research and retrieval-augmented generation. For commercial or systematic use, contact CMS directly.

### Runtime attribution

When GDPR AI produces a report citing retrieved chunks, the report includes:

- The source name (e.g. "GDPRhub", "EUR-Lex", "gesetze-im-internet.de")
- The original URL stored in the chunk's metadata
- The license tag for the source

This ensures every cited piece of information is traceable back to its origin and license, satisfying the attribution obligations of CC BY-NC-SA 4.0 and the attribution expectations of the public-domain government sources.

### Third-party software licenses

Third-party libraries used in this project retain their own licenses (Apache-2.0, MIT, BSD-3-Clause, etc.). See `pyproject.toml` for the full dependency list. Notable:

- Anthropic SDK — MIT
- ChromaDB — Apache-2.0
- sentence-transformers — Apache-2.0
- BAAI/bge-m3 model weights — MIT
- httpx — BSD-3-Clause
- BeautifulSoup4 — MIT
- Typer, Pydantic, Rich — MIT

### Noncommercial guarantee (v1)

Because GDPRhub is licensed under CC BY-NC-SA 4.0, GDPR AI v1 is operated strictly **noncommercially**:

- No paid users
- No ads
- No paid API
- No bundling into commercial products
- Source code is MIT-licensed, but the compiled knowledge base (which includes GDPRhub-derived chunks) is redistributable only under CC BY-NC-SA 4.0

If commercial use is desired in the future, the commercial-licensing path described in the GDPRhub section must be completed first.

## 🤝 Contributing

This is a personal project demonstrating production-ready AI system design. The documentation shows the complete thought process, architectural decisions, and evaluation methodology.

If the project opens up to external contribution in the future, follow the branching workflow above: work on `develop` or a feature branch off `develop`, and merge to `main` only when a phase or release is complete.

## ⚖️ Disclaimer

GDPR AI provides **informational guidance only**. It is **not legal advice**. It is not a substitute for a qualified data protection lawyer or a certified Data Protection Officer. Outputs may be incomplete, outdated, or incorrect, and machine translation of source legal text may introduce inaccuracies. Consult qualified counsel for any compliance decision with legal or financial consequences.

Translations of German legal and regulatory text included in the knowledge base are produced by GDPR AI using a large language model (Claude, Anthropic). These translations have **no legal status**. Only the official German-language originals, as published by the Federal Ministry of Justice or the respective authority, are authoritative.

## 🙏 Acknowledgments

This project demonstrates modern AI engineering practices including:

- Retrieval-augmented generation with strict grounding
- Hybrid dense + sparse retrieval
- Domain-specific knowledge base construction
- One-time translation pipeline for multilingual source coverage
- Evaluation-first development
- Prompt versioning and iteration discipline
- Low-cost, local-first architecture
- German-market specialization delivered through an English-only runtime
- Careful handling of mixed-license source content with explicit attribution

Special thanks to:

- **noyb — European Center for Digital Rights** for maintaining GDPRhub as a free public resource under CC BY-NC-SA 4.0
- **CMS Hasche Sigle** for the GDPR Enforcement Tracker
- **European Data Protection Board** for publishing open guidelines
- **German Federal Ministry of Justice** and **juris GmbH** for gesetze-im-internet.de
- **Anthropic** for the Claude API that powers the reasoning pipeline
- **ChromaDB**, **sentence-transformers**, and **BAAI** for open-source retrieval tooling

## 📞 Contact

**Prathamesh Patil**
Essen, Germany
prathamesh.patil000009@gmail.com

---

Built with care, grounded reasoning, and zero hallucinations. 🚀# GDPR-COMPLIANCE_AI
