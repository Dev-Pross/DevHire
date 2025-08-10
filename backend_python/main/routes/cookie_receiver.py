from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import json

router = APIRouter()

class CookieData(BaseModel):
    name: str
    value: str
    domain: str
    path: str
    secure: bool
    httpOnly: bool
    sameSite: str

class MultipleCookiesPayload(BaseModel):
    cookies: List[CookieData]
    timestamp: int
    total_cookies: int
    localStorage: Dict[str, Any] = {}
    sessionStorage: Dict[str, Any] = {}

@router.post("/api/store-cookie")
async def store_cookies(payload: MultipleCookiesPayload):
    try:
        os.makedirs("/data_dump", exist_ok=True)
        # Save cookies to file
        cookies_dict = {cookie.name: cookie.value for cookie in payload.cookies}
        with open(f"data_dump/cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies_dict, f, indent=2)
        # Save localStorage
        with open(f"data_dump/localStorage.json", "w", encoding="utf-8") as f:
            json.dump(payload.localStorage or {}, f, indent=2)
        # Save sessionStorage
        with open(f"data_dump/sessionStorage.json", "w", encoding="utf-8") as f:
            json.dump(payload.sessionStorage or {}, f, indent=2)
        return {"status": "success", "total_cookies": payload.total_cookies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store cookies/storage: {e}")