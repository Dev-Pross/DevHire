import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl, field_serializer
from typing import List, Dict, Any, Optional
from agents.scraper_agent import run_scraper_in_new_loop  
from concurrent.futures import ThreadPoolExecutor 
from main.progress_dict import job_progress
from agents import parse_agent
import logging
import json
import queue as thread_queue

class JobRequest(BaseModel):
    user_id: Optional[str] = None
    file_url: str
    password: Optional[str] = None
    progress_user: str

class Job(BaseModel):
    title: Optional[str] = "Title not available"  # Allow None with default
    job_id: Optional[Any] = "ID not available"    # Make this optional too
    company_name: Optional[Any] = None
    location: Optional[Any] = None
    experience: Optional[Any] = None
    salary: Optional[Any] = None
    key_skills: List[Any] = []                     # Default to empty list
    job_url: HttpUrl
    posted_at: Optional[Any] = None
    job_description: str = "Description not available"  # Provide default
    source: str = "linkedin"                       # Default value
    relevance_score: Optional[Any] = "unknown"     # Make optional with default

class ResponseJob(BaseModel):
    jobs: List[Job]
    total: int

router = APIRouter()

@router.get('/get-jobs')
async def get_job_stream(
    file_url: str,
    progress_user: str,
    user_id: Optional[str] = None,
    password: Optional[str] = None,
):
    async def event_stream():
        pq = thread_queue.Queue()
        try:
            yield f"data: {json.dumps({'progress': 1, 'status': 'processing...', 'message': 'Analyzing your resume...'})}\n\n"

            loop = asyncio.get_running_loop()
            title_keywords = await loop.run_in_executor(None, parse_agent.main, file_url)

            if (not title_keywords 
                or not isinstance(title_keywords, (list, tuple)) 
                or len(title_keywords) < 2 
                or not all(title_keywords)
            ):
                yield f"data: {json.dumps({"progress": 100, 'jobs': [], 'total': 0, 'message': 'No matching job titles found in resume'})}\n\n"
                return
            
            titles_string = title_keywords[0]
            keywords_string = title_keywords[1]

            titles = [title.strip() for title in titles_string.split(',')]
            keywords = [keyword.strip() for keyword in keywords_string.split(',')]

            yield f"data: {json.dumps({'progress': 8, 'status': 'processing...', 'message': f'Identified {len(titles)} matching roles'})}\n\n"
            yield f"data: {json.dumps({'progress': 10, 'status': 'searching....', 'message': f'Searching LinkedIn for: {', '.join(titles[:3])}...'})}\n\n"

            with ThreadPoolExecutor(max_workers=1) as executor:
                scraper_future = loop.run_in_executor(
                    executor,
                    run_scraper_in_new_loop,
                    titles,
                    keywords,
                    pq,
                    user_id,
                    password,
                    progress_user
                )

                done = False
                while not done:
                    if scraper_future.done():
                        done = True

                    while True:
                        try:
                            update = pq.get_nowait()
                            status = update.get('status')

                            if status == 'batch_ready':
                                valid_batch = []
                                for job in update.get('jobs', []):
                                    try:
                                        valid_batch.append(Job(**job).model_dump(mode='json'))
                                    except Exception as e:
                                        logging.warning(f"Skipping malformed job: {e}")
                                yield f"data: {json.dumps({'progress': update['progress'], 'status': 'batch_ready', 'batch_num': update['batch_num'], 'total_batches': update['total_batches'], 'jobs': valid_batch, 'message': update['message']})}\n\n"

                            elif status == 'done':
                                yield f"data: {json.dumps({'progress': 100, 'status': 'done', 'total': update.get('total', 0), 'message': update.get('message', 'Done!')})}\n\n"
                                return

                            elif status == 'error' or update.get('progress') == -1:
                                yield f"data: {json.dumps({'progress': -1, 'status': 'error', 'message': update.get('message', 'Error')})}\n\n"
                                return

                            else:
                                yield f"data: {json.dumps(update)}\n\n"

                        except thread_queue.Empty:
                            break

                        if not done:
                            await asyncio.sleep(0.1)
                
                # fallback only if pq never sent 'done' (shouldn't happen after fixes)
                jobs = await scraper_future
                if jobs:
                    job_data = []
                    for job in jobs:
                        try:
                            job_data.append(Job(**job).model_dump(mode='json'))
                        except Exception as e:
                            logging.warning(f"Skipping malformed job: {e}")
                    yield f"data: {json.dumps({'progress': 100, 'status': 'done', 'jobs': job_data, 'total': len(job_data), 'message': f'Found {len(job_data)} jobs!'})}\n\n"
                else:
                    yield f"data: {json.dumps({'progress': 100, 'status': 'done', 'jobs': [], 'total': 0, 'message': 'No jobs found'})}\n\n"


        except Exception as e:
            logging.error(f"get-jobs stream error: {e}")
            yield f"data: {json.dumps({'progress': -1, 'error': str(e)})}\n\n"
        
    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
