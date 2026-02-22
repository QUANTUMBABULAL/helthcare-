"""
schemas.py — Pydantic models shared across routers and services.
"""

from pydantic import BaseModel
from typing import Optional, Literal, Dict


# ---------- User / Health Profile ----------

class HealthProfile(BaseModel):
    """Subset of user health data sent with each request."""
    conditions: list[str] = []          # e.g. ["diabetes", "hypertension"]
    allergies: list[str] = []           # e.g. ["peanuts", "gluten"]
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    medications: list[str] = []


class UserProfile(BaseModel):
    """Full user profile stored in Supabase."""
    id: Optional[str] = None
    name: str
    email: str
    health: HealthProfile


# ---------- Food Analysis ----------

class FoodItem(BaseModel):
    name: str
    ingredients: list[str]
    estimated_calories: int
    verdict: Literal["OK", "LIMIT", "AVOID"]
    reason: str


class FoodAnalysisResponse(BaseModel):
    items: list[FoodItem]
    total_calories: int
    explanation: str        # friendly summary


# ---------- Prescription Analysis ----------

class MedicineItem(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str


class PrescriptionResult(BaseModel):
    medicines: list[MedicineItem]
    safety_warnings: list[str]
    cost_estimate: Dict[str, float]   # medicine_name → estimated price (USD)
    ocr_text: str
    explanation: str


# ---------- Unified Analyze ----------

class AnalyzeResponse(BaseModel):
    analysis_type: Literal["food", "prescription", "unknown"]
    food_result: Optional[FoodAnalysisResponse] = None
    prescription_result: Optional[PrescriptionResult] = None
    explanation: str


# ---------- Travel / Activity Risk ----------

class TravelRiskRequest(BaseModel):
    activity: str           # e.g. "flying", "scuba diving", "long drive"
    details: Optional[str] = None
    health: HealthProfile


class TravelRiskResponse(BaseModel):
    activity: str
    risk_level: str         # LOW | MODERATE | HIGH
    advice: list[str]
    explanation: str
