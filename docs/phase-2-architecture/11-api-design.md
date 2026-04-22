# Phase 2.11 – API Design

> **Status**: Deferred to v2. This document outlines the planned HTTP API for when GDPR AI evolves from a CLI tool to a web-accessible service.

## 1. Overview

Version 1 of GDPR AI is a command-line tool. It exposes no HTTP API. This document specifies the API design for v2, when a FastAPI layer will wrap the existing pipeline to serve a web UI and programmatic callers.

The API is designed to reuse the exact same pipeline components used by the CLI, ensuring behavioural parity between the two interfaces.

---

## 2. Design Principles

### 2.1 Thin HTTP Layer

The HTTP layer is a wrapper around the existing pipeline. No business logic is duplicated in API handlers.

### 2.2 REST-Style Endpoints

Endpoints follow REST conventions where they fit. Operations that do not map cleanly to CRUD use action-style paths.

### 2.3 JSON Everywhere

Request and response bodies are JSON. No form data, no multipart in v2 core.

### 2.4 Versioned URLs

All endpoints live under `/v1/` to allow for future breaking changes via `/v2/`.

### 2.5 Explicit Error Shape

Errors follow a consistent JSON structure for programmatic handling.

---

## 3. Planned Endpoints (v2)

### 3.1 Health and Meta

```
GET  /v1/health              → { "status": "ok", "version": "2.0.0" }
GET  /v1/version             → { "version": "2.0.0", "knowledge_base_indexed_at": "..." }
```

### 3.2 Primary Analysis

```
POST /v1/analyse
```

**Request body**

```json
{
  "scenario": "A German hospital accidentally emails patient test results to the wrong patient.",
  "options": {
    "include_similar_cases": true,
    "max_violations_returned": 10
  }
}
```

**Response body** (same schema as CLI output, plus envelope)

```json
{
  "query_id": "uuid",
  "scenario_summary": "...",
  "violations": [
    {
      "article": "Article 32",
      "paragraph": "1",
      "title": "Security of processing",
      "short_definition": "...",
      "scenario_explanation": "...",
      "source_url": "https://eur-lex.europa.eu/..."
    }
  ],
  "similar_cases": [ { "case_name": "...", "fine_amount_eur": 14500000, "url": "..." } ],
  "disclaimer": "...",
  "metadata": {
    "latency_ms": 3240,
    "cost_eur": 0.018,
    "model_used": "claude-sonnet-4-6"
  }
}
```

### 3.3 Feedback

```
POST /v1/feedback
```

**Request body**

```json
{
  "query_id": "uuid",
  "rating": "up" | "down",
  "comment": "optional text"
}
```

### 3.4 Query History (authenticated users)

```
GET  /v1/history              → last 50 queries for the authenticated user
GET  /v1/history/{query_id}   → detailed view of a single query
```

### 3.5 Knowledge Base Metadata

```
GET  /v1/kb/stats             → chunk counts per source, last refresh date
GET  /v1/kb/sources           → list of source documents indexed
```

---

## 4. Authentication and Authorisation (v2)

### 4.1 Authentication Model

Planned: API keys issued per user. Clients pass the key in the `Authorization` header:

```
Authorization: Bearer <api_key>
```

### 4.2 Authorisation Model

All endpoints except `/v1/health` and `/v1/version` require a valid API key.

### 4.3 Rate Limiting

Planned rate limits per API key:

* 60 requests per minute for `/v1/analyse`
* 600 requests per minute for read endpoints
* Excess requests → 429 with a `Retry-After` header

---

## 5. Error Shape

All errors share this structure:

```json
{
  "error": {
    "code": "INVALID_SCENARIO",
    "message": "Scenario is too short to analyse.",
    "details": { "min_length": 10, "provided_length": 5 }
  }
}
```

### 5.1 Error Code Catalogue

| Code | HTTP | Meaning |
|------|------|---------|
| `INVALID_SCENARIO` | 400 | Scenario fails input validation |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `PIPELINE_ERROR` | 500 | Pipeline stage failed |
| `LLM_UNAVAILABLE` | 503 | Anthropic API unreachable |
| `KNOWLEDGE_BASE_NOT_READY` | 503 | KB not yet indexed |

---

## 6. Observability

### 6.1 Request Logging

Every request logs:

* Request ID
* User ID (from API key)
* Endpoint
* Latency
* Status code
* Cost in EUR (for `/v1/analyse`)

### 6.2 Metrics

Planned Prometheus-style metrics:

* Request rate per endpoint
* Latency percentiles (p50, p95, p99)
* Error rates per code
* LLM token usage per hour

### 6.3 Tracing

OpenTelemetry spans for each pipeline stage, propagated across API and background workers.

---

## 7. Backward Compatibility

### 7.1 Rules

* Adding fields to responses is backward compatible
* Removing or renaming fields is not — requires `/v2/`
* Adding endpoints is backward compatible
* Changing error codes is not

### 7.2 Deprecation Policy

Deprecated endpoints continue working for 6 months after the new version ships. Deprecation is announced via response headers (`Warning: 299 - "deprecated"`).

---

## 8. CLI and API Parity

The CLI and API expose the same pipeline. Parity is enforced by:

* Shared Pydantic models for request and response
* Shared pipeline orchestrator
* Integration tests that verify CLI and API produce identical outputs for the same input

---

## 9. Open Questions for v2 Implementation

* Whether to support streaming responses for long reasoning steps
* Whether to offer a `/v1/batch-analyse` endpoint for bulk processing
* Whether to expose per-chunk evidence in the API response or gate it behind a flag
* Whether to offer webhook callbacks for async processing

These are tracked in the v2 planning document and decided closer to implementation.

---

## 10. Summary

The v2 API is designed as a thin, authenticated, JSON-over-HTTP wrapper around the existing pipeline. It inherits the pipeline's accuracy and cost characteristics while adding rate limiting, user authentication, and request history. Backward compatibility and observability are first-class concerns.

Implementation is deferred until v1 is shipped and the pipeline's behaviour is stable.