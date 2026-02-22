"""
user.py — User profile CRUD via Supabase.
POST /api/user     — create / update profile
GET  /api/user/:id — fetch profile
"""

import os
from fastapi import APIRouter, HTTPException

from models.schemas import UserProfile, HealthProfile

router = APIRouter(tags=["User Profile"])

# ---------- Supabase client (lazy init) ----------

_supabase = None


def _get_supabase():
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            # Fallback: run without Supabase (in-memory store for demo)
            return None
        from supabase import create_client
        _supabase = create_client(url, key)
    return _supabase


# In-memory fallback for hackathon demo when Supabase is not configured
_mem_store: dict[str, dict] = {}


@router.post("/user")
async def upsert_user(profile: UserProfile):
    """Create or update a user profile."""
    sb = _get_supabase()
    payload = profile.model_dump()

    if sb:
        result = sb.table("users").upsert(payload, on_conflict="email").execute()
        return {"status": "saved", "data": result.data}

    # In-memory fallback
    _mem_store[profile.email] = payload
    return {"status": "saved (in-memory)", "data": payload}


@router.get("/user/{email}")
async def get_user(email: str):
    """Fetch a user profile by email."""
    sb = _get_supabase()

    if sb:
        result = sb.table("users").select("*").eq("email", email).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        return result.data[0]

    # In-memory fallback
    if email not in _mem_store:
        raise HTTPException(status_code=404, detail="User not found")
    return _mem_store[email]
