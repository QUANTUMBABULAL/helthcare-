"""
risk_engine.py — Evaluates travel / activity risk based on user health profile.

Combines:
  1. Rule-based checks (deterministic safety layer)
  2. OpenAI text reasoning (nuanced explanation)
"""

import os
import json
from openai import OpenAI
from models.schemas import HealthProfile, TravelRiskResponse

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Rule-based risk matrix ----
# Maps (condition, activity_keyword) → (risk_level, advice)

RISK_RULES: list[tuple[str, list[str], str, str]] = [
    # (condition, activity_keywords, risk_level, advice)
    ("asthma", ["fly", "flight", "airplane", "plane", "altitude"],
     "MODERATE", "Cabin pressure changes may trigger symptoms. Carry your inhaler on board."),
    ("asthma", ["diving", "scuba", "snorkel"],
     "HIGH", "Scuba diving with asthma carries serious risk of air trapping. Consult a dive physician."),
    ("heart disease", ["fly", "flight", "airplane", "plane"],
     "MODERATE", "Flying is generally safe if stable, but consult your cardiologist before long-haul flights."),
    ("heart disease", ["diving", "scuba"],
     "HIGH", "Scuba diving places extreme cardiovascular stress. Strongly discouraged."),
    ("heart disease", ["hiking", "trek", "altitude", "mountain"],
     "HIGH", "High-altitude exertion with heart disease is dangerous. Avoid strenuous trekking."),
    ("hypertension", ["fly", "flight", "airplane"],
     "LOW", "Flying is usually fine. Stay hydrated and move regularly during the flight."),
    ("hypertension", ["diving", "scuba"],
     "MODERATE", "Diving can spike blood pressure. Get medical clearance first."),
    ("diabetes", ["long drive", "road trip", "driving"],
     "MODERATE", "Risk of hypoglycemia. Carry snacks, check blood sugar frequently, take breaks."),
    ("diabetes", ["fly", "flight", "airplane"],
     "LOW", "Flying is safe. Adjust insulin for time zone changes and carry supplies in carry-on."),
    ("epilepsy", ["driving", "long drive", "road trip"],
     "HIGH", "Seizure risk while driving is life-threatening. Check local driving regulations and seizure-free period."),
    ("epilepsy", ["diving", "scuba"],
     "HIGH", "Seizure underwater is fatal. Scuba diving is strongly contraindicated."),
    ("dvt", ["fly", "flight", "airplane", "long drive"],
     "HIGH", "Prolonged immobility increases clot risk. Wear compression stockings, move frequently."),
    ("pregnancy", ["fly", "flight", "airplane"],
     "MODERATE", "Generally safe before 36 weeks. Check airline policy and consult your OB-GYN."),
    ("pregnancy", ["diving", "scuba"],
     "HIGH", "Diving is contraindicated during pregnancy due to fetal decompression risk."),
]


def _rule_based_check(activity: str, health: HealthProfile) -> tuple[str, list[str]]:
    """Return the highest risk level and collected advice from deterministic rules."""
    activity_lower = activity.lower()
    conditions = [c.lower() for c in health.conditions]

    risk_priority = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
    highest_risk = "LOW"
    advice_list: list[str] = []

    for condition, keywords, risk, advice in RISK_RULES:
        if condition in conditions and any(kw in activity_lower for kw in keywords):
            if risk_priority[risk] > risk_priority[highest_risk]:
                highest_risk = risk
            advice_list.append(advice)

    return highest_risk, advice_list


async def evaluate_travel_risk(activity: str, details: str | None, health: HealthProfile) -> TravelRiskResponse:
    """Combine rule-based check with AI reasoning."""
    rule_risk, rule_advice = _rule_based_check(activity, health)

    # Build AI prompt for a richer explanation
    profile_summary = (
        f"Conditions: {', '.join(health.conditions) or 'none'}. "
        f"Allergies: {', '.join(health.allergies) or 'none'}. "
        f"Medications: {', '.join(health.medications) or 'none'}. "
        f"Age: {health.age or 'unknown'}."
    )

    prompt = (
        f"A user wants to do this activity: {activity}.\n"
        f"Additional details: {details or 'none'}.\n"
        f"Health profile: {profile_summary}\n\n"
        f"Our rule engine flagged risk as {rule_risk} with advice: {'; '.join(rule_advice) if rule_advice else 'none'}.\n\n"
        "Provide a concise, empathetic explanation (2-4 sentences) about why this activity "
        "carries that risk level for this user. Do NOT diagnose. Frame it as risk-awareness, "
        "not medical advice. Encourage consulting a doctor for personalized guidance."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a health-risk awareness assistant. You do NOT diagnose. You provide general safety guidance only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.4,
        )
        explanation = response.choices[0].message.content.strip()
    except Exception:
        explanation = (
            f"Based on your health profile, this activity is rated {rule_risk} risk. "
            "Please consult your doctor for personalized advice."
        )

    # If rules found nothing specific, default advice
    if not rule_advice:
        rule_advice = ["No specific risks identified. General precautions apply — stay hydrated and listen to your body."]

    return TravelRiskResponse(
        activity=activity,
        risk_level=rule_risk,
        advice=rule_advice,
        explanation=explanation,
    )
