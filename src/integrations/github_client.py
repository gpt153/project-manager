"""
GitHub API Client.

This module provides utilities for interacting with the GitHub API
to create comments, manage pull requests, and perform other repository operations.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GitHubRepo:
    """GitHub repository information."""

    owner: str
    name: str

    @property
    def full_name(self) -> str:
        """Get full repository name (owner/name)."""
        return f"{self.owner}/{self.name}"

    @classmethod
    def from_url(cls, url: str) -> "GitHubRepo":
        """
        Parse repository from GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            GitHubRepo: Parsed repository info

        Example:
            >>> GitHubRepo.from_url("https://github.com/owner/repo")
            GitHubRepo(owner='owner', name='repo')
        """
        # Remove protocol and trailing elements
        url = url.replace("https://", "").replace("http://", "")
        url = url.replace("github.com/", "")
        url = url.rstrip("/").replace(".git", "")

        parts = url.split("/")
        if len(parts) >= 2:
            return cls(owner=parts[0], name=parts[1])
        raise ValueError(f"Invalid GitHub URL: {url}")


class GitHubClient:
    """
    GitHub API client for repository operations.

    This client handles authentication and provides methods for common
    GitHub operations like creating comments and managing pull requests.
    """

    def __init__(self, access_token: Optional[str] = ...):  # type: ignore
        """
        Initialize GitHub client.

        Args:
            access_token: GitHub personal access token (uses settings.github_access_token if not provided)
        """
        # Use ... (Ellipsis) as sentinel to distinguish "not provided" from explicit None
        if access_token is ...:
            self.access_token = settings.github_access_token
        else:
            self.access_token = access_token
        self.base_url = "https://api.github.com"

        if not self.access_token:
            logger.warning("GitHub access token not configured - API calls will be limited")

    def _get_headers(self) -> dict:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    async def create_issue_comment(
        self, repo: GitHubRepo, issue_number: int, comment_body: str
    ) -> dict:
        """
        Create a comment on a GitHub issue or pull request.

        Args:
            repo: Repository information
            issue_number: Issue or PR number
            comment_body: Comment text (markdown supported)

        Returns:
            dict: API response with comment data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}/issues/{issue_number}/comments"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={"body": comment_body},
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(
                f"Created comment on {repo.full_name}#{issue_number}: "
                f"Comment ID {response.json().get('id')}"
            )

            return response.json()

    async def update_pull_request(
        self,
        repo: GitHubRepo,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
    ) -> dict:
        """
        Update a pull request.

        Args:
            repo: Repository information
            pr_number: Pull request number
            title: New PR title (optional)
            body: New PR body (optional)
            state: New PR state: "open" or "closed" (optional)

        Returns:
            dict: API response with updated PR data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}/pulls/{pr_number}"

        update_data = {}
        if title is not None:
            update_data["title"] = title
        if body is not None:
            update_data["body"] = body
        if state is not None:
            update_data["state"] = state

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json=update_data,
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(f"Updated PR {repo.full_name}#{pr_number}")

            return response.json()

    async def get_pull_request(self, repo: GitHubRepo, pr_number: int) -> dict:
        """
        Get pull request details.

        Args:
            repo: Repository information
            pr_number: Pull request number

        Returns:
            dict: Pull request data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}/pulls/{pr_number}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()

            return response.json()

    async def list_pull_requests(
        self,
        repo: GitHubRepo,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None,
    ) -> list[dict]:
        """
        List pull requests in a repository.

        Args:
            repo: Repository information
            state: PR state filter: "open", "closed", or "all"
            head: Filter by head branch (format: "user:ref-name")
            base: Filter by base branch

        Returns:
            list[dict]: List of pull requests

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}/pulls"

        params = {"state": state}
        if head:
            params["head"] = head
        if base:
            params["base"] = base

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()

            return response.json()

    async def get_issues(
        self, repo: GitHubRepo, state: str = "all", limit: int = 100
    ) -> list[dict]:
        """
        Get issues for a repository.

        Args:
            repo: Repository information
            state: Issue state filter: "open", "closed", or "all"
            limit: Maximum number of issues to return (max 100)

        Returns:
            list[dict]: List of issue dictionaries from GitHub API

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}/issues"
        params = {
            "state": state,
            "per_page": min(limit, 100),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self._get_headers(), params=params, timeout=10.0
            )
            response.raise_for_status()

            logger.info(
                f"Retrieved {len(response.json())} issues from {repo.full_name} (state={state})"
            )
            return response.json()

    async def create_pull_request(
        self,
        repo: GitHubRepo,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
    ) -> dict:
        """
        Create a new pull request.

        Args:
            repo: Repository information
            title: PR title
            head: Name of the branch where your changes are implemented
            base: Name of the branch you want changes pulled into (usually "main")
            body: PR description (markdown supported)
            draft: Create as draft PR

        Returns:
            dict: Created pull request data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}/pulls"

        pr_data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            pr_data["body"] = body

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=pr_data,
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(
                f"Created PR in {repo.full_name}: {title} (#{response.json().get('number')})"
            )

            return response.json()

    async def get_repository(self, repo: GitHubRepo) -> dict:
        """
        Get repository information.

        Args:
            repo: Repository information

        Returns:
            dict: Repository data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/repos/{repo.full_name}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()

            return response.json()

    async def check_repository_access(self, repo: GitHubRepo) -> bool:
        """
        Check if we have access to a repository.

        Args:
            repo: Repository information

        Returns:
            bool: True if we have access, False otherwise
        """
        try:
            await self.get_repository(repo)
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Repository not found or no access: {repo.full_name}")
                return False
            raise
