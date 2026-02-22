"""
nutrition_service.py — Applies health-condition rules to detected food items.

This is the rule-based safety layer:
  - Diabetes + high-sugar food  → AVOID
  - Hypertension + salty food   → LIMIT
  - Heart disease + fried food  → AVOID
  - Allergy match               → AVOID

A real product would call an external Nutrition API for macros;
here we use keyword heuristics (clearly mocked).
"""

from models.schemas import HealthProfile, FoodItem

# ---- keyword lists (simplified heuristics) ----

HIGH_SUGAR_KEYWORDS = [
    "cake", "candy", "chocolate", "cookie", "donut", "ice cream",
    "pastry", "soda", "syrup", "sugar", "sweet", "dessert", "pie",
    "brownie", "muffin", "waffle", "pancake", "jam", "jelly",
]

HIGH_SALT_KEYWORDS = [
    "chips", "fries", "pickle", "bacon", "sausage", "salami",
    "pretzel", "ramen", "soy sauce", "cured", "smoked", "jerky",
    "salted", "pizza", "burger", "hot dog", "fast food",
]

FRIED_KEYWORDS = [
    "fried", "deep-fried", "tempura", "fritter", "crispy",
    "nugget", "samosa", "pakora", "bhaji",
]

HIGH_FAT_KEYWORDS = [
    "butter", "cream", "cheese", "lard", "mayo", "mayonnaise",
    "oil", "ghee", "fatty",
]


def _matches(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def _matches_any(text_parts: list[str], keywords: list[str]) -> bool:
    return any(_matches(part, keywords) for part in text_parts)


def evaluate_food_item(name: str, calories: int, ingredients: list[str], health: HealthProfile) -> FoodItem:
    """Decide verdict (OK / LIMIT / AVOID) for a single food item."""
    conditions = [c.lower() for c in health.conditions]
    allergies = [a.lower() for a in health.allergies]
    normalized_ingredients = [str(i).strip().lower() for i in (ingredients or []) if str(i).strip()]
    searchable_text = [name.lower(), *normalized_ingredients]

    verdict = "OK"
    reason = "No specific risk identified."

    # --- allergy check (highest priority) ---
    for allergy in allergies:
        if any(allergy in part for part in searchable_text):
            return FoodItem(
                name=name,
                ingredients=normalized_ingredients,
                estimated_calories=calories,
                verdict="AVOID",
                reason=f"Contains allergen: {allergy}",
            )

    # --- condition-based rules ---
    diabetes_risk = _matches_any(searchable_text, ["sugar", "cocoa", "butter"]) or _matches_any(searchable_text, HIGH_SUGAR_KEYWORDS)
    bp_risk = _matches_any(searchable_text, ["salt", "butter"]) or _matches_any(searchable_text, HIGH_SALT_KEYWORDS)
    heart_risk = _matches_any(searchable_text, FRIED_KEYWORDS + HIGH_FAT_KEYWORDS)

    if "diabetes" in conditions and diabetes_risk:
        if calories >= 320 or ("sugar" in normalized_ingredients and "butter" in normalized_ingredients):
            verdict = "AVOID"
            reason = "High sugar/fat profile — risky for diabetes."
        else:
            verdict = "LIMIT"
            reason = "Contains sugar/cocoa/butter — limit portions for diabetes."
    elif ("hypertension" in conditions or "high blood pressure" in conditions) and bp_risk:
        verdict = "LIMIT"
        reason = "Contains salt/butter — may raise blood pressure."
    elif "heart disease" in conditions and heart_risk:
        verdict = "AVOID"
        reason = "High fat / fried — risky for heart disease."
    elif "cholesterol" in conditions and heart_risk:
        verdict = "LIMIT"
        reason = "High fat content — watch cholesterol."
    elif "obesity" in conditions and calories > 400:
        verdict = "LIMIT"
        reason = "High calorie item — consider a smaller portion."

    return FoodItem(
        name=name,
        ingredients=normalized_ingredients,
        estimated_calories=calories,
        verdict=verdict,
        reason=reason,
    )
