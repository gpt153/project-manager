"""
Health check endpoints for monitoring and readiness probes.

Provides detailed health information for different system components.
"""
import httpx
from fastapi import APIRouter, Response
from sqlalchemy import text

from src.database.connection import async_session_maker

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def basic_health():
    """
    Basic health check.

    Returns:
        dict: Basic health status
    """
    return {"status": "healthy", "service": "project-manager"}


@router.get("/db")
async def database_health():
    """
    Database connectivity check.

    Returns:
        dict: Database health status
    """
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return Response(
            content=f'{{"status": "unhealthy", "database": "disconnected", "error": "{str(e)}"}}',
            status_code=503,
            media_type="application/json"
        )


@router.get("/ai")
async def ai_service_health():
    """
    AI service connectivity check.

    Returns:
        dict: AI service health status
    """
    try:
        # Simple ping to Anthropic API
        async with httpx.AsyncClient() as client:
            await client.get(
                "https://api.anthropic.com",
                timeout=5.0
            )
        return {"status": "healthy", "ai_service": "reachable"}
    except Exception as e:
        return {
            "status": "degraded",
            "ai_service": "unreachable",
            "error": str(e)
        }


@router.get("/ready")
async def readiness_probe():
    """
    Readiness probe for Kubernetes/orchestration systems.

    Returns:
        dict: Readiness status (503 if not ready)
    """
    db_ok = False
    ai_ok = False

    # Check database
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Check AI service
    try:
        async with httpx.AsyncClient() as client:
            await client.get("https://api.anthropic.com", timeout=5.0)
        ai_ok = True
    except Exception:
        pass

    if db_ok and ai_ok:
        return {"status": "ready", "database": "ok", "ai_service": "ok"}
    else:
        db_status = "ok" if db_ok else "fail"
        ai_status = "ok" if ai_ok else "fail"
        return Response(
            content=f'{{"status": "not ready", "database": "{db_status}", "ai_service": "{ai_status}"}}',
            status_code=503,
            media_type="application/json"
        )
