"""NutriGuide AI - Empirical Evaluation & Hallucination Metrics Router"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

RESULTS_FILE = Path(__file__).parent.parent / "data" / "hallucination_evaluation_results.json"


@router.get("/evaluation/hallucination")
async def get_hallucination_evaluation():
    """
    Returns empirical hallucination and latency benchmark evaluation metrics:
    - Faithfulness Rate (%)
    - Unsupported Claim Rate (%)
    - Contradiction Rate (%)
    - Correct Abstention Rate (%)
    - Average Response Latency (ms)
    - Detailed category breakdown
    """
    if not RESULTS_FILE.exists():
        # Fallback to run lightweight evaluation if results file is not yet written
        try:
            from tests.evaluate_hallucination import run_full_evaluation
            return await run_full_evaluation(max_cases=5)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Evaluation results not yet available: {e}")

    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as exc:
        logger.error(f"Failed to read evaluation results: {exc}")
        raise HTTPException(status_code=500, detail="Could not read benchmark evaluation data.")
