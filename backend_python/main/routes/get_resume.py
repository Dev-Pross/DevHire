import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
from agents.tailor import process_batch as tailor_main

class TailorRequest(BaseModel):
    job_desc: str
    resume_url: HttpUrl

class TailorResponses(BaseModel):
    success: bool
    payload: List[str]
    media: str

router = APIRouter()

@router.post("/tailor",response_model=TailorResponses)
def tailor_resume(request: TailorRequest):
    try:
        resume_data = [{"job_url": "resume_", "job_description": request.job_desc}]
        # logging.info("resumedata: %s",resume_data)
        resume = tailor_main(request.resume_url, resume_data)
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
