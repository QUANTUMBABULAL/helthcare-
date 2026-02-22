"""
vision_service.py — Uses OpenAI Vision (GPT-4o) to identify food items, classify images,
and analyze prescriptions. Safe, reload-proof, hackathon-ready implementation.
"""

import os
import base64
import json
from typing import List, Dict
from openai import OpenAI


FOOD_SYSTEM_PROMPT = """You are a nutrition-aware food recognition AI.

You will be given:
1) A photo of food
2) An optional user description of the food

Your task:
- Identify the most likely food name
- Infer common ingredients
- Estimate calories based on typical serving size

Rules:
- If the image is unclear, trust the user's description more
- Be conservative with calorie estimates
- Respond ONLY with valid JSON in this exact format:

{
  "items": [
    {
      "name": "Chocolate cupcake",
      "ingredients": ["flour", "sugar", "butter", "cocoa", "eggs"],
      "estimated_calories": 280
    }
  ]
}

Do not include any text outside the JSON.
"""

CLASSIFY_SYSTEM_PROMPT = """You are an image classification AI for a medical health app.

Look at the image and optional user message, then classify it into exactly one of:
- "food": the image shows food, a meal, drink, or ingredient
- "prescription": the image shows a doctor's prescription, medicine label, or handwritten/printed medical instructions
- "unknown": the image does not clearly fit food or prescription

Respond ONLY with valid JSON:
{
  "type": "food" | "prescription" | "unknown",
  "confidence": 0.0-1.0
}

Do not include any text outside the JSON.
"""

PRESCRIPTION_SYSTEM_PROMPT = """You are a medical prescription analysis AI. Patient safety is your top priority.

You will be given an image of a prescription (handwritten or printed) and optionally a patient health profile.

Your tasks:
1. OCR: Extract ALL visible text from the prescription
2. Parse each medicine: name, dosage, frequency
3. Assign a mock estimated cost per medicine (use realistic Indian pharmacy prices in INR)
4. Flag safety warnings based on the health profile

Respond ONLY with valid JSON:
{
  "raw_text": "full OCR text here",
  "medicines": [
    {
      "name": "Medicine name",
      "dosage": "e.g. 500mg",
      "frequency": "e.g. twice daily",
      "estimated_cost": "e.g. ₹45 for 10 tablets",
      "warnings": ["warning if any"]
    }
  ],
  "safety_notes": ["general safety note 1", "note 2"],
  "explanation": "friendly summary for the patient"
}

Do not include any text outside the JSON.
"""


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences if the model wraps JSON in them."""
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


async def classify_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    user_message: str | None = None,
) -> Dict:
    """
    Stage 1: Classify image as food / prescription / unknown.
    Returns {"type": str, "confidence": float}
    """
    try:
        client = get_openai_client()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        hint = user_message.strip() if user_message else ""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Classify this image."
                                if not hint
                                else f"Classify this image. User says: {hint}"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                        },
                    ],
                },
            ],
            max_tokens=100,
            temperature=0.1,
        )

        raw = _strip_fences(response.choices[0].message.content.strip())
        data = json.loads(raw)
        img_type = data.get("type", "unknown")
        if img_type not in ("food", "prescription", "unknown"):
            img_type = "unknown"
        confidence = float(data.get("confidence", 0.5))
        return {"type": img_type, "confidence": confidence}

    except Exception:
        return {"type": "unknown", "confidence": 0.0}


async def analyze_food_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    food_hint: str | None = None,
) -> List[Dict]:
    """
    Sends an image to GPT-4o Vision and returns detected food items.
    """

    try:
        client = get_openai_client()

        b64 = base64.b64encode(image_bytes).decode("utf-8")

        hint_text = food_hint.strip() if isinstance(food_hint, str) else ""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": FOOD_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Identify the food items in this image and estimate calories for each."
                                if not hint_text
                                else f"Identify the food items in this image. User hint: {hint_text}"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64}"
                            },
                        },
                    ],
                },
            ],
            max_tokens=600,
            temperature=0.2,
        )

        raw = _strip_fences(response.choices[0].message.content.strip())
        data = json.loads(raw)

        items = data.get("items", [])
        if not isinstance(items, list):
            raise ValueError("Invalid items format from OpenAI")

        normalized_items: List[Dict] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "Unknown food"))
            calories = int(item.get("estimated_calories", 250) or 250)
            ingredients = item.get("ingredients", [])
            if not isinstance(ingredients, list):
                ingredients = []
            normalized_items.append(
                {
                    "name": name,
                    "ingredients": [str(i).strip().lower() for i in ingredients if str(i).strip()],
                    "estimated_calories": calories,
                }
            )

        if not normalized_items:
            raise ValueError("No valid food items returned from OpenAI")

        return normalized_items

    except Exception:
        # FAIL SAFE: never crash the app
        return [
            {
                "name": "Unknown food",
                "ingredients": [],
                "estimated_calories": 250,
            }
        ]


async def analyze_prescription_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    health_profile_summary: str = "",
    user_message: str | None = None,
) -> Dict:
    """
    Stage 2 (prescription): OCR the prescription, extract medicines, flag warnings.
    Returns dict matching PrescriptionAnalysisResponse schema.
    """
    try:
        client = get_openai_client()
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        system = PRESCRIPTION_SYSTEM_PROMPT
        if health_profile_summary:
            system += f"\n\nPatient health profile: {health_profile_summary}"

        hint = user_message.strip() if user_message else ""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this prescription."
                                if not hint
                                else f"Analyze this prescription. Patient note: {hint}"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                        },
                    ],
                },
            ],
            max_tokens=1000,
            temperature=0.2,
        )

        raw = _strip_fences(response.choices[0].message.content.strip())
        data = json.loads(raw)

        medicines = []
        for med in data.get("medicines", []):
            if not isinstance(med, dict):
                continue
            medicines.append({
                "name": str(med.get("name", "Unknown")),
                "dosage": str(med.get("dosage", "N/A")),
                "frequency": str(med.get("frequency", "N/A")),
                "estimated_cost": str(med.get("estimated_cost", "N/A")),
                "warnings": [str(w) for w in med.get("warnings", []) if str(w).strip()],
            })

        return {
            "raw_text": str(data.get("raw_text", "")),
            "medicines": medicines,
            "safety_notes": [str(n) for n in data.get("safety_notes", []) if str(n).strip()],
            "explanation": str(data.get("explanation", "Prescription analyzed.")),
        }

    except Exception:
        return {
            "raw_text": "",
            "medicines": [],
            "safety_notes": ["Unable to fully read the prescription. Please consult your doctor."],
            "explanation": "Could not analyze the prescription. Please consult your healthcare provider.",
        }
