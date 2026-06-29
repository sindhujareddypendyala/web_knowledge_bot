"""
Health endpoint router.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import HealthResponse
from config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)
