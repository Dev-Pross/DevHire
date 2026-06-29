from fastapi import APIRouter, Request, HTTPException
from database.linkedin_context import get_linkedin_context, save_linkedin_context
from typing import Dict, Any

router = APIRouter()

@router.post("/api/store-cookie")
async def store_cookie(request: Request):
    """
    Receives LinkedIn session data from the Chrome extension.
    If the user doesn't already have context in the DB, it formats the incoming 
    data exactly to match Playwright's expected structure and saves it.
    """
    try:
        data = await request.json()
        
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id in payload")
            
        print(f"Received session data from extension for user: {user_id}")


        # Format cookies mapping expirationDate -> expires for Playwright
        formatted_cookies = []
        for cookie in data.get("cookies", []):
            # Map Chrome's sameSite to Playwright's expected values
            raw_same_site = cookie.get("sameSite", "").lower()
            if raw_same_site == "no_restriction":
                same_site = "None"
            elif raw_same_site == "lax":
                same_site = "Lax"
            elif raw_same_site == "strict":
                same_site = "Strict"
            else:
                same_site = "None"

            formatted_cookie = {
                "name": cookie.get("name"),
                "value": cookie.get("value"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path", "/"),
                "httpOnly": cookie.get("httpOnly", False),
                "secure": cookie.get("secure", False),
                "sameSite": same_site,
            }
            if "expirationDate" in cookie and cookie["expirationDate"] is not None:
                formatted_cookie["expires"] = cookie["expirationDate"]
            elif "expires" in cookie:
                formatted_cookie["expires"] = cookie["expires"]
            else:
                formatted_cookie["expires"] = -1
                
            formatted_cookies.append(formatted_cookie)

        # Format origins strictly (dropping sessionStorage which Playwright rejects)
        formatted_origins = []
        for org in data.get("origins", []):
            formatted_origins.append({
                "origin": org.get("origin"),
                "localStorage": org.get("localStorage", [])
            })

        # Build Playwright formatted payload
        playwright_context = {
            "cookies": formatted_cookies,
            "origins": formatted_origins,
            "fingerprint": data.get("fingerprint", {})
        }

        # Save to database
        save_linkedin_context(user_id, playwright_context)
        print(f"Successfully saved new cross-origin context for {user_id}")
        
        return {"status": "success"}

    except Exception as e:
        print(f"Failed to store cookie payload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
