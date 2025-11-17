
from pydantic import BaseModel
from database.linkedin_context import clear_linkedin_context
from typing import List
from fastapi import APIRouter

logout_route = APIRouter()

class LogoutReq(BaseModel):
    user_id: str

@logout_route.delete("/logout")
async def logout_context(request: LogoutReq):
    # if linkedin_login_context == None:
    #     return {"status": "success", "message": "context is empty no need to log out"}
    # await clear_login_context()
    if clear_linkedin_context(request.user_id):
        return {"status": "success", "message": "Logged out successfully"}
    else:
        return {"status": "Failed", "message": "Log out failed"}
