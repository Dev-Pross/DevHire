
from main.progress_dict import clear_login_context, linkedin_login_context
from typing import List
from fastapi import APIRouter

logout_route = APIRouter()

@logout_route.delete("/logout")
async def logout_context():
    # if linkedin_login_context == None:
    #     return {"status": "success", "message": "context is empty no need to log out"}
    await clear_login_context()
    return {"status": "success", "message": "Logged out successfully"}