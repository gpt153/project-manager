"""
Tests for the project import service.
"""

import json

import pytest
from sqlalchemy import select

from src.database.models import Project
from src.services.project_import_service import (
    auto_import_projects,
    import_from_config,
    import_from_repos_list,
    load_projects_config,
)


class TestLoadProjectsConfig:
    """Tests for load_projects_config function"""

    @pytest.mark.asyncio
    async def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file"""
        config_data = {
            "version": "1.0",
            "projects": [
                {
                    "name": "Test Project",
                    "github_repo": "owner/repo",
                    "description": "A test project",
                }
            ],
        }

        config_file = tmp_path / "projects.json"
        config_file.write_text(json.dumps(config_data))

        result = await load_projects_config(str(config_file))

        assert result is not None
        assert result["version"] == "1.0"
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self):
        """Test loading a non-existent config file"""
        result = await load_projects_config("/nonexistent/path/projects.json")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON"""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")

        result = await load_projects_config(str(config_file))
        assert result is None

    @pytest.mark.asyncio
    async def test_load_config_missing_projects_key(self, tmp_path):
        """Test loading a config without 'projects' key"""
        config_data = {"version": "1.0"}

        config_file = tmp_path / "no_projects.json"
        config_file.write_text(json.dumps(config_data))

        result = await load_projects_config(str(config_file))
        assert result is None


class TestImportFromConfig:
    """Tests for import_from_config function"""

    @pytest.mark.asyncio
    async def test_import_new_projects(self, async_session):
        """Test importing new projects from config"""
        config = {
            "projects": [
                {"name": "Project 1", "github_repo": "owner/repo1", "description": "First project"},
                {
                    "name": "Project 2",
                    "github_repo": "owner/repo2",
                    "description": "Second project",
                },
            ]
        }

        count = await import_from_config(async_session, config)

        assert count == 2

        # Verify projects were created
        result = await async_session.execute(select(Project))
        projects = result.scalars().all()

        assert len(projects) == 2
        assert any(p.name == "Project 1" for p in projects)
        assert any(p.name == "Project 2" for p in projects)

    @pytest.mark.asyncio
    async def test_import_skip_duplicates(self, async_session):
        """Test that duplicate projects are skipped"""
        # Create existing project
        existing_project = Project(
            name="Existing Project",
            github_repo_url="https://github.com/owner/repo1",
            description="Already exists",
        )
        async_session.add(existing_project)
        await async_session.commit()

        config = {
            "projects": [
                {
                    "name": "Project 1",
                    "github_repo": "owner/repo1",
                    "description": "Should be skipped",
                },
                {
                    "name": "Project 2",
                    "github_repo": "owner/repo2",
                    "description": "Should be imported",
                },
            ]
        }

        count = await import_from_config(async_session, config)

        assert count == 1  # Only one new project

        result = await async_session.execute(select(Project))
        projects = result.scalars().all()

        assert len(projects) == 2  # Total 2 projects

    @pytest.mark.asyncio
    async def test_import_with_http_url(self, async_session):
        """Test importing project with full HTTP URL"""
        config = {
            "projects": [
                {
                    "name": "Full URL Project",
                    "github_repo": "https://github.com/owner/repo",
                    "description": "Uses full URL",
                }
            ]
        }

        count = await import_from_config(async_session, config)

        assert count == 1

        result = await async_session.execute(select(Project))
        project = result.scalar_one()

        assert project.github_repo_url == "https://github.com/owner/repo"

    @pytest.mark.asyncio
    async def test_import_with_telegram_chat_id(self, async_session):
        """Test importing project with telegram_chat_id"""
        config = {
            "projects": [
                {
                    "name": "Telegram Project",
                    "github_repo": "owner/repo",
                    "telegram_chat_id": -1001234567890,
                }
            ]
        }

        count = await import_from_config(async_session, config)

        assert count == 1

        result = await async_session.execute(select(Project))
        project = result.scalar_one()

        assert project.telegram_chat_id == -1001234567890

    @pytest.mark.asyncio
    async def test_import_empty_config(self, async_session):
        """Test importing with empty config"""
        config = {"projects": []}

        count = await import_from_config(async_session, config)

        assert count == 0

    @pytest.mark.asyncio
    async def test_import_skip_invalid_entries(self, async_session):
        """Test that entries without github_repo are skipped"""
        config = {
            "projects": [
                {"name": "Invalid Project", "description": "Missing github_repo"},
                {"name": "Valid Project", "github_repo": "owner/repo"},
            ]
        }

        count = await import_from_config(async_session, config)

        assert count == 1


class TestImportFromReposList:
    """Tests for import_from_repos_list function"""

    @pytest.mark.asyncio
    async def test_import_from_comma_separated_list(self, async_session):
        """Test importing from comma-separated repo list"""
        repos_str = "owner/repo1,owner/repo2,owner/repo3"

        count = await import_from_repos_list(async_session, repos_str)

        assert count == 3

        result = await async_session.execute(select(Project))
        projects = result.scalars().all()

        assert len(projects) == 3

    @pytest.mark.asyncio
    async def test_import_from_list_with_whitespace(self, async_session):
        """Test importing with whitespace in list"""
        repos_str = "owner/repo1, owner/repo2 , owner/repo3"

        count = await import_from_repos_list(async_session, repos_str)

        assert count == 3

    @pytest.mark.asyncio
    async def test_import_empty_string(self, async_session):
        """Test importing with empty string"""
        count = await import_from_repos_list(async_session, "")

        assert count == 0

    @pytest.mark.asyncio
    async def test_import_none(self, async_session):
        """Test importing with None"""
        count = await import_from_repos_list(async_session, None)

        assert count == 0


class TestAutoImportProjects:
    """Tests for auto_import_projects function"""

    @pytest.mark.asyncio
    async def test_auto_import_from_config_file(self, async_session, tmp_path, monkeypatch):
        """Test auto-import prioritizes config file"""
        config_data = {"projects": [{"name": "Config Project", "github_repo": "owner/config-repo"}]}

        config_file = tmp_path / "projects.json"
        config_file.write_text(json.dumps(config_data))

        # Mock settings to use our test config file
        from src import config

        monkeypatch.setattr(config.settings, "scar_projects_config", str(config_file))
        monkeypatch.setattr(config.settings, "scar_import_repos", None)
        monkeypatch.setattr(config.settings, "scar_import_user", None)
        monkeypatch.setattr(config.settings, "scar_import_org", None)

        result = await auto_import_projects(async_session)

        assert result["count"] == 1
        assert "config_file" in result["source"]
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_auto_import_from_env_repos(self, async_session, monkeypatch):
        """Test auto-import from SCAR_IMPORT_REPOS env var"""
        from src import config

        monkeypatch.setattr(config.settings, "scar_projects_config", "/nonexistent/config.json")
        monkeypatch.setattr(config.settings, "scar_import_repos", "owner/repo1,owner/repo2")
        monkeypatch.setattr(config.settings, "scar_import_user", None)
        monkeypatch.setattr(config.settings, "scar_import_org", None)

        result = await auto_import_projects(async_session)

        assert result["count"] == 2
        assert "env_repos" in result["source"]

    @pytest.mark.asyncio
    async def test_auto_import_no_sources(self, async_session, monkeypatch):
        """Test auto-import with no sources configured"""
        from src import config

        monkeypatch.setattr(config.settings, "scar_projects_config", "/nonexistent/config.json")
        monkeypatch.setattr(config.settings, "scar_import_repos", None)
        monkeypatch.setattr(config.settings, "scar_import_user", None)
        monkeypatch.setattr(config.settings, "scar_import_org", None)

        result = await auto_import_projects(async_session)

        assert result["count"] == 0
        assert result["source"] == "none"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_auto_import_multiple_sources(self, async_session, tmp_path, monkeypatch):
        """Test auto-import from multiple sources"""
        config_data = {"projects": [{"name": "Config Project", "github_repo": "owner/config-repo"}]}

        config_file = tmp_path / "projects.json"
        config_file.write_text(json.dumps(config_data))

        from src import config

        monkeypatch.setattr(config.settings, "scar_projects_config", str(config_file))
        monkeypatch.setattr(config.settings, "scar_import_repos", "owner/env-repo")
        monkeypatch.setattr(config.settings, "scar_import_user", None)
        monkeypatch.setattr(config.settings, "scar_import_org", None)

        result = await auto_import_projects(async_session)

        assert result["count"] == 2
        assert "config_file" in result["source"]
        assert "env_repos" in result["source"]
