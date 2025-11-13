"""Job-related API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Job, User, UserJob
from app.schemas.job import JobAction, JobListResponse, JobResponse, MessageResponse
from app.services.audio import generate_job_audio_with_script

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/action", response_model=MessageResponse)
def apply_reject_job(
    job_action: JobAction,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Apply or reject a job for a user."""
    try:
        job_id = int(job_action.jobId)
        user_id = int(job_action.userId)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="jobId and userId must be valid integers or numeric strings",
        ) from exc

    if job_action.action not in {"apply", "reject"}:
        raise HTTPException(
            status_code=400,
            detail="action must be either 'apply' or 'reject'",
        )

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with id {job_id} not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    if job.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="Cannot apply or reject a closed job",
        )

    status = "applied" if job_action.action == "apply" else "rejected"

    user_job = (
        db.query(UserJob)
        .filter(UserJob.userId == user_id, UserJob.jobId == job_id)
        .first()
    )

    if user_job:
        user_job.status = status
    else:
        user_job = UserJob(userId=user_id, jobId=job_id, status=status)
        db.add(user_job)

    db.commit()

    message = f"Job {status} successfully"
    return MessageResponse(message=message)


@router.get("", response_model=JobListResponse)
def get_all_jobs(
    city: Optional[str] = Query(None, description="Filter jobs by city"),
    user_id: Optional[int] = Query(None, alias="userId", description="User ID to determine job status"),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Get all jobs, optionally filtered by city, with status per user."""
    query = db.query(Job)

    if city:
        query = query.filter(Job.city == city)

    jobs = query.all()

    job_responses: list[JobResponse] = []
    for job in jobs:
        job_status = "pending"

        if job.status == "closed":
            job_status = "closed"
        elif user_id:
            user_job = (
                db.query(UserJob)
                .filter(UserJob.userId == user_id, UserJob.jobId == job.id)
                .first()
            )
            if user_job:
                job_status = user_job.status

        hindi_audio_script, hindi_audio_base64 = generate_job_audio_with_script(
            job.jobTitle,
            job.wage,
            job.city,
            job.gender,
        )

        job_response = JobResponse(
            jobId=job.id,
            wage=job.wage,
            city=job.city,
            jobTitle=job.jobTitle,
            gender=job.gender,
            audioScript=hindi_audio_script,
            audio=hindi_audio_base64,
            jobStatus=job_status,
        )
        job_responses.append(job_response)

    return JobListResponse(jobs=job_responses)


