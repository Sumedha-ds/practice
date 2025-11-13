"""API router for version 1 endpoints."""
from fastapi import APIRouter

from app.api.v1.endpoints import jobs

api_router = APIRouter()
api_router.include_router(jobs.router)

__all__ = ["api_router"]


