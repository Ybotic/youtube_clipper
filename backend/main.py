import shutil
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.models import GenerateRequest, JobStatus
from backend.pipeline import run_pipeline
from backend.services.downloader import DownloadError, validate_youtube_url
from backend.settings import settings


app = FastAPI(title="AI Clipper API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()


def _update_job(job_id: str, status: str, message: str, **values: Any) -> None:
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(status=status, message=message, **values)


def _process_job(job_id: str, youtube_url: str) -> None:
    job_dir = settings.temp_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    try:
        clips = run_pipeline(
            job_id,
            youtube_url,
            job_dir,
            settings.output_dir,
            lambda status, message: _update_job(job_id, status, message),
        )
        _update_job(job_id, "finished", "Finished", clips=clips)
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        _update_job(job_id, "failed", "Processing failed", error=str(exc))


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate")
def generate(request: GenerateRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    try:
        validate_youtube_url(request.youtube_url)
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "message": "Queued",
            "clips": [],
            "error": None,
        }
    background_tasks.add_task(_process_job, job_id, request.youtube_url)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}", response_model=JobStatus)
def status(job_id: str) -> JobStatus:
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return JobStatus(**job)


@app.get("/api/clips/{job_id}/{filename}")
def clip_file(job_id: str, filename: str) -> FileResponse:
    if (
        len(job_id) != 32
        or any(character not in "0123456789abcdef" for character in job_id)
        or Path(filename).name != filename
        or not filename.endswith(".mp4")
    ):
        raise HTTPException(status_code=400, detail="Invalid clip filename.")
    path = settings.output_dir / job_id / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Clip not found.")
    return FileResponse(path, media_type="video/mp4", filename=filename)
