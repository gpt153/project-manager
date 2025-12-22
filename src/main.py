"""
Main FastAPI application for the Project Orchestrator.

This module initializes the FastAPI app, configures middleware, and sets up routes.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.database.connection import close_db, init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan events.

    Handles startup and shutdown tasks like database initialization.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")

    if settings.app_env == "development":
        logger.info("Initializing database tables (development mode)")
        await init_db()

    # Auto-import SCAR projects
    if settings.scar_auto_import:
        logger.info("Auto-importing SCAR projects...")
        try:
            from src.database.connection import async_session_maker
            from src.services.project_import_service import auto_import_projects

            async with async_session_maker() as session:
                result = await auto_import_projects(session)
                if result['count'] > 0:
                    logger.info(
                        f"✅ Auto-import complete: {result['count']} projects from {result['source']}"
                    )
                else:
                    logger.info("No new projects to import")

                if result['errors']:
                    logger.warning(f"Import errors occurred: {result['errors']}")

        except Exception as e:
            logger.error(f"Error during auto-import: {e}", exc_info=True)
            # Don't fail startup on import errors
    else:
        logger.info("SCAR auto-import disabled")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI agent that helps non-coders build software projects",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Application health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "version": "0.1.0",
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API welcome message and documentation link
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }


# Include API routers

# GitHub webhook integration (from master)
try:
    from src.integrations.github_webhook import router as github_webhook_router
    app.include_router(github_webhook_router)
    logger.info("GitHub webhook router registered")
except ImportError:
    logger.warning("GitHub webhook router not available")

# Web UI routers (from feature-webui)
try:
    from src.api.projects import router as projects_router
    from src.api.documents import router as documents_router
    from src.api.websocket import router as websocket_router
    from src.api.sse import router as sse_router
    from src.api.github_issues import router as github_issues_router

    app.include_router(projects_router, prefix="/api", tags=["Projects"])
    app.include_router(documents_router, prefix="/api", tags=["Documents"])
    app.include_router(websocket_router, prefix="/api", tags=["WebSocket"])
    app.include_router(sse_router, prefix="/api", tags=["SSE"])
    app.include_router(github_issues_router, prefix="/api", tags=["GitHub Issues"])
    logger.info("Web UI routers registered")
except ImportError as e:
    logger.warning(f"Web UI routers not available: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
