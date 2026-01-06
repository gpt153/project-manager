"""
SCAR HTTP Client for communicating with SCAR Test Adapter API.

This client handles:
- Sending commands to SCAR via POST /test/message
- Polling for command completion via GET /test/messages/:id
- Cleaning up conversations via DELETE /test/messages/:id
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

import httpx

from src.config import Settings
from src.scar.types import ScarMessage, ScarMessageRequest, ScarMessagesResponse

logger = logging.getLogger(__name__)


class ScarClient:
    """
    HTTP client for SCAR Test Adapter API.

    Manages communication with SCAR's HTTP endpoints for command execution,
    message retrieval, and conversation cleanup.
    """

    def __init__(self, settings: Settings):
        """
        Initialize SCAR client with configuration.

        Args:
            settings: Application settings containing SCAR configuration
        """
        self.base_url = settings.scar_base_url
        self.timeout_seconds = settings.scar_timeout_seconds
        self.conversation_prefix = settings.scar_conversation_prefix

    def _build_conversation_id(self, project_id: UUID) -> str:
        """
        Build conversation ID for SCAR from project ID.

        Args:
            project_id: Project UUID

        Returns:
            str: Conversation ID (format: pm-project-{uuid})
        """
        return f"{self.conversation_prefix}{project_id}"

    def _derive_workspace_path(self, github_repo_url: str) -> str:
        """
        Derive workspace path from GitHub repository URL.

        Args:
            github_repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)

        Returns:
            str: Workspace path (e.g., /workspace/repo)
        """
        # Extract repo name from URL
        # https://github.com/owner/repo.git -> repo
        # https://github.com/owner/repo -> repo
        repo_part = github_repo_url.rstrip("/").split("/")[-1]
        repo_name = repo_part.replace(".git", "")

        # SCAR convention: /workspace/<repo-name>
        return f"/workspace/{repo_name}"

    async def _setup_workspace(self, conversation_id: str, github_repo_url: str) -> None:
        """
        Set up SCAR workspace for the project.

        Sends /repo command to SCAR to switch to the registered codebase.

        Args:
            conversation_id: Conversation ID for SCAR
            github_repo_url: GitHub repository URL

        Raises:
            httpx.HTTPError: If request fails
        """
        # Extract repo name from URL
        repo_part = github_repo_url.rstrip("/").split("/")[-1]
        repo_name = repo_part.replace(".git", "")

        logger.info(
            f"Switching SCAR to codebase: {repo_name}",
            extra={"conversation_id": conversation_id, "github_repo": github_repo_url},
        )

        # Send /repo command to switch codebase
        repo_request = ScarMessageRequest(
            conversationId=conversation_id, message=f"/repo {repo_name}"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/test/message",
                json=repo_request.model_dump(),
            )
            response.raise_for_status()

        logger.info(
            "SCAR codebase switched successfully",
            extra={"repo_name": repo_name},
        )

    async def send_command(
        self,
        project_id: UUID,
        command: str,
        args: Optional[list[str]] = None,
        github_repo_url: Optional[str] = None,
    ) -> str:
        """
        Send a command to SCAR and return conversation ID for polling.

        Automatically sets up the workspace before executing the command.

        Args:
            project_id: Project UUID
            command: SCAR command to execute (e.g., "prime", "plan-feature-github")
            args: Optional command arguments
            github_repo_url: Optional GitHub repository URL for workspace setup

        Returns:
            str: Conversation ID for polling messages

        Raises:
            httpx.HTTPError: If request fails
        """
        conversation_id = self._build_conversation_id(project_id)

        # Set up workspace if github_repo_url provided
        if github_repo_url:
            await self._setup_workspace(conversation_id, github_repo_url)

        # Build command string
        command_str = f"/command-invoke {command}"
        if args:
            # Quote args with spaces to preserve them
            args_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in args)
            command_str += f" {args_str}"

        logger.info(
            f"Sending SCAR command: {command_str}",
            extra={"conversation_id": conversation_id, "project_id": str(project_id)},
        )

        # Send POST /test/message
        request_body = ScarMessageRequest(conversationId=conversation_id, message=command_str)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/test/message",
                json=request_body.model_dump(),
            )
            response.raise_for_status()

        logger.info(
            "SCAR command sent successfully",
            extra={"conversation_id": conversation_id, "command": command},
        )

        return conversation_id

    async def get_messages(self, conversation_id: str) -> list[ScarMessage]:
        """
        Get all messages from SCAR conversation.

        Args:
            conversation_id: Conversation ID to retrieve messages from

        Returns:
            list[ScarMessage]: All messages (sent by bot)

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/test/messages/{conversation_id}")
            response.raise_for_status()

            # Parse response
            data = response.json()
            messages_response = ScarMessagesResponse(**data)

            # Filter to only messages sent by bot (direction="sent")
            bot_messages = [msg for msg in messages_response.messages if msg.direction == "sent"]

            return bot_messages

    async def clear_messages(self, conversation_id: str) -> None:
        """
        Clear all messages from SCAR conversation.

        Args:
            conversation_id: Conversation ID to clear

        Raises:
            httpx.HTTPError: If request fails
        """
        logger.info(f"Clearing SCAR conversation: {conversation_id}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{self.base_url}/test/messages/{conversation_id}")
            response.raise_for_status()

    async def wait_for_completion(
        self, conversation_id: str, timeout: Optional[float] = None, poll_interval: float = 2.0
    ) -> list[ScarMessage]:
        """
        Poll SCAR conversation until command completes.

        Completion is detected when no new messages appear for 2 consecutive polls.

        Args:
            conversation_id: Conversation ID to poll
            timeout: Max wait time in seconds (defaults to self.timeout_seconds)
            poll_interval: Seconds between polls (default: 2.0)

        Returns:
            list[ScarMessage]: All messages from completed command

        Raises:
            TimeoutError: If no completion detected within timeout
            httpx.HTTPError: If request fails
        """
        if timeout is None:
            timeout = float(self.timeout_seconds)

        logger.info(
            "Waiting for SCAR command completion",
            extra={
                "conversation_id": conversation_id,
                "timeout": timeout,
                "poll_interval": poll_interval,
            },
        )

        start_time = asyncio.get_event_loop().time()
        previous_message_count = 0
        stable_count = 0  # Number of consecutive polls with no new messages

        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"SCAR command timed out after {elapsed:.1f}s "
                    f"(timeout: {timeout}s, conversation: {conversation_id})"
                )

            # Get current messages
            messages = await self.get_messages(conversation_id)
            current_count = len(messages)

            logger.debug(
                f"Poll: {current_count} messages ({elapsed:.1f}s elapsed)",
                extra={"conversation_id": conversation_id, "message_count": current_count},
            )

            # Check for new messages
            if current_count > previous_message_count:
                # New messages arrived - reset stability counter
                stable_count = 0
                previous_message_count = current_count
            else:
                # No new messages - increment stability counter
                stable_count += 1

            # If we've had 2 consecutive polls with no new messages, consider complete
            if stable_count >= 2:
                logger.info(
                    "SCAR command completed",
                    extra={
                        "conversation_id": conversation_id,
                        "message_count": current_count,
                        "duration": elapsed,
                    },
                )
                return messages

            # Wait before next poll
            await asyncio.sleep(poll_interval)
