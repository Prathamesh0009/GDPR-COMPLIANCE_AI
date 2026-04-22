# GDPR AI – Documentation

This folder contains the complete design, requirements, and execution documentation for GDPR AI. The structure follows a four-phase engineering discipline: from problem framing, through requirements and architecture, into execution strategy.

Every document in this folder is version-controlled and updated in lockstep with the codebase. When a design decision changes, the relevant document is updated and the change is captured in a commit alongside the code change that implements it.

## Phase 0 – Overview

Foundational framing of what GDPR AI is, why it exists, who it serves, and how it will be delivered.

* [01 – Problem Statement](phase-0-overview/01-problem-statement.md)
* [02 – Why GDPR AI](phase-0-overview/02-why-gdpr-ai.md)
* [03 – Target Users](phase-0-overview/03-target-users.md)
* [04 – Implementation Plan](phase-0-overview/04-implementation-plan.md)

## Phase 1 – Requirements

What the system must do, how well it must do it, and the boundaries within which it operates.

* [05 – Functional Requirements](phase-1-requirements/05-functional-requirements.md)
* [06 – Non-Functional Requirements](phase-1-requirements/06-non-functional-requirements.md)
* [07 – Constraints and Assumptions](phase-1-requirements/07-constraints-assumptions.md)

## Phase 2 – Architecture

System-level design decisions, stack mapping, data model, and cross-cutting concerns.

* [08 – High-Level Architecture](phase-2-architecture/08-high-level-architecture.md)
* [09 – Technical Stack Mapping](phase-2-architecture/09-technical-stack-mapping.md)
* [10 – Data and Knowledge Model Design](phase-2-architecture/10-data-knowledge-model.md)
* [11 – API Design](phase-2-architecture/11-api-design.md) *(deferred to v2)*
* [12 – Cloud Architecture and Deployment](phase-2-architecture/12-cloud-architecture.md) *(deferred to v2)*
* [13 – Security Design](phase-2-architecture/13-security-design.md)

## Phase 3 – Execution and Build Strategy

Implementation-level detail: modules, flow, testing, frontend, CI/CD, monitoring.

* [14 – Backend Execution Design](phase-3-execution/14-backend-execution-design.md)
* [15 – Pipeline Module Design](phase-3-execution/15-pipeline-module-design.md)
* [16 – Knowledge Base Schema Design](phase-3-execution/16-knowledge-base-schema.md)
* [17 – Runtime Request Flow](phase-3-execution/17-runtime-request-flow.md)
* [18 – Frontend Design](phase-3-execution/18-frontend-design.md) *(deferred to v2)*
* [19 – Testing Strategy](phase-3-execution/19-testing-strategy.md)
* [20 – CI/CD Pipeline Design](phase-3-execution/20-cicd-pipeline.md) *(deferred to v2)*
* [21 – Monitoring and Alerting Design](phase-3-execution/21-monitoring-alerting.md)

## Architecture Decision Records (ADRs)

Point-in-time records of significant design decisions, preserved even when decisions are later superseded.

* [001 – Pre-Indexed RAG over Live Fetching](adr/001-pre-indexed-rag-over-live-fetching.md)
* [002 – ChromaDB for v1](adr/002-chromadb-for-v1.md)
* [003 – English-Only Runtime](adr/003-english-only-runtime.md)
* [004 – One-Time Translation of German Sources](adr/004-one-time-translation.md)
* [005 – Strict Grounding Over Generation Quality](adr/005-strict-grounding.md)

## How to Read This

If you are new to the project, read in the following order:

1. Phase 0 documents in sequence (01 → 04)
2. Phase 1 in sequence (05 → 07)
3. Phase 2 High-Level Architecture (08) and Data Model (10)
4. Any Phase 3 document relevant to what you are working on

If you are evaluating the project for portfolio or hiring purposes, the most informative documents are:

* [01 – Problem Statement](phase-0-overview/01-problem-statement.md)
* [08 – High-Level Architecture](phase-2-architecture/08-high-level-architecture.md)
* [09 – Technical Stack Mapping](phase-2-architecture/09-technical-stack-mapping.md)
* [15 – Pipeline Module Design](phase-3-execution/15-pipeline-module-design.md)
* [19 – Testing Strategy](phase-3-execution/19-testing-strategy.md)

## Document Conventions

* Every document uses numbered section headers for navigability
* Tables are used for comparisons and structured data
* Code blocks are used for concrete examples, commands, and schemas
* Cross-references use relative markdown links
* Deferred work is explicitly marked to distinguish it from unaddressed work