import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
from agents.scraper_agent import run_scraper_in_new_loop  
from concurrent.futures import ThreadPoolExecutor 
from main.progress_dict import job_progress
from agents import parse_agent
import os
import json

class JobRequest(BaseModel):
    user_id: str
    file_url: str
    password: str

class Job(BaseModel):
    title: Optional[str] = "Title not available"  # Allow None with default
    job_id: Optional[str] = "ID not available"    # Make this optional too
    company_name: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[str] = None
    salary: Optional[str] = None
    key_skills: List[str] = []                     # Default to empty list
    job_url: HttpUrl
    posted_at: Optional[str] = None
    job_description: str = "Description not available"  # Provide default
    source: str = "linkedin"                       # Default value
    relevance_score: Optional[str] = "unknown"     # Make optional with default

class ResponseJob(BaseModel):
    jobs: List[Job]
    total: int

router = APIRouter()

@router.post("/get-jobs", response_model=ResponseJob)
async def getJobs(request: JobRequest):
    

    try:

        title_keywords = parse_agent.main(request.user_id, request.file_url)
        if not title_keywords or not all(title_keywords):
            return ResponseJob(
                content={"jobs": [], "total": 0},
                status_code=200
    )
        
        titles_string = title_keywords[0]
        keywords_string = title_keywords[1]
        
        titles = [title.strip() for title in titles_string.split(",")]
        keywords = [keyword.strip() for keyword in keywords_string.split(",")]
        keywords.append('web developer')
        keywords.append("software Developer")
        keywords.append("full stack")


        print(titles,"\n", keywords)
        job_progress[request.user_id] = 10
         # Run scraper in separate thread with new event loop
        with ThreadPoolExecutor(max_workers=1) as executor:
            jobs = await asyncio.get_event_loop().run_in_executor(
                executor,
                run_scraper_in_new_loop,
                titles,  # Pass the string directly
                keywords,  # Pass the string directly
                job_progress,
                request.user_id,
                request.password
            )
        
        if not jobs:
            return ResponseJob(jobs=[],total=0)
        
        job_data=[]
        for job in jobs:
            try:
                j = Job(**job)
                job_data.append(j)
            except Exception as e:
                print(f"Error creating job model: {e}")
                continue

        return ResponseJob(jobs=job_data,total=len(job_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing jobs: {str(e)}")