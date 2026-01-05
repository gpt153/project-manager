"""
Type definitions for SCAR Test Adapter API.

These types mirror the request/response format of SCAR's HTTP Test Adapter
at endpoints: POST /test/message, GET /test/messages/:id, DELETE /test/messages/:id
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ScarMessageRequest(BaseModel):
    """Request body for POST /test/message"""

    conversationId: str = Field(
        ..., description="Unique conversation ID (format: pm-project-{uuid})"
    )
    message: str = Field(..., description="Command to send to SCAR (e.g., '/status')")


class ScarMessage(BaseModel):
    """A single message in SCAR conversation"""

    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    direction: Literal["sent", "received"] = Field(
        ..., description="Message direction: 'sent' by bot, 'received' from user"
    )


class ScarMessagesResponse(BaseModel):
    """Response body for GET /test/messages/:id"""

    conversationId: str = Field(..., description="Conversation ID")
    messages: list[ScarMessage] = Field(default_factory=list, description="All messages")
