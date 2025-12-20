"""
Tests for GitHub webhook integration.
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.database.models import Project, ProjectStatus
from src.integrations.github_webhook import (
    get_project_by_repo,
    handle_issue_comment,
    verify_github_signature,
)


@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    from fastapi.testclient import TestClient
    from src.main import app

    return TestClient(app)


@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "test_webhook_secret_123"


@pytest.fixture
def sample_issue_comment_payload():
    """Sample issue comment webhook payload."""
    return {
        "action": "created",
        "issue": {
            "number": 42,
            "title": "Test Issue",
            "html_url": "https://github.com/owner/repo/issues/42",
        },
        "comment": {
            "id": 1234567890,
            "body": "@po please help me with authentication",
            "user": {"login": "testuser"},
            "html_url": "https://github.com/owner/repo/issues/42#issuecomment-1234567890",
        },
        "repository": {
            "name": "repo",
            "full_name": "owner/repo",
            "html_url": "https://github.com/owner/repo",
        },
    }


@pytest.fixture
def sample_pull_request_payload():
    """Sample pull request webhook payload."""
    return {
        "action": "opened",
        "number": 10,
        "pull_request": {
            "number": 10,
            "title": "Add new feature",
            "html_url": "https://github.com/owner/repo/pull/10",
            "state": "open",
            "merged": False,
        },
        "repository": {
            "name": "repo",
            "full_name": "owner/repo",
            "html_url": "https://github.com/owner/repo",
        },
    }


class TestSignatureVerification:
    """Test webhook signature verification."""

    def test_verify_valid_signature(self, webhook_secret):
        """Test verifying a valid signature."""
        payload = b'{"test": "data"}'
        mac = hmac.new(webhook_secret.encode(), msg=payload, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        with patch("src.integrations.github_webhook.settings") as mock_settings:
            mock_settings.github_webhook_secret = webhook_secret
            assert verify_github_signature(payload, signature) is True

    def test_verify_invalid_signature(self, webhook_secret):
        """Test rejecting an invalid signature."""
        payload = b'{"test": "data"}'
        signature = "sha256=invalid_signature_here"

        with patch("src.integrations.github_webhook.settings") as mock_settings:
            mock_settings.github_webhook_secret = webhook_secret
            assert verify_github_signature(payload, signature) is False

    def test_verify_no_secret_configured(self):
        """Test that verification passes when no secret is configured (dev mode)."""
        payload = b'{"test": "data"}'
        signature = "sha256=anything"

        with patch("src.integrations.github_webhook.settings") as mock_settings:
            mock_settings.github_webhook_secret = None
            assert verify_github_signature(payload, signature) is True

    def test_verify_wrong_algorithm(self, webhook_secret):
        """Test rejecting wrong hash algorithm."""
        payload = b'{"test": "data"}'
        signature = "sha1=some_hash"

        with patch("src.integrations.github_webhook.settings") as mock_settings:
            mock_settings.github_webhook_secret = webhook_secret
            assert verify_github_signature(payload, signature) is False


class TestProjectLookup:
    """Test project repository lookup."""

    async def test_get_project_by_repo(self, db_session):
        """Test finding project by repository URL."""
        # Create test project
        project = Project(
            name="Test Project",
            status=ProjectStatus.BRAINSTORMING,
            github_repo_url="https://github.com/owner/test-repo",
        )
        db_session.add(project)
        await db_session.commit()

        # Find by exact URL
        found = await get_project_by_repo(db_session, "https://github.com/owner/test-repo")
        assert found is not None
        assert found.id == project.id

        # Find by URL without trailing slash
        found = await get_project_by_repo(db_session, "https://github.com/owner/test-repo/")
        assert found is not None

        # Find by URL with .git
        found = await get_project_by_repo(db_session, "https://github.com/owner/test-repo.git")
        assert found is not None

    async def test_get_project_not_found(self, db_session):
        """Test when project is not found."""
        found = await get_project_by_repo(db_session, "https://github.com/owner/nonexistent")
        assert found is None


class TestIssueCommentHandling:
    """Test issue comment webhook handling."""

    async def test_handle_issue_comment_with_mention(
        self, db_session, sample_issue_comment_payload
    ):
        """Test handling issue comment with bot mention."""
        # Create test project
        project = Project(
            name="Test Project",
            status=ProjectStatus.BRAINSTORMING,
            github_repo_url="https://github.com/owner/repo",
        )
        db_session.add(project)
        await db_session.commit()

        # Mock the orchestrator agent
        with patch("src.integrations.github_webhook.run_orchestrator") as mock_orchestrator:
            mock_orchestrator.return_value = "I can help you with authentication!"

            result = await handle_issue_comment(sample_issue_comment_payload, db_session)

            assert result["status"] == "success"
            assert result["project_id"] == str(project.id)
            assert result["issue_number"] == 42
            assert "authentication" in result["response"]

            # Verify orchestrator was called
            mock_orchestrator.assert_called_once()
            call_args = mock_orchestrator.call_args
            assert call_args[0][0] == project.id  # project_id
            assert "please help me with authentication" in call_args[0][1]  # user message

    async def test_handle_issue_comment_no_mention(
        self, db_session, sample_issue_comment_payload
    ):
        """Test ignoring comment without bot mention."""
        sample_issue_comment_payload["comment"]["body"] = "Just a regular comment"

        result = await handle_issue_comment(sample_issue_comment_payload, db_session)

        assert result["status"] == "ignored"
        assert result["reason"] == "Bot not mentioned"

    async def test_handle_issue_comment_project_not_found(
        self, db_session, sample_issue_comment_payload
    ):
        """Test handling comment when project doesn't exist."""
        result = await handle_issue_comment(sample_issue_comment_payload, db_session)

        assert result["status"] == "error"
        assert "not found" in result["reason"].lower()

    async def test_handle_issue_comment_edited(self, db_session, sample_issue_comment_payload):
        """Test ignoring edited comments."""
        sample_issue_comment_payload["action"] = "edited"

        result = await handle_issue_comment(sample_issue_comment_payload, db_session)

        assert result["status"] == "ignored"
        assert result["reason"] == "Not a created comment"


class TestWebhookEndpoint:
    """Test webhook endpoint integration."""

    def test_ping_event(self, test_client):
        """Test ping event from GitHub."""
        payload = {"zen": "Design for failure."}

        with patch("src.integrations.github_webhook.verify_github_signature", return_value=True):
            response = test_client.post(
                "/webhooks/github/",
                json=payload,
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": "sha256=test",
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "Pong" in response.json()["message"]

    def test_invalid_signature(self, test_client):
        """Test rejecting request with invalid signature."""
        payload = {"test": "data"}

        with patch(
            "src.integrations.github_webhook.verify_github_signature", return_value=False
        ):
            response = test_client.post(
                "/webhooks/github/",
                json=payload,
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": "sha256=invalid",
                },
            )

        assert response.status_code == 401

    def test_webhook_health_endpoint(self, test_client):
        """Test webhook health check endpoint."""
        response = test_client.get("/webhooks/github/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "webhook_secret_configured" in data
        assert "github_token_configured" in data
