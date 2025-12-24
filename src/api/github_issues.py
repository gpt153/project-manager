"""
REST API router for GitHub issues.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import Project
from src.integrations.github_client import GitHubClient, GitHubRepo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/projects/{project_id}/issues", response_model=List[dict])
async def get_project_issues(
    project_id: UUID,
    state: str = Query(default="all", regex="^(open|closed|all)$"),
    limit: int = Query(default=100, le=100),
    session: AsyncSession = Depends(get_session),
):
    """
    Fetch GitHub issues for a project.

    Returns issues directly from GitHub API (no database caching in MVP).

    Args:
        project_id: Project UUID
        state: Issue state filter ("open", "closed", or "all")
        limit: Maximum number of issues to return

    Returns:
        List of issues from GitHub

    Raises:
        404: Project not found or has no GitHub repo
        500: GitHub API error
    """
    try:
        # Get project from database
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
            )

        if not project.github_repo_url:
            # Project has no GitHub repo, return empty list
            logger.info(f"Project {project_id} has no GitHub repo URL")
            return []

        # Parse repo from URL
        try:
            repo = GitHubRepo.from_url(project.github_repo_url)
        except ValueError as e:
            logger.warning(
                f"Invalid GitHub URL for project {project_id}: {project.github_repo_url}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid GitHub repository URL: {str(e)}",
            )

        # Fetch issues from GitHub API
        github = GitHubClient()
        issues = await github.get_issues(repo, state=state, limit=limit)

        # Format response
        formatted_issues = [
            {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "url": issue["html_url"],
                "labels": [label["name"] for label in issue.get("labels", [])],
                "assignees": [assignee["login"] for assignee in issue.get("assignees", [])],
            }
            for issue in issues
            # Filter out pull requests (GitHub API includes PRs in /issues endpoint)
            if "pull_request" not in issue
        ]

        logger.info(
            f"Retrieved {len(formatted_issues)} issues for project {project_id} from GitHub"
        )
        return formatted_issues

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching GitHub issues for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch GitHub issues",
        )


@router.get("/projects/{project_id}/issue-counts", response_model=dict)
async def get_project_issue_counts(project_id: UUID, session: AsyncSession = Depends(get_session)):
    """
    Get issue counts (open/closed) for a project.

    This is a lightweight endpoint for getting just the counts without fetching
    all issue data. Useful for updating project navigator counts.

    Args:
        project_id: Project UUID

    Returns:
        dict with open_issues_count and closed_issues_count

    Raises:
        404: Project not found
    """
    try:
        # Get project
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
            )

        if not project.github_repo_url:
            return {"open_issues_count": 0, "closed_issues_count": 0}

        # Parse repo
        try:
            repo = GitHubRepo.from_url(project.github_repo_url)
        except ValueError:
            logger.warning(f"Invalid GitHub URL for project {project_id}")
            return {"open_issues_count": 0, "closed_issues_count": 0}

        # Fetch counts from GitHub
        github = GitHubClient()

        # Fetch just 1 issue of each type to get count from headers
        # For MVP, we'll just count the results
        open_issues = await github.get_issues(repo, state="open", limit=100)
        closed_issues = await github.get_issues(repo, state="closed", limit=100)

        # Filter out pull requests
        open_count = len([i for i in open_issues if "pull_request" not in i])
        closed_count = len([i for i in closed_issues if "pull_request" not in i])

        return {
            "open_issues_count": open_count,
            "closed_issues_count": closed_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting issue counts for project {project_id}: {e}")
        # Return zeros on error rather than failing
        return {"open_issues_count": 0, "closed_issues_count": 0}
