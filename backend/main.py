"""
main.py — FastAPI entry point for AI Health Risk & Lifestyle Companion.
Mounts all routers and configures CORS for the Next.js frontend.
"""

from dotenv import load_dotenv
load_dotenv()  # ✅ MUST be first

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import food, travel, user, prescription

app = FastAPI(
    title="AI Health Risk & Lifestyle Companion",
    version="0.1.0",
)

# Allow the Next.js dev server and common origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(food.router, prefix="/api")
app.include_router(travel.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(prescription.router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "AI Health Companion API"}
