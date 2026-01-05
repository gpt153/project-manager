"""
Database models for the Project Manager.

This module defines all SQLAlchemy models for tracking projects, conversations,
workflow phases, approval gates, and SCAR command executions.
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Enums
class ProjectStatus(str, enum.Enum):
    """Project lifecycle status"""

    BRAINSTORMING = "BRAINSTORMING"
    VISION_REVIEW = "VISION_REVIEW"
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class MessageRole(str, enum.Enum):
    """Conversation message roles"""

    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class PhaseStatus(str, enum.Enum):
    """Workflow phase status"""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class GateType(str, enum.Enum):
    """Approval gate types"""

    VISION_DOC = "VISION_DOC"
    PHASE_START = "PHASE_START"
    PHASE_COMPLETE = "PHASE_COMPLETE"
    ERROR_RESOLUTION = "ERROR_RESOLUTION"


class GateStatus(str, enum.Enum):
    """Approval gate status"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class CommandType(str, enum.Enum):
    """SCAR command types"""

    PRIME = "PRIME"
    PLAN_FEATURE = "PLAN_FEATURE"
    PLAN_FEATURE_GITHUB = "PLAN_FEATURE_GITHUB"
    EXECUTE = "EXECUTE"
    EXECUTE_GITHUB = "EXECUTE_GITHUB"
    VALIDATE = "VALIDATE"


class ExecutionStatus(str, enum.Enum):
    """Command execution status"""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Models
class Project(Base):
    """Main project entity tracking the software development project"""

    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    github_repo_url = Column(String(500), nullable=True)
    telegram_chat_id = Column(BigInteger, nullable=True)
    github_issue_number = Column(Integer, nullable=True)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.BRAINSTORMING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    vision_document = Column(JSONB, nullable=True)

    # Relationships
    conversation_messages = relationship(
        "ConversationMessage", back_populates="project", cascade="all, delete-orphan"
    )
    workflow_phases = relationship(
        "WorkflowPhase", back_populates="project", cascade="all, delete-orphan"
    )
    approval_gates = relationship(
        "ApprovalGate", back_populates="project", cascade="all, delete-orphan"
    )
    scar_executions = relationship(
        "ScarCommandExecution", back_populates="project", cascade="all, delete-orphan"
    )

    # Alias for backward compatibility with web UI
    @property
    def messages(self):
        """Alias for conversation_messages (web UI compatibility)"""
        return self.conversation_messages

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"


class ConversationMessage(Base):
    """Stores conversation history for projects"""

    __tablename__ = "conversation_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_metadata = Column(JSONB, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="conversation_messages")

    # Note: 'metadata' property removed - conflicts with SQLAlchemy reserved name
    # Web UI should use 'message_metadata' field directly

    @property
    def created_at(self):
        """Alias for timestamp (web UI compatibility)"""
        return self.timestamp

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role={self.role}, timestamp={self.timestamp})>"


class WorkflowPhase(Base):
    """Tracks workflow phases for a project"""

    __tablename__ = "workflow_phases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(PhaseStatus), nullable=False, default=PhaseStatus.PENDING)
    scar_command = Column(String(100), nullable=True)
    branch_name = Column(String(255), nullable=True)
    pr_url = Column(String(500), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="workflow_phases")
    scar_executions = relationship(
        "ScarCommandExecution", back_populates="phase", cascade="all, delete-orphan"
    )

    # Backward compatibility properties for web UI
    @property
    def order(self):
        """Alias for phase_number (web UI compatibility)"""
        return self.phase_number

    @property
    def is_completed(self):
        """Check if phase is completed (web UI compatibility)"""
        return self.status == PhaseStatus.COMPLETED

    @property
    def is_current(self):
        """Check if phase is current (web UI compatibility)"""
        return self.status == PhaseStatus.IN_PROGRESS

    @property
    def created_at(self):
        """Alias for started_at (web UI compatibility)"""
        return self.started_at

    def __repr__(self) -> str:
        return f"<WorkflowPhase(id={self.id}, name={self.name}, status={self.status})>"


class ApprovalGate(Base):
    """Manages approval gates for user decisions"""

    __tablename__ = "approval_gates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    phase_id = Column(PGUUID(as_uuid=True), ForeignKey("workflow_phases.id"), nullable=True)
    gate_type = Column(Enum(GateType), nullable=False)
    question = Column(Text, nullable=False)
    context = Column(JSONB, nullable=True)
    status = Column(Enum(GateStatus), nullable=False, default=GateStatus.PENDING)
    user_response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="approval_gates")

    # Backward compatibility properties for web UI
    @property
    def approved(self):
        """Check if gate is approved (web UI compatibility)"""
        return self.status == GateStatus.APPROVED if self.status else None

    @property
    def decided_at(self):
        """Alias for responded_at (web UI compatibility)"""
        return self.responded_at

    def __repr__(self) -> str:
        return f"<ApprovalGate(id={self.id}, type={self.gate_type}, status={self.status})>"


class ScarCommandExecution(Base):
    """Tracks SCAR command executions"""

    __tablename__ = "scar_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    phase_id = Column(PGUUID(as_uuid=True), ForeignKey("workflow_phases.id"), nullable=True)
    command_type = Column(Enum(CommandType), nullable=False)
    command_args = Column(Text, nullable=False)
    branch_name = Column(String(255), nullable=True)
    status = Column(Enum(ExecutionStatus), nullable=False, default=ExecutionStatus.QUEUED)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="scar_executions")
    phase = relationship("WorkflowPhase", back_populates="scar_executions")

    # Backward compatibility properties for web UI
    @property
    def command(self):
        """Get command name (web UI compatibility)"""
        return self.command_type.value if self.command_type else None

    @property
    def source(self):
        """Default source (web UI compatibility)"""
        return "scar"

    @property
    def message(self):
        """Get message from output or command args (web UI compatibility)"""
        return self.output or self.command_args

    @property
    def verbosity_level(self):
        """Default verbosity level (web UI compatibility)"""
        return 2

    # Note: 'metadata' property removed - conflicts with SQLAlchemy reserved name
    # Web UI should use a different approach if metadata dict is needed

    @property
    def created_at(self):
        """Alias for started_at (web UI compatibility)"""
        return self.started_at or datetime.utcnow()

    def __repr__(self) -> str:
        return (
            f"<ScarCommandExecution(id={self.id}, type={self.command_type}, status={self.status})>"
        )
