"""Endpoint for posting new jobs."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.job import Job
from app.schemas.job import JobDetails, JobPostResponse

router = APIRouter(tags=["job-posting"])

BASE_DIR = Path(__file__).resolve().parents[4]
UPLOAD_DIR = BASE_DIR / "uploads"


@router.post(
    "/post-job",
    response_model=JobPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post a new job",
)
async def post_job(
    jobTitle: str = Form(..., description="Title of the job"),
    gender: str = Form(..., description="Preferred gender for the job"),
    wage: float = Form(..., description="Wage offered for the job"),
    city: str = Form(..., description="City where the job is located"),
    audioDescription: UploadFile = File(..., description="MP3 audio description of the job"),
    db: Session = Depends(get_db),
) -> JobPostResponse:
    """Create a new job post with associated audio description."""
    job_title = jobTitle.strip()
    job_gender = gender.strip()
    job_city = city.strip()

    if not job_title:
        raise HTTPException(status_code=400, detail="jobTitle is required")

    if not job_gender:
        raise HTTPException(status_code=400, detail="gender is required")

    if not job_city:
        raise HTTPException(status_code=400, detail="city is required")

    if audioDescription.content_type not in {"audio/mpeg", "audio/mp3"}:
        raise HTTPException(status_code=400, detail="audioDescription must be an MP3 file")

    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to create uploads directory") from exc

    file_suffix = Path(audioDescription.filename or "").suffix.lower()
    if file_suffix not in {".mp3", ".mpeg"}:
        file_suffix = ".mp3"

    job_uuid = str(uuid.uuid4())
    timestamp = int(time.time())
    filename = f"audio_{timestamp}_{job_uuid}{file_suffix}"
    file_path = UPLOAD_DIR / filename

    try:
        contents = await audioDescription.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty")

        with file_path.open("wb") as buffer:
            buffer.write(contents)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - unexpected file errors
        raise HTTPException(status_code=500, detail="Failed to save audio file") from exc
    finally:
        await audioDescription.close()

    relative_path = str(file_path.relative_to(BASE_DIR))

    job = Job(
        jobUuid=job_uuid,
        jobTitle=job_title,
        gender=job_gender,
        wage=wage,
        city=job_city,
        audioScript="",
        audioFilePath=relative_path,
    )

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as exc:  # pragma: no cover - unexpected db errors
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to store job data") from exc

    print(f"New job posted: {job.jobTitle} ({job.city})")

    job_details = JobDetails(
        jobTitle=job.jobTitle,
        gender=job.gender,
        wage=job.wage,
        city=job.city,
        audioFilePath=job.audioFilePath or relative_path,
    )

    return JobPostResponse(
        message="Job posted successfully",
        jobId=job_uuid,
        jobDetails=job_details,
    )

