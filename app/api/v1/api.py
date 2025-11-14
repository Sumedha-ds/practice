"""API router for version 1 endpoints."""
from fastapi import APIRouter

from app.api.v1.endpoints import post_job, jobs, job_post_voice, auth_sync

api_router = APIRouter()
api_router.include_router(post_job.router)
api_router.include_router(jobs.router)
api_router.include_router(job_post_voice.router)
api_router.include_router(auth_sync.router)

__all__ = ["api_router"]