"""
Import existing GitHub repositories as Projects.

This script scans GitHub for repositories and creates Project records in the database.
Useful for populating the WebUI with existing project data.

Usage:
    python -m src.scripts.import_github_projects --org gpt153
    python -m src.scripts.import_github_projects --user gpt153
    python -m src.scripts.import_github_projects --repos "owner/repo1,owner/repo2"
"""

import argparse
import asyncio
import logging
from typing import List

import httpx
from sqlalchemy import select

from src.database.connection import async_session_maker
from src.database.models import Project, ProjectStatus
from src.integrations.github_client import GitHubClient, GitHubRepo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_repos_from_list(repo_urls: List[str]) -> int:
    """
    Import specific repositories from a list of URLs/names.

    Args:
        repo_urls: List of repository URLs or "owner/name" strings

    Returns:
        Number of projects imported
    """
    imported_count = 0
    github = GitHubClient()

    async with async_session_maker() as session:
        for repo_ref in repo_urls:
            try:
                # Parse repo from URL or "owner/name" format
                if "github.com" in repo_ref:
                    repo = GitHubRepo.from_url(repo_ref)
                    repo_url = repo_ref
                else:
                    # Assume "owner/name" format
                    parts = repo_ref.split("/")
                    if len(parts) != 2:
                        logger.warning(f"Invalid repo format: {repo_ref} (expected 'owner/name')")
                        continue
                    repo = GitHubRepo(owner=parts[0], name=parts[1])
                    repo_url = f"https://github.com/{repo.full_name}"

                # Check if project already exists
                result = await session.execute(
                    select(Project).where(Project.github_repo_url == repo_url)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"✓ Project already exists: {repo.full_name}")
                    continue

                # Fetch repo details from GitHub to get description
                try:
                    headers = github._get_headers()
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"https://api.github.com/repos/{repo.full_name}",
                            headers=headers,
                            timeout=10.0,
                        )
                        if response.status_code == 200:
                            repo_data = response.json()
                            description = repo_data.get("description", "")
                        else:
                            description = ""
                            logger.warning(f"Could not fetch details for {repo.full_name}")
                except Exception as e:
                    logger.warning(f"Could not fetch details for {repo.full_name}: {e}")
                    description = ""

                # Create new project
                project = Project(
                    name=repo.name,
                    description=description or f"Imported from {repo.full_name}",
                    github_repo_url=repo_url,
                    status=ProjectStatus.IN_PROGRESS,
                )
                session.add(project)
                imported_count += 1
                logger.info(f"✅ Imported: {repo.full_name}")

            except Exception as e:
                logger.error(f"Error importing {repo_ref}: {e}")
                continue

        await session.commit()

    return imported_count


async def import_repos_from_user(username: str) -> int:
    """
    Import all repositories for a GitHub user.

    Args:
        username: GitHub username

    Returns:
        Number of projects imported
    """
    github = GitHubClient()
    logger.info(f"Fetching repositories for user: {username}")

    try:
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 100, "type": "all"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=github._get_headers(), params=params, timeout=30.0
            )
            response.raise_for_status()
            repos = response.json()

        logger.info(f"Found {len(repos)} repositories for {username}")

        # Convert to repo URLs
        repo_urls = [repo["html_url"] for repo in repos]

        return await import_repos_from_list(repo_urls)

    except Exception as e:
        logger.error(f"Error fetching repos for user {username}: {e}")
        return 0


async def import_repos_from_org(org_name: str) -> int:
    """
    Import all repositories for a GitHub organization.

    Args:
        org_name: GitHub organization name

    Returns:
        Number of projects imported
    """
    github = GitHubClient()
    logger.info(f"Fetching repositories for organization: {org_name}")

    try:
        url = f"https://api.github.com/orgs/{org_name}/repos"
        params = {"per_page": 100, "type": "all"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=github._get_headers(), params=params, timeout=30.0
            )
            response.raise_for_status()
            repos = response.json()

        logger.info(f"Found {len(repos)} repositories for organization {org_name}")

        # Convert to repo URLs
        repo_urls = [repo["html_url"] for repo in repos]

        return await import_repos_from_list(repo_urls)

    except Exception as e:
        logger.error(f"Error fetching repos for organization {org_name}: {e}")
        return 0


async def main():
    """Main entry point for the import script."""
    parser = argparse.ArgumentParser(
        description="Import GitHub repositories as Projects in the database"
    )
    parser.add_argument("--user", type=str, help="Import all repositories for a GitHub user")
    parser.add_argument("--org", type=str, help="Import all repositories for a GitHub organization")
    parser.add_argument(
        "--repos", type=str, help='Comma-separated list of repo URLs or "owner/name" strings'
    )

    args = parser.parse_args()

    if not any([args.user, args.org, args.repos]):
        parser.error("Must specify at least one of: --user, --org, or --repos")

    logger.info("Starting GitHub repository import")

    total_imported = 0

    if args.repos:
        repo_list = [r.strip() for r in args.repos.split(",")]
        logger.info(f"Importing {len(repo_list)} repositories from list")
        total_imported += await import_repos_from_list(repo_list)

    if args.user:
        total_imported += await import_repos_from_user(args.user)

    if args.org:
        total_imported += await import_repos_from_org(args.org)

    logger.info(f"✅ Import complete! Imported {total_imported} new projects")

    # Show summary
    async with async_session_maker() as session:
        result = await session.execute(select(Project))
        all_projects = result.scalars().all()
        logger.info(f"📊 Total projects in database: {len(all_projects)}")


if __name__ == "__main__":
    asyncio.run(main())
