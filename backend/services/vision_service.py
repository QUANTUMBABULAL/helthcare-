"""
vision_service.py — Uses OpenAI Vision (GPT-4o) to identify food items in an image.
Safe, reload-proof, hackathon-ready implementation.
"""

import os
import base64
import json
from typing import List, Dict
from openai import OpenAI


SYSTEM_PROMPT = """You are a nutrition-aware food recognition AI.

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


PRESCRIPTION_SYSTEM_PROMPT = """You are a medical document reading assistant for prescriptions.

Task:
- Read the prescription image carefully.
- Extract medicine names, dose, frequency, and duration.
- Return only strict JSON with this structure:

{
    "medicines": [
        {
            "name": "Paracetamol",
            "dose": "500 mg",
            "frequency": "twice daily",
            "duration": "5 days"
        }
    ]
}

Rules:
- If unclear, keep best guess but do not fabricate too many medicines.
- Use "not specified" for missing fields.
- Do not return markdown or extra explanation.
"""


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


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
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Identify the food items in this image and estimate calories for each."
                        },
                        {
                            "type": "text",
                            "text": (
                                "No user description was provided."
                                if not hint_text
                                else f"User food description: {hint_text}. Prefer this hint when image is ambiguous."
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

        raw = response.choices[0].message.content.strip()

        # Remove markdown fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]

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

    except Exception as e:
        # 🔥 FAIL SAFE: never crash the app
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
    location: str | None = None,
) -> List[Dict]:
    """
    Sends a prescription image to GPT-4o Vision and returns extracted medicines.
    """

    try:
        client = get_openai_client()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        location_text = (location or "").strip()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PRESCRIPTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all medicines from this prescription image."
                        },
                        {
                            "type": "text",
                            "text": (
                                "Location context not provided."
                                if not location_text
                                else f"Location context for pricing: {location_text}"
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
            max_tokens=700,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]

        data = json.loads(raw)
        medicines = data.get("medicines", [])
        if not isinstance(medicines, list):
            raise ValueError("Invalid medicines format from OpenAI")

        normalized: List[Dict] = []
        for med in medicines:
            if not isinstance(med, dict):
                continue
            name = str(med.get("name", "Unknown medicine")).strip()
            dose = str(med.get("dose", "not specified")).strip()
            frequency = str(med.get("frequency", "not specified")).strip()
            duration = str(med.get("duration", "not specified")).strip()
            if not name:
                continue
            normalized.append(
                {
                    "name": name,
                    "dose": dose,
                    "frequency": frequency,
                    "duration": duration,
                }
            )

        return normalized

    except Exception:
        return []
