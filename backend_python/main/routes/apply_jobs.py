import math
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import asyncio
import json
import time
import logging
from concurrent.futures import Executor, ThreadPoolExecutor
from queue import Queue, Empty
import tempfile
import os

# Import your existing modules
from main.progress_dict import apply_progress
from agents.tailor import process_batch
from agents.apply_agent import main as applier_main  # Your async main function from index.py

class JobApplication(BaseModel):
    job_url: HttpUrl
    job_description: str

class ApplyJobRequest(BaseModel):
    user_id: Optional[str] = None
    password: Optional[str] = None
    resume_url: HttpUrl
    jobs: List[JobApplication]
    progress_user: str

class ApplyJobResponse(BaseModel):
    success: bool
    total_jobs: int
    successful_applications: List
    failed_applications: List
    message: str

router = APIRouter()

# apply_jobs.py
def run_applier_in_new_loop(tailored_batch, user_id, password, resume_url, progress_user, pq, total_jobs, jobs_applied_counter):
    # jobs_applied_counter is a list([0]) — mutable ref shared across batches
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            applier_main(tailored_batch, user_id, password, resume_url, progress_user, pq, total_jobs, jobs_applied_counter)
        )
        return result
    finally:
        loop.close()

@router.post('/apply-jobs')
async def apply_jobs_stream(request: ApplyJobRequest):

    pq: Queue = Queue()

    async def event_stream():
        loop = asyncio.get_event_loop()
        total_jobs = len(request.jobs)
        batch_size = 15

        total_applied = []
        total_failed = []
        jobs_applied_counter = [0]


        yield f"data: {json.dumps({'progress': 0, 'status': 'starting', 'message': 'Starting job application...', 'total_jobs': total_jobs})}\n\n"

        jobs_queue: asyncio.Queue = asyncio.Queue()

        async def tailor_producer():

            pq.put({
                    'progress': 5,
                    'status': 'tailoring',
                    'message': f'Tailoring resumes for {total_jobs} jobs...'
                })
            
            for i in range(0, total_jobs, batch_size):
                batch_num = i // batch_size + 1

                batch_jobs = [
                    {
                        'job_url' : str(j.job_url),
                        'job_description': str(j.job_description)
                    }
                    for j in request.jobs[i: i + batch_size]
                ] 


                logging.info(
                    f"Tailoring batch {batch_num}: "
                    f"jobs {i + 1}-{min(i + batch_size, total_jobs)}"
                )

                tailored_batch = await loop.run_in_executor(
                    None,
                    process_batch,
                    str(request.resume_url),
                    batch_jobs
                )

                await jobs_queue.put(( batch_num, tailored_batch ))

            pq.put({
                    'progress': 10,
                    'status': 'tailoring',
                    'message': 'Resumes tailored — starting applications'
                })
            await jobs_queue.put(None)

        executor = ThreadPoolExecutor(max_workers=1) 


        async def applier_consumer():
            
            while True:
                item = await jobs_queue.get()

                if item is None:
                    jobs_queue.task_done()
                    break

                batch_num, tailored_batch = item

                logging.info(
                    f"Applying batch {batch_num} with {len(tailored_batch)} jobs"
                )

                
                batch_result = await loop.run_in_executor(
                    executor,
                    run_applier_in_new_loop,
                    tailored_batch,
                    request.user_id,
                    request.password,
                    str(request.resume_url),
                    request.progress_user,
                    pq,
                    total_jobs, 
                    jobs_applied_counter,
                )

                if isinstance(batch_result, dict):
                    applied_list = batch_result.get('applied', [])
                    failed_list = batch_result.get('failed', [])

                    if not isinstance(applied_list, list):
                        applied_list = []
                    if not isinstance(failed_list, list):
                        failed_list = []
                    
                    total_applied.extend(applied_list)
                    total_failed.extend(failed_list)

                    logging.info(
                        f"Batch {batch_num} done: "
                        f"{len(applied_list)} applied, {len(failed_list)} failed"
                    )
                
                jobs_queue.task_done()
                
        pipeline_task = asyncio.ensure_future(
                asyncio.gather(tailor_producer(), applier_consumer())
            )

        while not pipeline_task.done():
            had_event = False
            while True:
                try:
                    event = pq.get_nowait()
                    yield f"data: {json.dumps(event)}\n\n"
                    had_event = True
                except Empty:
                    break
            # Always yield a keep-alive comment every poll cycle
            # yield ": keep-alive\n\n"   # ← THIS forces a TCP chunk every 0.2s
            await asyncio.sleep(0.2)

        while True:
            try:
                event = pq.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"
                # yield ": keep-alive\n\n"
            except Empty:
                break

        try:
            await pipeline_task
        except Exception as e:
            logging.error(f"Pipeline error: {e}")
            yield f"data: {json.dumps({'progress': 100, 'status': 'error', 'message': str(e)})}\n\n"
            return    
        finally:
            executor.shutdown(wait=True)

        yield f"data: {json.dumps({
            'progress': 100,
            'status': 'done',
            'message': f'Done! Applied to {len(total_applied)}/{total_jobs} jobs.',
            'applied': total_applied,
            'failed': total_failed,
            'total_jobs': total_jobs,
        })}\n\n"


    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    )                
