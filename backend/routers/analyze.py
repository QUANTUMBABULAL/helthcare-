"""
analyze.py — POST /api/analyze
Unified endpoint: accepts any image + optional text + health profile.
Returns food analysis OR prescription analysis based on AI classification.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models.schemas import HealthProfile, AnalyzeResponse
from services.analyze_service import run_analysis

router = APIRouter(tags=["Unified Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(...),
    user_message: Optional[str] = Form(default=None),
    health_profile: str = Form(default='{"conditions":[],"allergies":[]}'),
):
    """
    Two-stage AI pipeline:
    1. Classify image as food | prescription | unknown
    2. Run appropriate analysis and return structured result
    """

    try:
        image_bytes = await image.read()
        mime = image.content_type or "image/jpeg"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded image")

    try:
        parsed = json.loads(health_profile)
        health = HealthProfile(**parsed)
    except Exception:
        health = HealthProfile()

    try:
        result = await run_analysis(image_bytes, mime, user_message, health)
    except Exception:
        logger.error("run_analysis raised an unexpected error", exc_info=True)
        result = AnalyzeResponse(
            analysis_type="unknown",
            explanation="Something went wrong during analysis. Please try again.",
        )

    return result
