"""Aggregate statistics from the query log (same source as ``gdpr-check stats``)."""

from __future__ import annotations

from fastapi import APIRouter

from gdpr_ai.api.schemas import StatsResponse
from gdpr_ai.logger import get_stats

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def stats() -> StatsResponse:
    """Return aggregate counters and averages for all logged queries."""
    raw = get_stats()
    return StatsResponse(
        total_queries=int(raw["total_queries"]),
        avg_latency_ms=float(raw["avg_latency_ms"]),
        avg_cost_eur=float(raw["avg_cost_eur"]),
        total_cost_eur=float(raw["total_cost_eur"]),
        total_tokens=float(raw["total_tokens"]),
        avg_violations_per_query=float(raw["avg_violations_per_query"]),
    )
