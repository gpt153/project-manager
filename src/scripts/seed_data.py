"""
Seed database with example projects and data for WebUI demonstration.

This script creates sample projects with conversations, vision documents,
and workflow phases to populate the WebUI with demo content.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import async_session_maker
from src.database.models import (
    CommandStatus,
    CommandType,
    ConversationMessage,
    MessageRole,
    PhaseStatus,
    Project,
    ProjectStatus,
    ScarCommandExecution,
    WorkflowPhase,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_projects(session: AsyncSession):
    """Create sample projects with realistic data."""

    # Project 1: Meal Planning App (Vision Complete)
    logger.info("Creating Project 1: Meal Planning App")
    project1 = Project(
        name="Meal Planner Pro",
        description="A meal planning app for busy parents who waste food and can't decide what to cook",
        status=ProjectStatus.PLANNING,
        vision_document={
            "title": "Meal Planner Pro",
            "overview": "An AI-powered project management agent for non-technical users",
            "target_users": ["Busy professionals", "Students"],
            "core_features": [
                {
                    "name": "Task Creation",
                    "priority": "Critical",
                    "description": "Quick task entry with rich text descriptions"
                },
                {
                    "name": "Smart Reminders",
                    "priority": "High",
                    "description": "Email and push notifications with customizable timing"
                }
            ]
        }
    )
    session.add(project1)
    await session.flush()

    # Add conversation history for project 1
    conversations1 = [
        ("user", "I want to build a meal planning app"),
        ("assistant", "Great idea! Tell me more about who will use it and what problems it solves."),
        ("user", "Busy parents who waste food and can't decide what to cook"),
        ("assistant", "Perfect! What are the key features you'd like to have?"),
        ("user", "Creating meal plans, shopping lists, and recipe suggestions"),
        ("assistant", "Excellent! I have enough information to create a vision document."),
    ]

    base_time = datetime.utcnow() - timedelta(hours=2)
    for i, (role, content) in enumerate(conversations1):
        msg = ConversationMessage(
            project_id=project1.id,
            role=MessageRole(role),
            content=content,
            timestamp=base_time + timedelta(minutes=i*5)
        )
        session.add(msg)

    # Project 2: E-Commerce Platform (In Progress)
    logger.info("Creating Project 2: E-Commerce Platform")
    project2 = Project(
        name="ShopEasy Platform",
        description="Modern e-commerce platform with AI-powered recommendations",
        status=ProjectStatus.IN_PROGRESS,
        github_repo_url="https://github.com/example/shop-easy",
    )
    session.add(project2)
    await session.flush()

    conversations2 = [
        ("user", "Help me build an e-commerce platform"),
        ("assistant", "I'd love to help! What makes your e-commerce platform unique?"),
        ("user", "AI-powered product recommendations and smart search"),
        ("assistant", "Excellent direction! Let's create a comprehensive plan."),
    ]

    base_time2 = datetime.utcnow() - timedelta(days=1)
    for i, (role, content) in enumerate(conversations2):
        msg = ConversationMessage(
            project_id=project2.id,
            role=MessageRole(role),
            content=content,
            timestamp=base_time2 + timedelta(minutes=i*10)
        )
        session.add(msg)

    # Add workflow phases for project 2
    phases = [
        ("Vision Document Review", "Review and approve the project vision", 1, True, False),
        ("Prime Context", "Load project context into SCAR", 2, True, False),
        ("Plan Feature", "Create implementation plan", 3, False, True),
        ("Execute Implementation", "Implement the planned features", 4, False, False),
    ]

    for name, desc, order, is_completed, is_current in phases:
        phase = WorkflowPhase(
            project_id=project2.id,
            name=name,
            description=desc,
            order=order,
            status=PhaseStatus.COMPLETED if is_completed else (PhaseStatus.IN_PROGRESS if is_current else PhaseStatus.PENDING),
            is_completed=is_completed,
            is_current=is_current,
        )
        session.add(phase)

    # Project 3: Fitness Tracker (Brainstorming)
    logger.info("Creating Project 3: Fitness Tracker")
    project3 = Project(
        name="FitTrack360",
        description="Comprehensive fitness and wellness tracking app",
        status=ProjectStatus.BRAINSTORMING,
    )
    session.add(project3)
    await session.flush()

    conversations3 = [
        ("user", "I have an idea for a fitness app"),
        ("assistant", "That's exciting! What specific aspect of fitness does it focus on?"),
        ("user", "Tracking workouts, nutrition, and sleep patterns all in one place"),
        ("assistant", "Interesting holistic approach! Who is your target audience?"),
        ("user", "People who want data-driven insights into their health"),
        ("assistant", "Great! Let's explore the key features you envision..."),
    ]

    base_time3 = datetime.utcnow() - timedelta(hours=5)
    for i, (role, content) in enumerate(conversations3):
        msg = ConversationMessage(
            project_id=project3.id,
            role=MessageRole(role),
            content=content,
            timestamp=base_time3 + timedelta(minutes=i*3)
        )
        session.add(msg)

    # Add some SCAR command history for project 2
    logger.info("Adding SCAR command history for project 2")

    scar_commands = [
        (CommandType.PRIME, "Load project context", CommandStatus.COMPLETED,
         "Successfully loaded project context. Repository structure analyzed."),
        (CommandType.PLAN, "Create feature plan for user authentication", CommandStatus.COMPLETED,
         "Implementation plan created with 5 phases covering authentication flow."),
    ]

    for cmd_type, cmd_args, status, output in scar_commands:
        exec_time = datetime.utcnow() - timedelta(hours=12)
        scar_exec = ScarCommandExecution(
            project_id=project2.id,
            command_type=cmd_type,
            command_args=cmd_args,
            status=status,
            started_at=exec_time,
            completed_at=exec_time + timedelta(minutes=5),
            output=output,
        )
        session.add(scar_exec)

    await session.commit()
    logger.info("✅ Seed data created successfully!")
    logger.info(f"Created {session.info.get('project_count', 3)} projects with conversations and workflow data")


async def main():
    """Main seed data function."""
    logger.info("Starting database seeding...")

    async with async_session_maker() as session:
        try:
            # Check if data already exists
            from sqlalchemy import select
            result = await session.execute(select(Project))
            existing_projects = result.scalars().all()

            if existing_projects:
                logger.warning(f"Database already has {len(existing_projects)} projects.")
                response = input("Delete existing data and reseed? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Seeding cancelled.")
                    return

                # Clear existing data
                logger.info("Clearing existing data...")
                await session.execute("DELETE FROM scar_command_executions")
                await session.execute("DELETE FROM workflow_phases")
                await session.execute("DELETE FROM conversation_messages")
                await session.execute("DELETE FROM approval_gates")
                await session.execute("DELETE FROM projects")
                await session.commit()
                logger.info("Existing data cleared.")

            await create_sample_projects(session)

        except Exception as e:
            logger.error(f"Error seeding database: {e}", exc_info=True)
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
