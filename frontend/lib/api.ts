/**
 * lib/api.ts — Thin wrapper around fetch calls to the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/** POST /analyze — unified image analysis (food or prescription) */
export async function analyzeImage(
  imageFile: File,
  healthProfile: object,
  userMessage?: string
) {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("health_profile", JSON.stringify(healthProfile));
  if (userMessage && userMessage.trim().length > 0) {
    form.append("user_message", userMessage.trim());
  }

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);
  return res.json();
}

/** POST /analyze-food-image — multipart form with image + health profile JSON */
export async function analyzeFoodImage(
  imageFile: File,
  healthProfile: object,
  foodHint?: string
) {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("health_profile", JSON.stringify(healthProfile));
  if (foodHint && foodHint.trim().length > 0) {
    form.append("food_hint", foodHint.trim());
  }

  const res = await fetch(`${API_BASE}/analyze-food-image`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) throw new Error(`Food analysis failed: ${res.statusText}`);
  return res.json();
}

/** POST /travel-risk — JSON body */
export async function assessTravelRisk(
  activity: string,
  details: string,
  healthProfile: object
) {
  const res = await fetch(`${API_BASE}/travel-risk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      activity,
      details,
      health: healthProfile,
    }),
  });

  if (!res.ok) throw new Error(`Travel risk failed: ${res.statusText}`);
  return res.json();
}
