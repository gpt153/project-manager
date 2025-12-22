"""
Service for importing SCAR projects from configuration files and environment variables.

This module provides functionality to automatically load projects into the database
on application startup.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.models import Project, ProjectStatus
from src.integrations.github_client import GitHubClient, GitHubRepo

logger = logging.getLogger(__name__)


async def load_projects_config(config_path: str) -> Optional[Dict]:
    """
    Load and parse the projects configuration file.

    Args:
        config_path: Path to the projects.json config file

    Returns:
        Parsed configuration dict or None if file not found/invalid
    """
    path = Path(config_path)

    if not path.exists():
        logger.debug(f"Projects config file not found: {config_path}")
        return None

    try:
        with open(path, 'r') as f:
            config = json.load(f)

        if not isinstance(config, dict) or 'projects' not in config:
            logger.warning(f"Invalid projects config format in {config_path}")
            return None

        logger.info(f"Loaded projects config from {config_path}")
        return config

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse projects config {config_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading projects config {config_path}: {e}")
        return None


async def import_from_config(session: AsyncSession, config: Dict) -> int:
    """
    Import projects from configuration dictionary.

    Args:
        session: Database session
        config: Configuration dict with 'projects' list

    Returns:
        Number of projects imported
    """
    if not config or 'projects' not in config:
        return 0

    projects_list = config.get('projects', [])
    imported_count = 0

    for project_config in projects_list:
        try:
            # Validate required fields
            if 'github_repo' not in project_config:
                logger.warning(f"Skipping project without github_repo: {project_config}")
                continue

            # Construct GitHub URL
            github_repo = project_config['github_repo']
            if github_repo.startswith('http'):
                repo_url = github_repo
            else:
                repo_url = f"https://github.com/{github_repo}"

            # Check if project already exists
            result = await session.execute(
                select(Project).where(Project.github_repo_url == repo_url)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug(f"Project already exists: {github_repo}")
                continue

            # Fetch repo details from GitHub if possible
            description = project_config.get('description', '')
            name = project_config.get('name', github_repo.split('/')[-1])

            if not description and settings.github_access_token:
                try:
                    github = GitHubClient()
                    repo = GitHubRepo.from_url(repo_url)

                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"https://api.github.com/repos/{repo.full_name}",
                            headers={
                                "Authorization": f"Bearer {settings.github_access_token}",
                                "Accept": "application/vnd.github.v3+json",
                                "User-Agent": "Project-Orchestrator"
                            },
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            repo_data = response.json()
                            description = repo_data.get("description", "") or description
                except Exception as e:
                    logger.debug(f"Could not fetch GitHub details for {github_repo}: {e}")

            # Get telegram_chat_id if provided
            telegram_chat_id = project_config.get('telegram_chat_id')

            # Create project
            project = Project(
                name=name,
                description=description or f"Imported from {github_repo}",
                github_repo_url=repo_url,
                telegram_chat_id=telegram_chat_id,
                status=ProjectStatus.IN_PROGRESS,
            )

            session.add(project)
            imported_count += 1
            logger.info(f"✅ Imported project from config: {github_repo}")

        except Exception as e:
            logger.error(f"Error importing project from config: {project_config}: {e}")
            continue

    if imported_count > 0:
        await session.commit()
        logger.info(f"Committed {imported_count} projects from config")

    return imported_count


async def import_from_repos_list(session: AsyncSession, repos_str: str) -> int:
    """
    Import projects from comma-separated list of repo names.

    Args:
        session: Database session
        repos_str: Comma-separated list like "owner/repo1,owner/repo2"

    Returns:
        Number of projects imported
    """
    if not repos_str or not repos_str.strip():
        return 0

    repo_list = [r.strip() for r in repos_str.split(',') if r.strip()]

    if not repo_list:
        return 0

    logger.info(f"Importing {len(repo_list)} repos from SCAR_IMPORT_REPOS")

    # Convert to config format and use import_from_config
    config = {
        'projects': [
            {'github_repo': repo, 'name': repo.split('/')[-1]}
            for repo in repo_list
        ]
    }

    return await import_from_config(session, config)


async def import_from_user(session: AsyncSession, username: str) -> int:
    """
    Import all repositories for a GitHub user.

    Args:
        session: Database session
        username: GitHub username

    Returns:
        Number of projects imported
    """
    if not username or not settings.github_access_token:
        return 0

    logger.info(f"Fetching repositories for user: {username}")

    try:
        import httpx
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 100, "type": "all"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {settings.github_access_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Project-Orchestrator"
                },
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            repos = response.json()

        logger.info(f"Found {len(repos)} repositories for {username}")

        # Convert to config format
        config = {
            'projects': [
                {
                    'github_repo': repo['full_name'],
                    'name': repo['name'],
                    'description': repo.get('description', '')
                }
                for repo in repos
            ]
        }

        return await import_from_config(session, config)

    except Exception as e:
        logger.error(f"Error fetching repos for user {username}: {e}")
        return 0


async def import_from_org(session: AsyncSession, org_name: str) -> int:
    """
    Import all repositories for a GitHub organization.

    Args:
        session: Database session
        org_name: GitHub organization name

    Returns:
        Number of projects imported
    """
    if not org_name or not settings.github_access_token:
        return 0

    logger.info(f"Fetching repositories for organization: {org_name}")

    try:
        import httpx
        url = f"https://api.github.com/orgs/{org_name}/repos"
        params = {"per_page": 100, "type": "all"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {settings.github_access_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Project-Orchestrator"
                },
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            repos = response.json()

        logger.info(f"Found {len(repos)} repositories for organization {org_name}")

        # Convert to config format
        config = {
            'projects': [
                {
                    'github_repo': repo['full_name'],
                    'name': repo['name'],
                    'description': repo.get('description', '')
                }
                for repo in repos
            ]
        }

        return await import_from_config(session, config)

    except Exception as e:
        logger.error(f"Error fetching repos for org {org_name}: {e}")
        return 0


async def auto_import_projects(session: AsyncSession) -> Dict:
    """
    Main orchestrator function for automatic project import.

    Tries multiple sources in priority order:
    1. Config file (.scar/projects.json)
    2. SCAR_IMPORT_REPOS environment variable
    3. SCAR_IMPORT_USER environment variable
    4. SCAR_IMPORT_ORG environment variable

    Args:
        session: Database session

    Returns:
        Summary dict with keys: source, count, errors
    """
    total_count = 0
    sources_used = []
    errors = []

    # Try config file first
    config = await load_projects_config(settings.scar_projects_config)
    if config:
        try:
            count = await import_from_config(session, config)
            if count > 0:
                total_count += count
                sources_used.append(f"config_file({count})")
        except Exception as e:
            logger.error(f"Error importing from config file: {e}")
            errors.append(f"config_file: {str(e)}")

    # Try environment variable repos list
    if settings.scar_import_repos:
        try:
            count = await import_from_repos_list(session, settings.scar_import_repos)
            if count > 0:
                total_count += count
                sources_used.append(f"env_repos({count})")
        except Exception as e:
            logger.error(f"Error importing from SCAR_IMPORT_REPOS: {e}")
            errors.append(f"env_repos: {str(e)}")

    # Try user repos
    if settings.scar_import_user:
        try:
            count = await import_from_user(session, settings.scar_import_user)
            if count > 0:
                total_count += count
                sources_used.append(f"user:{settings.scar_import_user}({count})")
        except Exception as e:
            logger.error(f"Error importing from user repos: {e}")
            errors.append(f"user: {str(e)}")

    # Try org repos
    if settings.scar_import_org:
        try:
            count = await import_from_org(session, settings.scar_import_org)
            if count > 0:
                total_count += count
                sources_used.append(f"org:{settings.scar_import_org}({count})")
        except Exception as e:
            logger.error(f"Error importing from org repos: {e}")
            errors.append(f"org: {str(e)}")

    source_summary = ", ".join(sources_used) if sources_used else "none"

    return {
        'source': source_summary,
        'count': total_count,
        'errors': errors
    }
