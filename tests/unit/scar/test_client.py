"""
Unit tests for SCAR HTTP client.

Uses respx to mock HTTP requests to SCAR Test Adapter API.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

import httpx
import pytest
import respx
from respx import MockRouter

from src.config import Settings
from src.scar.client import ScarClient
from src.scar.types import ScarMessage


@pytest.fixture
def settings():
    """Test settings with SCAR configuration"""
    return Settings(
        scar_base_url="http://localhost:3000",
        scar_timeout_seconds=300,
        scar_conversation_prefix="pm-project-",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
    )


@pytest.fixture
def client(settings):
    """SCAR client instance for testing"""
    return ScarClient(settings)


@pytest.fixture
def project_id():
    """Test project UUID"""
    return uuid4()


class TestSendCommand:
    """Tests for ScarClient.send_command()"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_command_success(self, client: ScarClient, project_id, respx_mock: MockRouter):
        """Test successfully sending a command to SCAR"""
        # Mock POST /test/message
        respx_mock.post("http://localhost:3000/test/message").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        # Send command
        conversation_id = await client.send_command(project_id, "prime")

        # Verify conversation ID format
        assert conversation_id == f"pm-project-{project_id}"

        # Verify request was made
        assert len(respx_mock.calls) == 1
        request = respx_mock.calls[0].request
        assert request.method == "POST"

        # Verify request body
        body = request.content.decode()
        assert f"pm-project-{project_id}" in body
        assert "/command-invoke prime" in body

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_command_with_args(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test sending command with arguments"""
        respx_mock.post("http://localhost:3000/test/message").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await client.send_command(project_id, "plan-feature-github", ["Add dark mode"])

        # Verify command includes quoted args (JSON escapes quotes)
        request = respx_mock.calls[0].request
        body = request.content.decode()
        assert '/command-invoke plan-feature-github \\"Add dark mode\\"' in body

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_command_args_without_spaces(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test args without spaces are not quoted"""
        respx_mock.post("http://localhost:3000/test/message").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await client.send_command(project_id, "validate", ["arg1", "arg2"])

        request = respx_mock.calls[0].request
        body = request.content.decode()
        assert "/command-invoke validate arg1 arg2" in body

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_command_connection_error(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test handling connection error when SCAR is not running"""
        respx_mock.post("http://localhost:3000/test/message").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(httpx.ConnectError):
            await client.send_command(project_id, "prime")


class TestGetMessages:
    """Tests for ScarClient.get_messages()"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_messages_empty(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test getting messages from empty conversation"""
        conversation_id = f"pm-project-{project_id}"

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            return_value=httpx.Response(
                200, json={"conversationId": conversation_id, "messages": []}
            )
        )

        messages = await client.get_messages(conversation_id)

        assert messages == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_messages_single_message(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test getting single bot message"""
        conversation_id = f"pm-project-{project_id}"

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "conversationId": conversation_id,
                    "messages": [
                        {
                            "message": "Primed successfully",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "direction": "sent",
                        }
                    ],
                },
            )
        )

        messages = await client.get_messages(conversation_id)

        assert len(messages) == 1
        assert messages[0].message == "Primed successfully"
        assert messages[0].direction == "sent"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_messages_filters_received(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test that only bot messages (direction=sent) are returned"""
        conversation_id = f"pm-project-{project_id}"

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "conversationId": conversation_id,
                    "messages": [
                        {
                            "message": "/command-invoke prime",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "direction": "received",
                        },
                        {
                            "message": "Priming...",
                            "timestamp": "2024-01-01T00:00:01Z",
                            "direction": "sent",
                        },
                        {
                            "message": "Done",
                            "timestamp": "2024-01-01T00:00:02Z",
                            "direction": "sent",
                        },
                    ],
                },
            )
        )

        messages = await client.get_messages(conversation_id)

        # Should only get the 2 bot messages
        assert len(messages) == 2
        assert all(msg.direction == "sent" for msg in messages)
        assert messages[0].message == "Priming..."
        assert messages[1].message == "Done"


class TestClearMessages:
    """Tests for ScarClient.clear_messages()"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_clear_messages_success(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test clearing conversation messages"""
        conversation_id = f"pm-project-{project_id}"

        respx_mock.delete(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await client.clear_messages(conversation_id)

        # Verify DELETE request was made
        assert len(respx_mock.calls) == 1
        assert respx_mock.calls[0].request.method == "DELETE"


class TestWaitForCompletion:
    """Tests for ScarClient.wait_for_completion()"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_wait_for_completion_immediate(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test waiting when command completes immediately"""
        conversation_id = f"pm-project-{project_id}"

        # Mock: First 2 polls return same message (stable)
        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "conversationId": conversation_id,
                    "messages": [
                        {
                            "message": "Done",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "direction": "sent",
                        }
                    ],
                },
            )
        )

        messages = await client.wait_for_completion(conversation_id, poll_interval=0.1)

        assert len(messages) == 1
        assert messages[0].message == "Done"

        # Should have polled at least 2 times for stability
        assert len(respx_mock.calls) >= 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_wait_for_completion_streaming(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test waiting with streaming messages (multiple responses)"""
        conversation_id = f"pm-project-{project_id}"

        # Simulate streaming: messages accumulate over time
        call_count = 0

        def dynamic_response(request):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First poll: 1 message
                messages = [
                    {
                        "message": "Starting...",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    }
                ]
            elif call_count == 2:
                # Second poll: 2 messages
                messages = [
                    {
                        "message": "Starting...",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    },
                    {
                        "message": "Processing...",
                        "timestamp": "2024-01-01T00:00:01Z",
                        "direction": "sent",
                    },
                ]
            else:
                # Subsequent polls: stable with 3 messages
                messages = [
                    {
                        "message": "Starting...",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    },
                    {
                        "message": "Processing...",
                        "timestamp": "2024-01-01T00:00:01Z",
                        "direction": "sent",
                    },
                    {
                        "message": "Done",
                        "timestamp": "2024-01-01T00:00:02Z",
                        "direction": "sent",
                    },
                ]

            return httpx.Response(
                200, json={"conversationId": conversation_id, "messages": messages}
            )

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            side_effect=dynamic_response
        )

        messages = await client.wait_for_completion(conversation_id, poll_interval=0.1)

        # Should get all 3 messages
        assert len(messages) == 3
        assert messages[0].message == "Starting..."
        assert messages[1].message == "Processing..."
        assert messages[2].message == "Done"

    @pytest.mark.asyncio
    @respx.mock
    async def test_wait_for_completion_timeout(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test timeout when command never completes"""
        conversation_id = f"pm-project-{project_id}"

        # Mock: Always return new messages (never stable)
        call_count = 0

        def never_stable(request):
            nonlocal call_count
            call_count += 1
            # Always add new message to prevent stability
            messages = [
                {
                    "message": f"Message {i}",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "direction": "sent",
                }
                for i in range(call_count)
            ]
            return httpx.Response(
                200, json={"conversationId": conversation_id, "messages": messages}
            )

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            side_effect=never_stable
        )

        with pytest.raises(TimeoutError, match="SCAR command timed out"):
            await client.wait_for_completion(
                conversation_id, timeout=0.5, poll_interval=0.1
            )


class TestBuildConversationId:
    """Tests for conversation ID building"""

    def test_build_conversation_id_format(self, client: ScarClient, project_id):
        """Test conversation ID format is correct"""
        conversation_id = client._build_conversation_id(project_id)

        assert conversation_id.startswith("pm-project-")
        assert str(project_id) in conversation_id
        assert conversation_id == f"pm-project-{project_id}"
