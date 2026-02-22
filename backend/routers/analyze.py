"""
analyze.py — POST /api/analyze
Unified endpoint: classifies any uploaded image (food or prescription),
then runs the appropriate analysis pipeline.
"""

from fastapi import APIRouter, UploadFile, File, Form
import json
from typing import Optional

from models.schemas import (
    HealthProfile,
    FoodItem,
    FoodAnalysisResponse,
    MedicineItem,
    PrescriptionAnalysisResponse,
    AnalyzeResponse,
)
from services.vision_service import (
    classify_image,
    analyze_food_image,
    analyze_prescription_image,
)
from services.nutrition_service import evaluate_food_item

router = APIRouter(tags=["Unified Analysis"])


def _build_health_summary(health: HealthProfile) -> str:
    parts = []
    if health.conditions:
        parts.append(f"Conditions: {', '.join(health.conditions)}")
    if health.allergies:
        parts.append(f"Allergies: {', '.join(health.allergies)}")
    if health.medications:
        parts.append(f"Medications: {', '.join(health.medications)}")
    if health.age:
        parts.append(f"Age: {health.age}")
    return ". ".join(parts) if parts else "No known conditions."


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: Optional[UploadFile] = File(None),
    user_message: Optional[str] = Form(default=None),
    health_profile: str = Form(default='{"conditions":[],"allergies":[]}'),
):
    """
    Two-stage AI pipeline:
      Stage 1 — classify the image (food | prescription | unknown)
      Stage 2 — run the appropriate analysis based on classification
    Never crashes; always returns a safe fallback.
    """

    # ── Parse health profile ──────────────────────────────────────────────
    try:
        health = HealthProfile(**json.loads(health_profile))
    except Exception:
        health = HealthProfile()

    health_summary = _build_health_summary(health)

    # ── Read image bytes ──────────────────────────────────────────────────
    image_bytes: bytes = b""
    mime_type = "image/jpeg"
    if image and image.filename:
        try:
            image_bytes = await image.read()
            mime_type = image.content_type or "image/jpeg"
        except Exception:
            image_bytes = b""

    if not image_bytes:
        return AnalyzeResponse(
            type="unknown",
            confidence=0.0,
            message="No image provided. Please upload an image to analyze.",
        )

    # ── Stage 1: Classification ───────────────────────────────────────────
    try:
        classification = await classify_image(image_bytes, mime_type, user_message)
    except Exception:
        classification = {"type": "unknown", "confidence": 0.0}

    img_type: str = classification.get("type", "unknown")
    confidence: float = float(classification.get("confidence", 0.0))

    # ── Stage 2: Task execution ───────────────────────────────────────────

    # ---- FOOD ----
    if img_type == "food":
        try:
            detected_items = await analyze_food_image(image_bytes, mime_type, user_message)
        except Exception:
            detected_items = [{"name": "Unknown food", "ingredients": [], "estimated_calories": 250}]

        evaluated: list[FoodItem] = []
        for item in detected_items:
            evaluated.append(
                evaluate_food_item(
                    str(item.get("name", "Unknown food")),
                    int(item.get("estimated_calories", 250) or 250),
                    item.get("ingredients", []) if isinstance(item.get("ingredients"), list) else [],
                    health,
                )
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
            type="food",
            confidence=confidence,
            food_data=FoodAnalysisResponse(
                items=evaluated,
                total_calories=total_cal,
                explanation=" ".join(parts),
            ),
        )

    # ---- PRESCRIPTION ----
    if img_type == "prescription":
        try:
            rx_data = await analyze_prescription_image(
                image_bytes, mime_type, health_summary, user_message
            )
        except Exception:
            rx_data = {
                "raw_text": "",
                "medicines": [],
                "safety_notes": ["Please consult your doctor."],
                "explanation": "Could not analyze the prescription.",
            }

        medicines = [MedicineItem(**m) for m in rx_data.get("medicines", [])]

        return AnalyzeResponse(
            type="prescription",
            confidence=confidence,
            prescription_data=PrescriptionAnalysisResponse(
                raw_text=rx_data.get("raw_text", ""),
                medicines=medicines,
                safety_notes=rx_data.get("safety_notes", []),
                explanation=rx_data.get("explanation", ""),
            ),
        )

    # ---- UNKNOWN ----
    return AnalyzeResponse(
        type="unknown",
        confidence=confidence,
        message=(
            "I couldn't clearly identify what's in this image. "
            "Try uploading a clearer photo of food or a prescription, "
            "or add a description in the message box."
        ),
    )
