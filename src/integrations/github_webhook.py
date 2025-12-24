"""
GitHub Webhook Integration.

This module handles incoming GitHub webhooks for issue comments, pull requests,
and other repository events.
"""

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.orchestrator_agent import run_orchestrator
from src.config import settings
from src.database.models import Project

logger = logging.getLogger(__name__)

# Create router for webhook endpoints
router = APIRouter(prefix="/webhooks/github", tags=["GitHub Webhooks"])


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value

    Returns:
        bool: True if signature is valid
    """
    if not settings.github_webhook_secret:
        logger.warning("GitHub webhook secret not configured - skipping signature verification")
        return True

    if not signature_header:
        return False

    # GitHub sends signature as "sha256=<hash>"
    hash_algorithm, github_signature = signature_header.split("=")

    if hash_algorithm != "sha256":
        return False

    # Calculate HMAC
    mac = hmac.new(
        settings.github_webhook_secret.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256,
    )
    expected_signature = mac.hexdigest()

    return hmac.compare_digest(expected_signature, github_signature)


async def get_project_by_repo(session: AsyncSession, repo_url: str) -> Optional[Project]:
    """
    Find project by GitHub repository URL.

    Args:
        session: Database session
        repo_url: GitHub repository URL

    Returns:
        Project if found, None otherwise
    """
    # Normalize repo URL (remove trailing slash, .git, etc.)
    normalized_url = repo_url.rstrip("/").replace(".git", "")

    result = await session.execute(
        select(Project).where(Project.github_repo_url.like(f"%{normalized_url}%"))
    )
    return result.scalar_one_or_none()


async def handle_issue_comment(payload: dict, session: AsyncSession) -> dict:
    """
    Handle issue comment webhook event.

    This checks for @mentions of the bot and triggers the orchestrator agent.

    Args:
        payload: GitHub webhook payload
        session: Database session

    Returns:
        dict: Response message
    """
    action = payload.get("action")
    comment = payload.get("comment", {})
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})

    # Only process created comments
    if action != "created":
        return {"status": "ignored", "reason": "Not a created comment"}

    comment_body = comment.get("body", "")
    repo_url = repository.get("html_url", "")

    # Check if bot is mentioned (customize bot name as needed)
    bot_mention = "@po"
    if bot_mention not in comment_body.lower():
        return {"status": "ignored", "reason": "Bot not mentioned"}

    # Find project by repo URL
    project = await get_project_by_repo(session, repo_url)
    if not project:
        logger.warning(f"No project found for repository: {repo_url}")
        return {"status": "error", "reason": "Project not found"}

    # Extract user message (remove bot mention)
    user_message = comment_body.replace(bot_mention, "").strip()

    # Process through orchestrator agent
    try:
        response = await run_orchestrator(project.id, user_message, session)

        logger.info(
            f"Processed issue comment for project {project.id}: "
            f"Issue #{issue.get('number')}, Comment #{comment.get('id')}"
        )

        return {
            "status": "success",
            "project_id": str(project.id),
            "issue_number": issue.get("number"),
            "response": response,
        }
    except Exception as e:
        logger.error(f"Error processing issue comment: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}


async def handle_pull_request(payload: dict, session: AsyncSession) -> dict:
    """
    Handle pull request webhook event.

    Args:
        payload: GitHub webhook payload
        session: Database session

    Returns:
        dict: Response message
    """
    action = payload.get("action")
    pull_request = payload.get("pull_request", {})
    repository = payload.get("repository", {})

    logger.info(
        f"Received PR webhook: action={action}, "
        f"PR #{pull_request.get('number')} in {repository.get('full_name')}"
    )

    # Find project
    repo_url = repository.get("html_url", "")
    project = await get_project_by_repo(session, repo_url)

    if not project:
        logger.warning(f"No project found for repository: {repo_url}")
        return {"status": "error", "reason": "Project not found"}

    # Handle different PR actions
    if action == "opened":
        # PR opened - could trigger validation workflow
        return {
            "status": "success",
            "message": "PR opened notification received",
            "pr_number": pull_request.get("number"),
        }
    elif action == "closed":
        # PR merged or closed
        if pull_request.get("merged"):
            return {
                "status": "success",
                "message": "PR merged notification received",
                "pr_number": pull_request.get("number"),
            }

    return {"status": "ignored", "reason": f"Unhandled action: {action}"}


@router.post("/")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
):
    """
    GitHub webhook endpoint.

    Receives and processes GitHub webhook events (issue comments, PRs, etc.).

    Args:
        request: FastAPI request object
        x_github_event: GitHub event type header
        x_hub_signature_256: GitHub signature header

    Returns:
        dict: Processing result
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    if not verify_github_signature(body, x_hub_signature_256):
        logger.warning("Invalid GitHub webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info(f"Received GitHub webhook: event={x_github_event}")

    # Process event based on type
    from src.database.connection import async_session_maker

    async with async_session_maker() as session:
        if x_github_event == "issue_comment":
            result = await handle_issue_comment(payload, session)
        elif x_github_event == "pull_request":
            result = await handle_pull_request(payload, session)
        elif x_github_event == "ping":
            return {"status": "success", "message": "Pong! Webhook is configured correctly"}
        else:
            logger.info(f"Unhandled GitHub event type: {x_github_event}")
            return {"status": "ignored", "event": x_github_event}

    return result


@router.get("/health")
async def webhook_health():
    """
    Webhook health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "webhook_secret_configured": bool(settings.github_webhook_secret),
        "github_token_configured": bool(settings.github_access_token),
    }
