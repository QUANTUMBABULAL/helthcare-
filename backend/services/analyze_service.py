"""
analyze_service.py — Two-stage AI pipeline for unified image analysis.

Stage 1: Classify image as food | prescription | unknown
Stage 2: Execute the appropriate analysis based on classification
"""

import os
import base64
import json
import logging
from typing import Optional
from openai import OpenAI

from models.schemas import (
    HealthProfile,
    FoodAnalysisResponse,
    PrescriptionResult,
    MedicineItem,
    AnalyzeResponse,
)
from services.vision_service import analyze_food_image
from services.nutrition_service import evaluate_food_item

logger = logging.getLogger(__name__)

# ---------- Mock medicine price list ----------

MEDICINE_PRICES = {
    "amoxicillin": 15.0,
    "metformin": 10.0,
    "lisinopril": 12.0,
    "atorvastatin": 25.0,
    "omeprazole": 18.0,
    "ibuprofen": 8.0,
    "paracetamol": 5.0,
    "aspirin": 6.0,
    "cetirizine": 9.0,
    "azithromycin": 20.0,
    "pantoprazole": 14.0,
    "amlodipine": 11.0,
    "losartan": 13.0,
    "dolo": 5.0,
    "ciprofloxacin": 17.0,
}

CLASSIFY_SYSTEM_PROMPT = """You are a medical image classifier.
Look at the image (and optional user message) and return ONLY valid JSON:

{
  "type": "food",
  "confidence": 0.95
}

Rules:
- "food": image shows food, meals, snacks, beverages, or ingredients
- "prescription": image shows a medical prescription, medicine label, doctor's note, or any medical document with medicine names
- "unknown": anything else (selfie, landscape, document, etc.)

Respond with ONLY the JSON. No explanation. No markdown.
"""

PRESCRIPTION_SYSTEM_PROMPT = """You are a medical prescription OCR and safety expert.

Patient health profile:
{health_context}

Analyze the prescription image carefully. Extract and return ONLY valid JSON:

{{
  "medicines": [
    {{
      "name": "Medicine name",
      "dosage": "dose per tablet/unit",
      "frequency": "e.g. twice daily",
      "duration": "e.g. 7 days"
    }}
  ],
  "safety_warnings": ["warning 1", "warning 2"],
  "ocr_text": "raw visible text from prescription",
  "explanation": "brief plain-language summary for the patient"
}}

Safety rules you MUST apply:
- Flag any drug that interacts with patient's current medications
- Flag contraindications based on patient conditions
- If image is unclear or unreadable, set safety_warnings to ["Prescription image is unclear – please consult your pharmacist or doctor."]
- Always prioritize patient safety

Respond with ONLY the JSON. No markdown. No text outside JSON.
"""


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _encode_image(image_bytes: bytes, mime_type: str) -> str:
    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"


# ─────────────────────────────────────────────
# Stage 1 — Classification
# ─────────────────────────────────────────────

async def classify_image(
    image_bytes: bytes,
    mime_type: str,
    user_message: Optional[str],
) -> dict:
    """Returns {"type": "food"|"prescription"|"unknown", "confidence": float}."""
    try:
        client = _get_client()
        image_url = _encode_image(image_bytes, mime_type)

        hint = f"User message: {user_message.strip()}" if user_message and user_message.strip() else "No user message provided."

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": hint},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            max_tokens=80,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        data = json.loads(raw)
        return {
            "type": data.get("type", "unknown"),
            "confidence": float(data.get("confidence", 0.5)),
        }
    except Exception:
        logger.warning("classify_image failed", exc_info=True)
        return {"type": "unknown", "confidence": 0.0}


# ─────────────────────────────────────────────
# Stage 2a — Food Analysis (delegates to existing service)
# ─────────────────────────────────────────────

async def _run_food_analysis(
    image_bytes: bytes,
    mime_type: str,
    user_message: Optional[str],
    health: HealthProfile,
) -> FoodAnalysisResponse:
    try:
        detected_items = await analyze_food_image(image_bytes, mime_type, user_message)
    except Exception:
        logger.warning("analyze_food_image failed", exc_info=True)
        detected_items = [{"name": "Unknown food", "ingredients": [], "estimated_calories": 250}]

    from models.schemas import FoodItem
    evaluated = []
    for item in detected_items:
        name = str(item.get("name", "Unknown food"))
        calories = int(item.get("estimated_calories", 250) or 250)
        ingredients = item.get("ingredients", [])
        if not isinstance(ingredients, list):
            ingredients = []
        evaluated.append(evaluate_food_item(name, calories, ingredients, health))

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

    return FoodAnalysisResponse(
        items=evaluated,
        total_calories=total_cal,
        explanation=" ".join(parts),
    )


# ─────────────────────────────────────────────
# Stage 2b — Prescription Analysis
# ─────────────────────────────────────────────

def _build_health_context(health: HealthProfile) -> str:
    parts = []
    if health.conditions:
        parts.append(f"Conditions: {', '.join(health.conditions)}")
    if health.allergies:
        parts.append(f"Allergies: {', '.join(health.allergies)}")
    if health.medications:
        parts.append(f"Current medications: {', '.join(health.medications)}")
    if health.age:
        parts.append(f"Age: {health.age}")
    return "\n".join(parts) if parts else "No health profile provided."


async def _run_prescription_analysis(
    image_bytes: bytes,
    mime_type: str,
    health: HealthProfile,
) -> PrescriptionResult:
    try:
        client = _get_client()
        image_url = _encode_image(image_bytes, mime_type)
        health_context = _build_health_context(health)

        system_prompt = PRESCRIPTION_SYSTEM_PROMPT.format(health_context=health_context)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please read and analyze this prescription."},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            max_tokens=1000,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        data = json.loads(raw)

        medicines_raw = data.get("medicines", [])
        medicines = []
        cost_estimate = {}

        for m in medicines_raw:
            if not isinstance(m, dict):
                continue
            name = str(m.get("name", "Unknown")).strip()
            medicines.append(MedicineItem(
                name=name,
                dosage=str(m.get("dosage", "As prescribed")),
                frequency=str(m.get("frequency", "As directed")),
                duration=str(m.get("duration", "As directed")),
            ))
            # Mock cost lookup
            key = name.lower().split()[0]
            cost_estimate[name] = MEDICINE_PRICES.get(key, 20.0)

        safety_warnings = data.get("safety_warnings", [])
        if not isinstance(safety_warnings, list):
            safety_warnings = []

        return PrescriptionResult(
            medicines=medicines,
            safety_warnings=safety_warnings,
            cost_estimate=cost_estimate,
            ocr_text=str(data.get("ocr_text", "")),
            explanation=str(data.get("explanation", "Prescription analyzed.")),
        )

    except Exception:
        logger.warning("_run_prescription_analysis failed", exc_info=True)
        return PrescriptionResult(
            medicines=[],
            safety_warnings=["Could not read prescription. Please consult your pharmacist or doctor."],
            cost_estimate={},
            ocr_text="",
            explanation="Unable to analyze the prescription image. Please ensure the image is clear and try again.",
        )


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

async def run_analysis(
    image_bytes: bytes,
    mime_type: str,
    user_message: Optional[str],
    health: HealthProfile,
) -> AnalyzeResponse:
    """Run two-stage pipeline: classify → execute."""

    classification = await classify_image(image_bytes, mime_type, user_message)
    img_type = classification.get("type", "unknown")

    if img_type == "food":
        food_result = await _run_food_analysis(image_bytes, mime_type, user_message, health)
        return AnalyzeResponse(
            analysis_type="food",
            food_result=food_result,
            explanation=food_result.explanation,
        )

    if img_type == "prescription":
        rx_result = await _run_prescription_analysis(image_bytes, mime_type, health)
        return AnalyzeResponse(
            analysis_type="prescription",
            prescription_result=rx_result,
            explanation=rx_result.explanation,
        )

    # Unknown — try food analysis as best-effort fallback
    food_result = await _run_food_analysis(image_bytes, mime_type, user_message, health)
    return AnalyzeResponse(
        analysis_type="unknown",
        food_result=food_result,
        explanation=(
            "I couldn't clearly identify the image type. "
            "I've attempted a food analysis — if this is something else, please add a description."
        ),
    )
