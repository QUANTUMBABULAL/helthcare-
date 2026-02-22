"""
travel.py — POST /api/travel-risk
Accepts an activity + health profile, returns risk assessment.
"""

from fastapi import APIRouter
from models.schemas import TravelRiskRequest, TravelRiskResponse
from services.risk_engine import evaluate_travel_risk

router = APIRouter(tags=["Travel & Activity Risk"])


@router.post("/travel-risk", response_model=TravelRiskResponse)
async def travel_risk(req: TravelRiskRequest):
    """Evaluate travel/activity risk for the user's health profile."""
    return await evaluate_travel_risk(req.activity, req.details, req.health)
