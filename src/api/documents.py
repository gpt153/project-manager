"""
REST API router for document retrieval (vision docs, plans).
"""
import logging
from typing import List
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.connection import get_session
from src.database.models import Project

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/documents/vision/{project_id}", response_class=PlainTextResponse)
async def get_vision_document(
    project_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get vision document as markdown.

    Args:
        project_id: Project UUID

    Returns:
        Vision document in markdown format

    Raises:
        404: Project or vision document not found
    """
    try:
        query = select(Project).where(Project.id == project_id)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        if not project.vision_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vision document not found for this project"
            )

        # Convert JSONB vision document to markdown
        # For now, return as JSON string; can be enhanced to convert to markdown
        import json
        vision_markdown = json.dumps(project.vision_document, indent=2)

        return vision_markdown

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vision document for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vision document"
        )


@router.get("/documents/plans/{project_id}", response_model=List[dict])
async def get_implementation_plans(
    project_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get implementation plans for a project.

    This is a placeholder for future implementation.
    Plans could be stored in the database or as files in .agents/plans/

    Args:
        project_id: Project UUID

    Returns:
        List of plan documents
    """
    try:
        # Verify project exists
        query = select(Project).where(Project.id == project_id)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # For MVP, return empty list
        # TODO: Implement plan storage and retrieval
        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plans for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans"
        )


@router.get("/documents/list/{project_id}", response_model=List[dict])
async def list_documents(
    project_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    List all available documents for a project.

    Args:
        project_id: Project UUID

    Returns:
        List of document metadata
    """
    try:
        # Verify project exists
        query = select(Project).where(Project.id == project_id)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        documents = []

        # Add vision document if it exists
        if project.vision_document:
            documents.append({
                "id": f"vision-{project_id}",
                "name": "Vision Document",
                "type": "vision",
                "url": f"/api/documents/vision/{project_id}",
            })

        # TODO: Add plans when implemented
        # TODO: Add other document types

        logger.debug(f"Found {len(documents)} documents for project {project_id}")
        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )
