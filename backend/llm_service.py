from __future__ import annotations

import json
import os
from typing import Any

import requests


def build_prompt(stats: dict[str, Any]) -> str:
    """Build a stronger prompt so the LLM returns concrete, business-focused recommendations."""
    summary = stats.get("stats", {})
    return (
        "You are a senior FinOps and cloud cost optimization consultant. "
        "Analyze the billing summary and produce 3-5 recommendations that are specific, operationally actionable, and meaningful for a business team. "
        "Write each suggestion as a concrete next step a finance or engineering team could execute. "
        "Prefer cost levers such as rightsizing, schedule-based shutdowns, storage tier changes, reserved capacity, regional optimization, and idle resource cleanup. "
        "Avoid generic advice and do not repeat the same recommendation. "
        "Return JSON only with a list of objects. "
        "Each object must contain: suggestion, affected_resource, estimated_monthly_savings, priority. "
        f"Provider: {stats.get('provider', 'unknown')}. "
        f"Total monthly cost: {summary.get('total_cost', 0)}. "
        f"Top services: {summary.get('cost_by_service', {})}. "
        f"Top regions: {summary.get('cost_by_region', {})}. "
        f"Top expenses: {summary.get('top_expenses', [])}."
    )


def generate_suggestions(stats: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate structured suggestions using the Groq API or a business-friendly fallback."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback_suggestions(stats)

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a practical FinOps consultant focused on measurable cost reduction.",
                    },
                    {"role": "user", "content": build_prompt(stats)},
                ],
                "temperature": 0.2,
                "max_tokens": 400,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        message = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _parse_llm_response(message, stats)
    except Exception as exc:
        print(f"LLM request failed: {exc}")
        return _fallback_suggestions(stats)


def _parse_llm_response(raw_response: str, stats: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse JSON from the LLM response and return a list of suggestion dictionaries."""
    if not raw_response:
        return _fallback_suggestions(stats)

    cleaned_response = raw_response.strip()
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response.strip("`")
        if cleaned_response.lower().startswith("json"):
            cleaned_response = cleaned_response[4:].strip()

    try:
        parsed = json.loads(cleaned_response)
        if isinstance(parsed, list):
            return _normalize_suggestions(parsed, stats)
        if isinstance(parsed, dict) and isinstance(parsed.get("suggestions"), list):
            return _normalize_suggestions(parsed["suggestions"], stats)
    except (json.JSONDecodeError, TypeError):
        pass

    return _fallback_suggestions(stats)


def _normalize_suggestions(items: list[Any], stats: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize LLM suggestions into the expected shape."""
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        suggestion = str(item.get("suggestion", "")).strip()
        if not suggestion:
            suggestion = _default_suggestion(stats)

        normalized.append(
            {
                "suggestion": suggestion,
                "affected_resource": str(item.get("affected_resource", _default_resource(stats))),
                "estimated_monthly_savings": float(item.get("estimated_monthly_savings", 0.0) or 0.0),
                "priority": str(item.get("priority", "medium")).lower(),
            }
        )

    return normalized or _fallback_suggestions(stats)


def _fallback_suggestions(stats: dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic fallback suggestions that sound actionable and specific."""
    summary = stats.get("stats", {})
    top_expenses = summary.get("top_expenses", [])
    if top_expenses:
        first_expense = top_expenses[0]
        service_name = str(first_expense.get("service_name", "the largest cloud service") or "the largest cloud service")
        resource_id = str(first_expense.get("resource_id", "unknown") or "unknown")
        cost_value = float(first_expense.get("cost", 0.0) or 0.0)
        service_lower = service_name.lower()

        if "ec2" in service_lower or "compute" in service_lower:
            suggestion = (
                f"Rightsize {service_name} usage on {resource_id} by moving non-production workloads to smaller sizes and turning them off outside business hours; "
                "this is a strong lever for cutting idle compute spend."
            )
            priority = "high"
            savings = round(cost_value * 0.35, 2) or 120.0
        elif "s3" in service_lower or "storage" in service_lower:
            suggestion = (
                f"Move older {service_name} data on {resource_id} to a lower-cost storage tier and enforce lifecycle policies so inactive objects stop consuming premium storage."
            )
            priority = "medium"
            savings = round(cost_value * 0.2, 2) or 75.0
        elif "rds" in service_lower or "database" in service_lower:
            suggestion = (
                f"Right-size the {service_name} instance for {resource_id} and review backup and scaling settings to eliminate overprovisioned database capacity."
            )
            priority = "high"
            savings = round(cost_value * 0.25, 2) or 90.0
        else:
            suggestion = (
                f"Rightsize {service_name} usage for {resource_id} and apply a targeted cost lever such as shutdown policies or commitment discounts to reduce waste."
            )
            priority = "medium"
            savings = round(cost_value * 0.15, 2) or 60.0

        return [
            {
                "suggestion": suggestion,
                "affected_resource": resource_id,
                "estimated_monthly_savings": savings,
                "priority": priority,
            }
        ]

    return [
        {
            "suggestion": "Implement tagging and usage governance to identify idle resources and stop waste before it grows.",
            "affected_resource": "unknown",
            "estimated_monthly_savings": 75.0,
            "priority": "medium",
        }
    ]


def _default_resource(stats: dict[str, Any]) -> str:
    """Select a sensible resource name for fallback normalization."""
    summary = stats.get("stats", {})
    top_expenses = summary.get("top_expenses", [])
    if top_expenses:
        return str(top_expenses[0].get("resource_id", "unknown") or "unknown")
    return "unknown"


def _default_suggestion(stats: dict[str, Any]) -> str:
    """Provide a helpful default suggestion when the model omits the value."""
    summary = stats.get("stats", {})
    top_expenses = summary.get("top_expenses", [])
    if top_expenses:
        first_expense = top_expenses[0]
        service_name = str(first_expense.get("service_name", "the largest cloud service") or "the largest cloud service")
        resource_id = str(first_expense.get("resource_id", "unknown") or "unknown")
        return f"Review {service_name} usage for {resource_id} and apply a targeted optimization such as rightsizing or usage-based shutdowns."
    return "Review the largest cost item for rightsizing or idle-resource cleanup."
