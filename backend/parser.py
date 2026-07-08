from __future__ import annotations

import io
from typing import Any

import pandas as pd


def detect_provider(headers: list[str]) -> str:
    """Detect the likely cloud provider by inspecting column names."""
    normalized_headers = {header.strip().lower().replace(" ", "_") for header in headers}

    aws_markers = {"productname", "usagequantity", "blendedcost", "resourceid"}
    azure_markers = {"metername", "pretaxcost", "resourceid"}
    gcp_markers = {"service", "sku", "cost", "usage_quantity", "resourceid"}

    if aws_markers.issubset(normalized_headers):
        return "aws"
    if azure_markers.issubset(normalized_headers):
        return "azure"
    if gcp_markers.issubset(normalized_headers):
        return "gcp"

    return "unknown"


def parse_and_normalize_bill(file_contents: bytes, filename: str) -> dict[str, Any]:
    """Read a billing CSV and normalize it into a common schema."""
    if not file_contents:
        raise ValueError("Uploaded file is empty.")

    dataframe = pd.read_csv(io.BytesIO(file_contents))
    headers = [str(column).strip() for column in dataframe.columns]
    provider = detect_provider(headers)

    if provider == "unknown":
        raise ValueError("Unable to identify the cloud provider from the CSV headers.")

    aliases: dict[str, dict[str, list[str]]] = {
        "aws": {
            "service_name": ["service_name", "product_name", "productname", "line_item_description"],
            "resource_id": ["resource_id", "resourceid"],
            "cost": ["cost", "blended_cost", "blendedcost", "unblended_cost"],
            "usage_quantity": ["usage_quantity", "usagequantity"],
            "region": ["region", "location"],
            "date": ["date", "usage_start_date", "start_date"],
        },
        "azure": {
            "service_name": ["service_name", "meter_name", "metername", "consumed_service"],
            "resource_id": ["resource_id", "resourceid"],
            "cost": ["cost", "pretax_cost", "pretaxcost"],
            "usage_quantity": ["usage_quantity", "usagequantity"],
            "region": ["region", "location"],
            "date": ["date", "usage_start_date", "start_date"],
        },
        "gcp": {
            "service_name": ["service_name", "service", "sku"],
            "resource_id": ["resource_id", "resourceid"],
            "cost": ["cost"],
            "usage_quantity": ["usage_quantity", "usagequantity"],
            "region": ["region", "location"],
            "date": ["date", "usage_start_date", "start_date"],
        },
    }

    field_map = aliases[provider]
    normalized_rows: list[dict[str, Any]] = []

    for _, row in dataframe.iterrows():
        normalized_row: dict[str, Any] = {
            "service_name": _first_available_value(row, field_map["service_name"]),
            "resource_id": _first_available_value(row, field_map["resource_id"]),
            "cost": float(_first_available_value(row, field_map["cost"], default="0")),
            "usage_quantity": float(_first_available_value(row, field_map["usage_quantity"], default="0")),
            "region": _first_available_value(row, field_map["region"], default="unknown"),
            "date": str(_first_available_value(row, field_map["date"], default="unknown")),
            "provider": provider,
            "source_file": filename,
        }
        normalized_rows.append(normalized_row)

    if not normalized_rows:
        raise ValueError("The uploaded CSV did not contain any rows to analyze.")

    return {"provider": provider, "rows": normalized_rows}


def _first_available_value(row: Any, candidates: list[str], default: str = "") -> Any:
    """Return the first matching column value from a pandas row."""
    normalized_candidates = {
        candidate.strip().lower().replace(" ", "_") for candidate in candidates
    }

    for column_name in row.index:
        normalized_column = str(column_name).strip().lower().replace(" ", "_")
        if normalized_column in normalized_candidates:
            value = row[column_name]
            if pd.notna(value):
                return value

    return default
