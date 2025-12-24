"""
Vision Document Generation Service.

This service handles the generation of vision documents from brainstorming
conversations. It checks conversation completeness, extracts features,
and generates structured vision documents in markdown format.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.prompts import (
    CONVERSATION_COMPLETENESS_CHECK_PROMPT,
    FEATURE_EXTRACTION_PROMPT,
    VISION_GENERATION_PROMPT_TEMPLATE,
)
from src.agent.tools import get_conversation_history
from src.database.models import ConversationMessage


class Feature(BaseModel):
    """A feature extracted from conversation"""

    name: str = Field(..., description="Short, descriptive feature name")
    description: str = Field(..., description="What it does in plain English")
    priority: str = Field(..., description="HIGH, MEDIUM, or LOW")


class VisionDocument(BaseModel):
    """Structured vision document model"""

    what_it_is: str = Field(..., description="One paragraph overview")
    who_its_for: list[str] = Field(..., description="Primary and secondary users")
    problem_statement: str = Field(..., description="Problem being solved")
    solution_overview: str = Field(..., description="How it solves the problem")
    key_features: list[Feature] = Field(..., description="List of key features")
    user_journey: str = Field(..., description="Story of product usage")
    success_metrics: list[str] = Field(..., description="Measurable goals")
    out_of_scope: list[str] = Field(..., description="What we're NOT building")


class CompletenessCheck(BaseModel):
    """Result of conversation completeness check"""

    is_ready: bool = Field(..., description="Whether conversation has enough info")
    next_question: Optional[str] = Field(None, description="Next question to ask if not ready")


# Agent instances - lazily initialized to avoid requiring API key at import time
_completeness_agent: Optional[Agent] = None
_feature_extraction_agent: Optional[Agent] = None
_vision_generation_agent: Optional[Agent] = None


def _get_completeness_agent() -> Agent:
    """Get or create the completeness checking agent"""
    global _completeness_agent
    if _completeness_agent is None:
        _completeness_agent = Agent(
            model="anthropic:claude-sonnet-4-20250514",
            result_type=CompletenessCheck,
            system_prompt="You are an expert at evaluating whether conversations contain enough information to generate comprehensive vision documents.",
        )
    return _completeness_agent


def _get_feature_extraction_agent() -> Agent:
    """Get or create the feature extraction agent"""
    global _feature_extraction_agent
    if _feature_extraction_agent is None:
        _feature_extraction_agent = Agent(
            model="anthropic:claude-sonnet-4-20250514",
            result_type=list[Feature],
            system_prompt="You are an expert at extracting and structuring features from natural conversations.",
        )
    return _feature_extraction_agent


def _get_vision_generation_agent() -> Agent:
    """Get or create the vision generation agent"""
    global _vision_generation_agent
    if _vision_generation_agent is None:
        _vision_generation_agent = Agent(
            model="anthropic:claude-sonnet-4-20250514",
            result_type=VisionDocument,
            system_prompt="You are an expert at creating clear, non-technical vision documents that make complex projects accessible to anyone.",
        )
    return _vision_generation_agent


# Public aliases for testability (tests mock these)
completeness_agent = _get_completeness_agent()
feature_extraction_agent = _get_feature_extraction_agent()
vision_generation_agent = _get_vision_generation_agent()


def _format_conversation_history(messages: list[ConversationMessage]) -> str:
    """
    Format conversation messages into a readable string.

    Args:
        messages: List of conversation messages

    Returns:
        str: Formatted conversation history
    """
    formatted = []
    for msg in messages:
        role = msg.role.value.title()
        formatted.append(f"{role}: {msg.content}")
    return "\n\n".join(formatted)


async def check_conversation_completeness(
    session: AsyncSession, project_id: UUID
) -> CompletenessCheck:
    """
    Check if conversation has enough information for vision document.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        CompletenessCheck: Result with is_ready flag and optional next question
    """
    # Get conversation history
    messages = await get_conversation_history(session, project_id)

    if not messages:
        return CompletenessCheck(
            is_ready=False,
            next_question="Could you tell me about the project you'd like to build?",
        )

    # Format conversation for analysis
    conversation_text = _format_conversation_history(messages)

    # Create prompt with conversation
    prompt = CONVERSATION_COMPLETENESS_CHECK_PROMPT.format(conversation_history=conversation_text)

    # Run completeness check
    agent = _get_completeness_agent()
    result = await agent.run(prompt)

    return result.data


async def extract_features(session: AsyncSession, project_id: UUID) -> list[Feature]:
    """
    Extract features from conversation history.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        list[Feature]: Extracted features with priorities
    """
    # Get conversation history
    messages = await get_conversation_history(session, project_id)

    if not messages:
        return []

    # Format conversation for analysis
    conversation_text = _format_conversation_history(messages)

    # Create prompt with conversation
    prompt = FEATURE_EXTRACTION_PROMPT.format(conversation_history=conversation_text)

    # Run feature extraction
    agent = _get_feature_extraction_agent()
    result = await agent.run(prompt)

    return result.data


async def generate_vision_document(session: AsyncSession, project_id: UUID) -> VisionDocument:
    """
    Generate a complete vision document from conversation.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        VisionDocument: Structured vision document

    Raises:
        ValueError: If conversation doesn't have enough information
    """
    # First check if conversation is complete
    completeness = await check_conversation_completeness(session, project_id)

    if not completeness.is_ready:
        raise ValueError(
            f"Conversation not ready for vision document. "
            f"Need more info: {completeness.next_question}"
        )

    # Get conversation history
    messages = await get_conversation_history(session, project_id)
    conversation_text = _format_conversation_history(messages)

    # Create prompt with conversation
    prompt = VISION_GENERATION_PROMPT_TEMPLATE.format(conversation_history=conversation_text)

    # Generate vision document
    agent = _get_vision_generation_agent()
    result = await agent.run(prompt)

    return result.data


def vision_document_to_markdown(vision: VisionDocument) -> str:
    """
    Convert vision document to markdown format.

    Args:
        vision: VisionDocument object

    Returns:
        str: Markdown formatted document
    """
    md_parts = [
        "# Project Vision Document",
        "",
        "## What It Is",
        vision.what_it_is,
        "",
        "## Who It's For",
    ]

    for user_type in vision.who_its_for:
        md_parts.append(f"- {user_type}")

    md_parts.extend(
        [
            "",
            "## Problem Statement",
            vision.problem_statement,
            "",
            "## Solution Overview",
            vision.solution_overview,
            "",
            "## Key Features",
        ]
    )

    for feature in vision.key_features:
        md_parts.append(f"### {feature.name} ({feature.priority} Priority)")
        md_parts.append(feature.description)
        md_parts.append("")

    md_parts.extend(
        [
            "## User Journey",
            vision.user_journey,
            "",
            "## Success Metrics",
        ]
    )

    for metric in vision.success_metrics:
        md_parts.append(f"- {metric}")

    md_parts.extend(["", "## Out of Scope (for MVP)"])

    for item in vision.out_of_scope:
        md_parts.append(f"- {item}")

    return "\n".join(md_parts)


def vision_document_to_dict(vision: VisionDocument) -> dict:
    """
    Convert vision document to dictionary for JSON storage.

    Args:
        vision: VisionDocument object

    Returns:
        dict: Dictionary representation
    """
    return {
        "what_it_is": vision.what_it_is,
        "who_its_for": vision.who_its_for,
        "problem_statement": vision.problem_statement,
        "solution_overview": vision.solution_overview,
        "key_features": [
            {
                "name": f.name,
                "description": f.description,
                "priority": f.priority,
            }
            for f in vision.key_features
        ],
        "user_journey": vision.user_journey,
        "success_metrics": vision.success_metrics,
        "out_of_scope": vision.out_of_scope,
    }
