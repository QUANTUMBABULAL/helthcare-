import re
from typing import Dict, List

from models.schemas import (
    HealthProfile,
    PrescriptionMedicineExtract,
    PrescriptionMedicineResult,
    PrescriptionAnalysisResponse,
)


DISCLAIMER_TEXT = "This does not replace professional medical advice."


BRAND_TO_ACTIVE: Dict[str, str] = {
    "dolo": "paracetamol",
    "crocin": "paracetamol",
    "calpol": "paracetamol",
    "tylenol": "paracetamol",
    "combiflam": "ibuprofen",
    "advil": "ibuprofen",
    "brufen": "ibuprofen",
    "azithral": "azithromycin",
    "augmentin": "amoxicillin",
    "allegra": "fexofenadine",
    "cetcip": "cetirizine",
}

MOCK_UNIT_PRICE: Dict[str, float] = {
    "paracetamol": 2.0,
    "ibuprofen": 3.5,
    "amoxicillin": 9.0,
    "azithromycin": 15.0,
    "metformin": 4.0,
    "cetirizine": 2.5,
    "fexofenadine": 7.0,
    "omeprazole": 5.0,
    "pantoprazole": 6.0,
    "default": 6.0,
}

PREGNANCY_CAUTION_ACTIVES = {
    "ibuprofen",
    "warfarin",
    "isotretinoin",
    "aceclofenac",
}

HIGH_DOSE_LIMITS_MG: Dict[str, int] = {
    "paracetamol": 650,
    "ibuprofen": 400,
    "metformin": 1000,
    "amoxicillin": 875,
}


def _normalize_name(name: str) -> str:
    clean = re.sub(r"[^a-z0-9\s]", " ", (name or "").lower()).strip()
    return re.sub(r"\s+", " ", clean)


def _active_ingredient(name: str) -> str:
    normalized = _normalize_name(name)
    if not normalized:
        return "unknown"
    first_token = normalized.split(" ")[0]
    return BRAND_TO_ACTIVE.get(first_token, first_token)


def _extract_mg(dose: str) -> int | None:
    match = re.search(r"(\d+)\s*mg", (dose or "").lower())
    if not match:
        return None
    return int(match.group(1))


def _frequency_per_day(freq: str) -> int:
    text = (freq or "").lower()
    if "once" in text or "daily" in text or "od" in text:
        return 1
    if "twice" in text or "bid" in text or "2" in text and "day" in text:
        return 2
    if "thrice" in text or "tid" in text or "3" in text and "day" in text:
        return 3
    if "four" in text or "qid" in text or "4" in text and "day" in text:
        return 4
    return 1


def _duration_days(duration: str) -> int:
    text = (duration or "").lower()
    day_match = re.search(r"(\d+)\s*day", text)
    if day_match:
        return max(int(day_match.group(1)), 1)
    week_match = re.search(r"(\d+)\s*week", text)
    if week_match:
        return max(int(week_match.group(1)) * 7, 1)
    return 5


def _estimate_cost(active: str, frequency: str, duration: str, location: str | None) -> float:
    unit_price = MOCK_UNIT_PRICE.get(active, MOCK_UNIT_PRICE["default"])
    regional_multiplier = 1.1 if (location or "").strip() else 1.0
    qty = _frequency_per_day(frequency) * _duration_days(duration)
    return round(unit_price * qty * regional_multiplier, 2)


def evaluate_prescription(
    extracted: List[PrescriptionMedicineExtract],
    health: HealthProfile,
    location: str | None,
) -> PrescriptionAnalysisResponse:
    conditions = [c.lower() for c in health.conditions]
    allergies = [a.lower() for a in health.allergies]

    seen_names: set[str] = set()
    seen_active_to_brand: Dict[str, str] = {}
    global_warnings: List[str] = []
    results: List[PrescriptionMedicineResult] = []

    for med in extracted:
        name = (med.name or "Unknown medicine").strip()
        dose = (med.dose or "not specified").strip()
        frequency = (med.frequency or "once daily").strip()
        duration = (med.duration or "5 days").strip()

        norm_name = _normalize_name(name)
        active = _active_ingredient(name)

        warning_level = "OK"
        reasons: List[str] = ["No immediate rule-based issue found."]

        if norm_name in seen_names:
            warning_level = "CAUTION"
            reasons = ["Duplicate medicine appears in prescription."]
            global_warnings.append(f"Duplicate detected: {name}")
        seen_names.add(norm_name)

        if active in seen_active_to_brand and seen_active_to_brand[active] != norm_name:
            warning_level = "CAUTION" if warning_level == "OK" else warning_level
            reasons = [f"Possible same drug under different brand names ({active})."]
            global_warnings.append(
                f"Potential brand duplication: {name} and {seen_active_to_brand[active]}"
            )
        else:
            seen_active_to_brand[active] = norm_name

        allergy_hit = next((a for a in allergies if a and (a in norm_name or a in active)), None)
        if allergy_hit:
            warning_level = "AVOID"
            reasons = [f"Allergy conflict detected: {allergy_hit}."]
            global_warnings.append(f"Allergy conflict for {name}: {allergy_hit}")

        if "pregnancy" in conditions and active in PREGNANCY_CAUTION_ACTIVES:
            if warning_level != "AVOID":
                warning_level = "CAUTION"
            reasons = ["Use in pregnancy may require doctor confirmation."]
            global_warnings.append(f"Pregnancy caution: {name}")

        dose_mg = _extract_mg(dose)
        dose_limit = HIGH_DOSE_LIMITS_MG.get(active)
        if dose_mg is not None and dose_limit is not None and dose_mg > dose_limit:
            warning_level = "CAUTION" if warning_level == "OK" else warning_level
            reasons = [f"Dose appears high ({dose_mg} mg) for {active}."]
            global_warnings.append(f"High dose warning: {name} ({dose_mg} mg)")

        estimated_cost = _estimate_cost(active, frequency, duration, location)

        results.append(
            PrescriptionMedicineResult(
                name=name,
                dose=dose,
                frequency=frequency,
                duration=duration,
                warning_level=warning_level,
                warning_reason=" ".join(reasons),
                estimated_cost=estimated_cost,
            )
        )

    total_cost = round(sum(m.estimated_cost for m in results), 2)

    if not global_warnings and results:
        global_warnings.append("No major rule-based conflicts detected.")
    if not results:
        global_warnings.append("Could not reliably extract medicines from the image.")

    return PrescriptionAnalysisResponse(
        medicines=results,
        total_estimated_cost=total_cost,
        warnings=global_warnings,
        disclaimer=DISCLAIMER_TEXT,
    )
