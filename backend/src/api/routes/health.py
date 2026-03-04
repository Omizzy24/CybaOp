"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Health check with service metadata."""
    return {
        "status": "healthy",
        "service": "cybaop-backend",
        "version": "0.1.0",
    }
