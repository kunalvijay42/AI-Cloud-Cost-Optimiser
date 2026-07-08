from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SuggestionItem(BaseModel):
    """Structured output for an AI-generated cost optimisation suggestion."""
    suggestion: str = Field(..., description="Short description of the recommendation")
    affected_resource: str = Field(..., description="Resource or service impacted")
    estimated_monthly_savings: float = Field(..., description="Estimated monthly savings")
    priority: str = Field(..., description="Suggested priority: low, medium, or high")


class AnalysisStats(BaseModel):
    """Summary statistics derived from the normalized billing data."""
    total_cost: float
    total_records: int
    cost_by_service: dict[str, float]
    cost_by_region: dict[str, float]
    top_expenses: list[dict[str, Any]]
    month_over_month: dict[str, float]


class AnalysisResponse(BaseModel):
    """Response returned by the backend analysis endpoint."""
    provider: str
    stats: AnalysisStats
    suggestions: list[SuggestionItem]
