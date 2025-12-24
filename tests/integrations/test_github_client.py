"""
Tests for GitHub API client.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.integrations.github_client import GitHubClient, GitHubRepo


class TestGitHubRepo:
    """Test GitHubRepo dataclass."""

    def test_full_name(self):
        """Test full_name property."""
        repo = GitHubRepo(owner="octocat", name="hello-world")
        assert repo.full_name == "octocat/hello-world"

    def test_from_url_basic(self):
        """Test parsing basic GitHub URL."""
        repo = GitHubRepo.from_url("https://github.com/octocat/hello-world")
        assert repo.owner == "octocat"
        assert repo.name == "hello-world"

    def test_from_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        repo = GitHubRepo.from_url("https://github.com/octocat/hello-world/")
        assert repo.owner == "octocat"
        assert repo.name == "hello-world"

    def test_from_url_with_git_extension(self):
        """Test parsing URL with .git extension."""
        repo = GitHubRepo.from_url("https://github.com/octocat/hello-world.git")
        assert repo.owner == "octocat"
        assert repo.name == "hello-world"

    def test_from_url_http(self):
        """Test parsing http URL."""
        repo = GitHubRepo.from_url("http://github.com/octocat/hello-world")
        assert repo.owner == "octocat"
        assert repo.name == "hello-world"

    def test_from_url_no_protocol(self):
        """Test parsing URL without protocol."""
        repo = GitHubRepo.from_url("github.com/octocat/hello-world")
        assert repo.owner == "octocat"
        assert repo.name == "hello-world"

    def test_from_url_invalid(self):
        """Test parsing invalid URL."""
        with pytest.raises(ValueError):
            GitHubRepo.from_url("invalid-url")


class TestGitHubClient:
    """Test GitHub API client."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx AsyncClient."""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def github_client(self):
        """Create GitHub client with test token."""
        return GitHubClient(access_token="test_token_123")

    @pytest.fixture
    def test_repo(self):
        """Test repository."""
        return GitHubRepo(owner="octocat", name="hello-world")

    def test_client_initialization_with_token(self):
        """Test client initialization with explicit token."""
        client = GitHubClient(access_token="my_token")
        assert client.access_token == "my_token"

    def test_client_initialization_without_token(self):
        """Test client initialization uses settings."""
        with patch("src.integrations.github_client.settings") as mock_settings:
            mock_settings.github_access_token = "settings_token"
            client = GitHubClient()
            assert client.access_token == "settings_token"

    def test_get_headers(self, github_client):
        """Test header generation."""
        headers = github_client._get_headers()

        assert "Accept" in headers
        assert headers["Accept"] == "application/vnd.github+json"
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token_123"
        assert "X-GitHub-Api-Version" in headers

    def test_get_headers_no_token(self):
        """Test header generation without token."""
        client = GitHubClient(access_token=None)
        headers = client._get_headers()

        assert "Authorization" not in headers
        assert "Accept" in headers

    async def test_create_issue_comment(self, github_client, test_repo):
        """Test creating an issue comment."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345, "body": "Test comment"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await github_client.create_issue_comment(
                test_repo, issue_number=42, comment_body="Test comment"
            )

            assert result["id"] == 12345
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "octocat/hello-world" in call_args[0][0]
            assert "issues/42/comments" in call_args[0][0]

    async def test_update_pull_request(self, github_client, test_repo):
        """Test updating a pull request."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"number": 10, "title": "Updated Title"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.patch = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await github_client.update_pull_request(
                test_repo, pr_number=10, title="Updated Title"
            )

            assert result["title"] == "Updated Title"
            mock_client.patch.assert_called_once()
            call_args = mock_client.patch.call_args
            assert "pulls/10" in call_args[0][0]

    async def test_get_pull_request(self, github_client, test_repo):
        """Test getting pull request details."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 10,
            "title": "Test PR",
            "state": "open",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await github_client.get_pull_request(test_repo, pr_number=10)

            assert result["number"] == 10
            assert result["state"] == "open"

    async def test_list_pull_requests(self, github_client, test_repo):
        """Test listing pull requests."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"number": 1, "title": "PR 1"},
            {"number": 2, "title": "PR 2"},
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await github_client.list_pull_requests(test_repo, state="open")

            assert len(result) == 2
            assert result[0]["number"] == 1

    async def test_create_pull_request(self, github_client, test_repo):
        """Test creating a pull request."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 15,
            "title": "New Feature",
            "html_url": "https://github.com/octocat/hello-world/pull/15",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await github_client.create_pull_request(
                test_repo,
                title="New Feature",
                head="feature-branch",
                base="main",
                body="Feature description",
            )

            assert result["number"] == 15
            assert result["title"] == "New Feature"
            mock_client.post.assert_called_once()

    async def test_get_repository(self, github_client, test_repo):
        """Test getting repository information."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "private": False,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await github_client.get_repository(test_repo)

            assert result["name"] == "hello-world"
            assert result["private"] is False

    async def test_check_repository_access_success(self, github_client, test_repo):
        """Test checking repository access when we have access."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "hello-world"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            has_access = await github_client.check_repository_access(test_repo)

            assert has_access is True

    async def test_check_repository_access_not_found(self, github_client, test_repo):
        """Test checking repository access when repo doesn't exist."""
        mock_response = AsyncMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Not Found", request=AsyncMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client

            has_access = await github_client.check_repository_access(test_repo)

            assert has_access is False

    async def test_api_error_handling(self, github_client, test_repo):
        """Test API error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Internal Server Error", request=AsyncMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await github_client.get_repository(test_repo)
