import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .database import init_db
from .jobs import create_job, get_job, get_workshop_cache
from .models import JobCreate, JobResponse
from .worker import job_queue, start_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker = asyncio.create_task(start_worker())
    yield
    worker.cancel()


app = FastAPI(title="Zomboid Mod Extractor", lifespan=lifespan)


@app.post("/jobs", response_model=JobResponse, status_code=202)
async def submit_job(data: JobCreate):
    """Submit workshop IDs for processing. Returns a job ID to poll for progress."""
    if not data.workshop_ids:
        raise HTTPException(status_code=400, detail="workshop_ids must not be empty")
    job = await create_job(data.workshop_ids)
    await job_queue.put(job["id"])
    return job


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Poll job progress. status: pending → processing → completed / failed"""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/workshop/{workshop_id}")
async def get_workshop(workshop_id: str):
    """Get cached mod info for a workshop item."""
    data = await get_workshop_cache(workshop_id)
    if not data:
        raise HTTPException(status_code=404, detail="Workshop item not in cache")
    return data
