from __future__ import annotations

from collections import defaultdict
from typing import Any


def compute_stats(normalized_rows: list[dict[str, Any]], provider: str) -> dict[str, Any]:
    """Compute basic statistics from normalized billing rows."""
    if not normalized_rows:
        raise ValueError("No normalized rows were provided for analysis.")

    total_cost = round(sum(float(row["cost"]) for row in normalized_rows), 2)
    cost_by_service: dict[str, float] = defaultdict(float)
    cost_by_region: dict[str, float] = defaultdict(float)
    monthly_trend: dict[str, float] = defaultdict(float)

    for row in normalized_rows:
        service_name = str(row.get("service_name", "unknown"))
        region = str(row.get("region", "unknown"))
        date_value = str(row.get("date", "unknown"))
        cost_value = float(row.get("cost", 0.0))

        cost_by_service[service_name] += cost_value
        cost_by_region[region] += cost_value

        if date_value != "unknown":
            monthly_trend[date_value] += cost_value

    top_expenses = sorted(
        [
            {
                "service_name": row["service_name"],
                "resource_id": row["resource_id"],
                "cost": round(float(row["cost"]), 2),
                "region": row["region"],
                "date": row["date"],
            }
            for row in normalized_rows
        ],
        key=lambda item: item["cost"],
        reverse=True,
    )[:5]

    return {
        "provider": provider,
        "stats": {
            "total_cost": total_cost,
            "total_records": len(normalized_rows),
            "cost_by_service": {key: round(value, 2) for key, value in dict(cost_by_service).items()},
            "cost_by_region": {key: round(value, 2) for key, value in dict(cost_by_region).items()},
            "top_expenses": top_expenses,
            "month_over_month": {
                key: round(value, 2) for key, value in sorted(monthly_trend.items())
            },
        },
    }
