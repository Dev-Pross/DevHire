import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Dict, Any, Optional
from agents.tailor import process_batch as tailor_main

class TailorRequest(BaseModel):
    job_desc: Optional[str] = None
    resume_url: Optional[HttpUrl] = None
    user_data: Optional[str] = None
    template: int = None
    
    # @field_validator('*', mode='before')
    # @classmethod
    # def check_at_least_one_required(cls, v):
    #     return v
    
    # def __init__(self, **data):
    #     super().__init__(**data)
    #     # Validate that we have valid combinations
    #     has_url = self.resume_url is not None
    #     has_user_data = self.user_data is not None
    #     has_desc = self.job_desc is not None
        
    #     # Valid combinations:
    #     # 1. resume_url + optional job_desc
    #     # 2. user_data + optional job_desc
    #     if not has_url and not has_user_data:
    #         raise ValueError("Must provide either 'resume_url' or 'user_data'")
        
    #     if has_url and has_user_data:
    #         raise ValueError("Cannot provide both 'resume_url' and 'user_data' - use only one")

class TailorResponses(BaseModel):
    success: bool
    payload: List[str]
    media: str

router = APIRouter()

@router.post("/tailor",response_model=TailorResponses)
def tailor_resume(request: TailorRequest):
    try:
        print(f"{request.template} - template from route")
        resume_data = [{"job_url": "resume_", "job_description": request.job_desc or "**MAKE GENERAL RESUME**"}]
        # logging.info("resumedata: %s",resume_data)
        resume = []
        if request.resume_url:
            resume = tailor_main(request.resume_url, resume_data, template=request.template)
        else:
            resume = tailor_main(user_data=request.user_data, jobs=resume_data, template=request.template)
        if resume:
            logging.info("resume generated")
        # Extract just the base64 strings from the returned list for payload
        base64_list = [item["resume_binary"] for item in resume]
        return TailorResponses(
            success=True,
            payload=base64_list,
            media="application/pdf"
        )
    except Exception as e:
        logging.error(f"Error in apply_jobs_route: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing job applications: {str(e)}"
        )
