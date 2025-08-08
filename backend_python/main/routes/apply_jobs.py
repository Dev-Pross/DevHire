from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any
import asyncio
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import tempfile
import os

# Import your existing modules
from agents.tailor import process_batch
from agents.apply_agent import main as applier_main  # Your async main function from index.py

class JobApplication(BaseModel):
    job_url: HttpUrl
    job_description: str

class ApplyJobRequest(BaseModel):
    user_id: str
    password: str
    resume_url: HttpUrl
    jobs: List[JobApplication]

class ApplyJobResponse(BaseModel):
    success: bool
    total_jobs: int
    successful_applications: int
    failed_applications: int
    message: str

router = APIRouter()

def run_applier_in_new_loop(applications, user_id=None, password=None):
    """Run applier in a new event loop - same pattern as your list_jobs.py"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(applier_main(applications,user_id,password))
            return result
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Applier error: {e}")
        return {"applied": 0, "failed": len(applications), "success_rate": 0}

@router.post("/apply-jobs", response_model=ApplyJobResponse)
async def apply_jobs_route(request: ApplyJobRequest):
    """
    Apply to jobs with tailored resumes - using same pattern as list_jobs.py
    """
    
    try:
        logging.info(f"Processing {len(request.jobs)} job applications for user {request.user_id}")
        
        # Step 1: Prepare jobs data for resume tailoring
        jobs_data = []
        for job in request.jobs:
            jobs_data.append({
                "job_url": str(job.job_url),
                "job_description": job.job_description
            })
        
        # Step 2: Process batches and apply sequentially (like your original approach)
        batch_size = 15
        total_applied = 0
        total_failed = 0
        
        for i in range(0, len(jobs_data), batch_size):
            batch_jobs = jobs_data[i:i+batch_size]
            batch_number = i//batch_size + 1
            
            logging.info(f"Processing batch {batch_number}: jobs {i+1}-{min(i+batch_size, len(jobs_data))}")
            
            # Tailor resumes for this batch
            tailored_batch = process_batch(str(request.resume_url), batch_jobs)
            logging.info(f"Batch {batch_number} tailored: {len(tailored_batch)} jobs")
            
            # Apply to jobs using ThreadPoolExecutor (same pattern as list_jobs.py)
            logging.info(f"Applying to {len(tailored_batch)} jobs from batch {batch_number}")
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                batch_results = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    run_applier_in_new_loop,
                    tailored_batch,
                    request.user_id,
                    request.password
                )
            
            # Accumulate results
            if isinstance(batch_results, dict):
                total_applied += batch_results.get('applied', 0)
                total_failed += batch_results.get('failed', 0)
                logging.info(f"Batch {batch_number} results: {batch_results.get('applied', 0)} applied, {batch_results.get('failed', 0)} failed")
            else:
                # If applier returns just a count
                applied_count = batch_results if batch_results else 0
                total_applied += applied_count
                total_failed += len(tailored_batch) - applied_count
                logging.info(f"Batch {batch_number} results: {applied_count} applied")
            
            # Sleep between batches (except for last batch)
            if i + batch_size < len(jobs_data):
                logging.info("Pause 30s before next batch")
                time.sleep(30)
        
        success_rate = round((total_applied / len(jobs_data)) * 100, 2) if jobs_data else 0
        
        return ApplyJobResponse(
            success=True,
            total_jobs=len(request.jobs),
            successful_applications=total_applied,
            failed_applications=total_failed,
            message=f"Applied to {total_applied} out of {len(request.jobs)} jobs successfully. Success rate: {success_rate}%"
        )
        
    except Exception as e:
        logging.error(f"Error in apply_jobs_route: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing job applications: {str(e)}"
        )
