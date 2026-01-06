"""
PydanticAI mocking utilities for testing.

Provides mock implementations of PydanticAI agent components.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class MockAgentResult:
    """Mock PydanticAI agent result"""

    def __init__(self, data: Any):
        self.data = data
        self.cost = None
        self.usage = None


class MockAgent:
    """
    Mock PydanticAI agent for testing.

    Provides a simplified interface that mimics pydantic_ai.Agent behavior.
    """

    def __init__(self, response_data: Optional[Any] = None):
        """
        Initialize mock agent.

        Args:
            response_data: Data to return from run() calls
        """
        self.response_data = response_data or {"message": "Mock response"}
        self.run_calls = []

    async def run(
        self, prompt: str, deps: Any = None, result_type: Optional[type] = None
    ) -> MockAgentResult:
        """
        Mock agent run method.

        Args:
            prompt: User prompt
            deps: Dependencies
            result_type: Expected result type

        Returns:
            MockAgentResult with mocked data
        """
        # Track call for assertions
        self.run_calls.append({"prompt": prompt, "deps": deps, "result_type": result_type})

        # Return typed result if result_type specified
        if result_type and issubclass(result_type, BaseModel):
            if hasattr(result_type, "model_validate"):
                data = result_type.model_validate(self.response_data)
            else:
                data = result_type(**self.response_data)
            return MockAgentResult(data)

        return MockAgentResult(self.response_data)


def create_mock_agent(response: Optional[Dict[str, Any]] = None) -> MockAgent:
    """
    Create a mock PydanticAI agent.

    Args:
        response: Response data to return from agent.run()

    Returns:
        MockAgent instance
    """
    return MockAgent(response)


def create_mock_vision_document() -> Dict[str, Any]:
    """
    Create mock vision document data.

    Returns:
        Dictionary with vision document structure
    """
    return {
        "title": "Test Project",
        "overview": "A test project for mocking",
        "target_users": ["Test users"],
        "problem_statement": "Test problem",
        "solution_overview": "Test solution",
        "features": [
            {"name": "Test Feature 1", "description": "First test feature", "priority": "high"},
            {"name": "Test Feature 2", "description": "Second test feature", "priority": "medium"},
        ],
        "success_metrics": ["Test metric 1", "Test metric 2"],
        "out_of_scope": ["Test exclusion"],
    }
