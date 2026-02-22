"""
food.py — POST /api/analyze-food-image
Accepts an uploaded image + optional health profile, returns food analysis.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import json
from typing import Optional

from models.schemas import HealthProfile, FoodItem, FoodAnalysisResponse
from services.vision_service import analyze_food_image
from services.nutrition_service import evaluate_food_item

router = APIRouter(tags=["Food Analysis"])


@router.post("/analyze-food-image", response_model=FoodAnalysisResponse)
async def analyze_food(
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),  # allows frontend to send "file"
    health_profile: str = Form(default='{"conditions":[],"allergies":[]}'),
    food_hint: Optional[str] = Form(default=None),
):
    """
    1. Accept uploaded image (image OR file field)
    2. Send to OpenAI Vision → detect food items
    3. Evaluate each item using nutrition rule engine
    4. Return structured response
    """

    # 🔹 Support both "image" and "file"
    upload = image or file
    if not upload:
        raise HTTPException(status_code=400, detail="No image file provided")

    try:
        image_bytes = await upload.read()
        mime = upload.content_type or "image/jpeg"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    # 🔹 Parse health profile safely
    try:
        parsed_profile = json.loads(health_profile)
        health = HealthProfile(**parsed_profile)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid health_profile JSON")

    normalized_food_hint = food_hint.strip() if isinstance(food_hint, str) else None
    if normalized_food_hint == "":
        normalized_food_hint = None

    # 🔹 Step 1: Vision AI — detect foods
    try:
        detected_items = await analyze_food_image(image_bytes, mime, normalized_food_hint)
    except Exception:
        detected_items = [
            {
                "name": "Unknown food",
                "ingredients": [],
                "estimated_calories": 250,
            }
        ]

    # 🔹 Step 2: Rule engine — evaluate each item
    evaluated: list[FoodItem] = []
    for item in detected_items:
        item_name = str(item.get("name", "Unknown food"))
        item_calories = int(item.get("estimated_calories", 250) or 250)
        item_ingredients = item.get("ingredients", [])
        if not isinstance(item_ingredients, list):
            item_ingredients = []

        evaluated.append(
            evaluate_food_item(
                item_name,
                item_calories,
                item_ingredients,
                health,
            )
        )

    total_cal = sum(i.estimated_calories for i in evaluated)

    # 🔹 Friendly explanation builder
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
