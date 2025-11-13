"""API router for version 1 endpoints."""
from fastapi import APIRouter

from app.api.v1.endpoints import job_post, jobs

api_router = APIRouter()
api_router.include_router(job_post.router)
api_router.include_router(jobs.router)

__all__ = ["api_router"]