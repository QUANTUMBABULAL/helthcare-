"""
analyze.py — POST /api/analyze
Unified two-stage AI pipeline: classify any image then run appropriate analysis.
"""

import json
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models.schemas import (
    HealthProfile,
    FoodItem,
    FoodAnalysisResponse,
    PrescriptionMedicineExtract,
    PrescriptionAnalysisResponse,
    AnalyzeResponse,
)
from services.vision_service import classify_image, analyze_food_image, analyze_prescription_image
from services.nutrition_service import evaluate_food_item
from services.prescription_service import evaluate_prescription

router = APIRouter(tags=["Unified Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(...),
    user_message: Optional[str] = Form(default=None),
    health_profile: str = Form(default='{"conditions":[],"allergies":[]}'),
):
    """
    Stage 1 — Classify the image (food / prescription / unknown).
    Stage 2 — Run the appropriate analysis pipeline.
    Patient health profile is applied in every stage.
    """

    try:
        image_bytes = await image.read()
        mime = image.content_type or "image/jpeg"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    try:
        parsed_profile = json.loads(health_profile)
        health = HealthProfile(**parsed_profile)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid health_profile JSON")

    # ── Stage 1: Classify ────────────────────────────────────────────────────
    try:
        classification = await classify_image(image_bytes, mime, user_message)
    except Exception:
        classification = {"type": "unknown", "confidence": 0.0}

    image_type = classification.get("type", "unknown")
    confidence = float(classification.get("confidence", 0.0))

    # ── Stage 2: Execute ─────────────────────────────────────────────────────
    try:
        if image_type == "food":
            detected_items = await analyze_food_image(image_bytes, mime, user_message)

            evaluated: list[FoodItem] = []
            for item in detected_items:
                item_name = str(item.get("name", "Unknown food"))
                item_calories = int(item.get("estimated_calories", 250) or 250)
                item_ingredients = item.get("ingredients", [])
                if not isinstance(item_ingredients, list):
                    item_ingredients = []
                evaluated.append(
                    evaluate_food_item(item_name, item_calories, item_ingredients, health)
                )

            total_cal = sum(i.estimated_calories for i in evaluated)
            avoid_items = [i.name for i in evaluated if i.verdict == "AVOID"]
            limit_items = [i.name for i in evaluated if i.verdict == "LIMIT"]

            parts = [f"Total estimated calories: ~{total_cal} kcal."]
            if avoid_items:
                parts.append(f"You should AVOID: {', '.join(avoid_items)}.")
            if limit_items:
                parts.append(f"Consider LIMITING: {', '.join(limit_items)}.")
            if not avoid_items and not limit_items:
                parts.append("Everything looks fine for your health profile!")

            return AnalyzeResponse(
                response_type="food",
                confidence=confidence,
                food=FoodAnalysisResponse(
                    items=evaluated,
                    total_calories=total_cal,
                    explanation=" ".join(parts),
                ),
            )

        elif image_type == "prescription":
            extracted_raw = await analyze_prescription_image(image_bytes, mime, None)
            extracted: list[PrescriptionMedicineExtract] = []
            for med in extracted_raw:
                try:
                    extracted.append(PrescriptionMedicineExtract(**med))
                except Exception:
                    continue

            prescription_response = evaluate_prescription(extracted, health, None)
            return AnalyzeResponse(
                response_type="prescription",
                confidence=confidence,
                prescription=prescription_response,
            )

        else:
            return AnalyzeResponse(
                response_type="unknown",
                confidence=confidence,
                message=(
                    "I couldn't identify the content of this image. "
                    "Please upload a food photo or prescription image, "
                    "and optionally describe what it is in the message box."
                ),
            )

    except Exception:
        return AnalyzeResponse(
            response_type="unknown",
            confidence=0.0,
            message="Image analysis failed. Please ensure the image is clear and try again.",
        )
