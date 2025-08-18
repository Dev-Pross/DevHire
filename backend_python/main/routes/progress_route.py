from fastapi import APIRouter
from main.progress_dict import job_progress  # Import your shared dictionary

progress_router = APIRouter()

@progress_router.get("/jobs/{job_id}/progress")
def get_job_progress(job_id: str):
    percent = job_progress.get(job_id, 0)
    return {"progress": percent}
