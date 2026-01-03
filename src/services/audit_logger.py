"""
Audit logging service for tracking state-changing operations.

Provides structured logging of all critical actions for security auditing.
"""
import json
import logging
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID


class AuditLogger:
    """
    Audit logger for tracking state-changing operations.

    Logs all critical actions to a dedicated audit log file for security
    monitoring and compliance.
    """

    def __init__(self, log_file: str = "logs/audit.log"):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file
        """
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Add file handler for audit logs
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

        # Also log to console in development
        if os.getenv("APP_ENV", "development") == "development":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(console_handler)

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        project_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        result: str = "success",
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log an audit event.

        Args:
            action: Action being performed (e.g., "project_created", "workflow_started")
            user_id: User ID performing the action
            project_id: Project ID affected
            details: Additional context details
            result: Result of action ("success" or "failure")
            ip_address: IP address of requester
        """
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "user_id": user_id,
            "project_id": str(project_id) if project_id else None,
            "details": details or {},
            "result": result,
            "ip_address": ip_address
        }
        self.logger.info(json.dumps(event))

    def log_project_created(self, project_id: UUID, user_id: str, name: str) -> None:
        """Log project creation."""
        self.log(
            action="project_created",
            user_id=user_id,
            project_id=project_id,
            details={"name": name}
        )

    def log_workflow_started(self, project_id: UUID, workflow_phase: str) -> None:
        """Log workflow phase start."""
        self.log(
            action="workflow_started",
            project_id=project_id,
            details={"phase": workflow_phase}
        )

    def log_approval_granted(self, project_id: UUID, approval_type: str, user_id: str) -> None:
        """Log approval gate approval."""
        self.log(
            action="approval_granted",
            user_id=user_id,
            project_id=project_id,
            details={"approval_type": approval_type}
        )

    def log_scar_command(self, project_id: UUID, command_type: str, branch: Optional[str] = None) -> None:
        """Log SCAR command execution."""
        self.log(
            action="scar_command_executed",
            project_id=project_id,
            details={"command_type": command_type, "branch": branch}
        )


# Global instance
audit_logger = AuditLogger()
