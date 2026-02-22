"""
prescription.py — POST /api/analyze-prescription
Accepts a prescription image and returns extracted medicines + safety recheck.
"""

import json
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models.schemas import (
    HealthProfile,
    PrescriptionMedicineExtract,
    PrescriptionAnalysisResponse,
)
from services.vision_service import analyze_prescription_image
from services.prescription_service import evaluate_prescription

router = APIRouter(tags=["Prescription Recheck"])


@router.post("/analyze-prescription", response_model=PrescriptionAnalysisResponse)
async def analyze_prescription(
    image: Optional[UploadFile] = File(None),
    health_profile: Optional[str] = Form(default='{"conditions":[],"allergies":[]}'),
    location: Optional[str] = Form(default=None),
):
    upload = image
    if not upload:
        raise HTTPException(status_code=400, detail="No prescription image provided")

    try:
        image_bytes = await upload.read()
        mime = upload.content_type or "image/jpeg"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    try:
        profile_payload = json.loads(health_profile or '{"conditions":[],"allergies":[]}')
        health = HealthProfile(**profile_payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid health_profile JSON")

    try:
        extracted_raw = await analyze_prescription_image(image_bytes, mime, location)
    except Exception:
        extracted_raw = []

    extracted: list[PrescriptionMedicineExtract] = []
    for med in extracted_raw:
        try:
            extracted.append(PrescriptionMedicineExtract(**med))
        except Exception:
            continue

    try:
        return evaluate_prescription(extracted, health, location)
    except Exception:
        return PrescriptionAnalysisResponse(
            medicines=[],
            total_estimated_cost=0.0,
            warnings=["Unable to process prescription safely right now."],
            disclaimer="This does not replace professional medical advice.",
        )
