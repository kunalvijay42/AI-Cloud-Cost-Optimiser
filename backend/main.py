from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile

from backend.analyzer import compute_stats
from backend.llm_service import generate_suggestions
from backend.models import AnalysisResponse, AnalysisStats, SuggestionItem
from backend.parser import parse_and_normalize_bill

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Cloud Cost Optimiser API", version="0.1.0")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_bill(file: UploadFile = File(...)) -> AnalysisResponse:
    """Analyze an uploaded cloud billing CSV and return stats plus AI suggestions."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        contents = await file.read()
        if not contents:
            raise ValueError("Uploaded file is empty.")

        parsed_bill = parse_and_normalize_bill(contents, file.filename)
        stats = compute_stats(parsed_bill["rows"], parsed_bill["provider"])
        suggestion_payload = generate_suggestions(stats)

        return AnalysisResponse(
            provider=parsed_bill["provider"],
            stats=AnalysisStats(**stats["stats"]),
            suggestions=[SuggestionItem(**item) for item in suggestion_payload],
        )
    except ValueError as exc:
        logger.warning("Validation error while analyzing bill: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard for the scaffold
        logger.exception("Unexpected error while analyzing bill")
        raise HTTPException(status_code=500, detail="Unable to analyze the uploaded bill.") from exc
