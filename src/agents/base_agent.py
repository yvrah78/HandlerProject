"""
Base agent class for Project Handler multi-agent system.
All specialized agents inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from src.core.logging import get_logger
from src.core.exceptions import AgentError


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    All agents must implement process() and validate_input() methods.
    Provides common functionality for status tracking and error handling.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize base agent.

        Args:
            name: Unique name for the agent
            description: Optional description of agent's purpose
        """
        self.name = name
        self.description = description or f"{name} Agent"
        self.status = "initialized"
        self.logger = get_logger(f"agent.{name}")
        self.created_at = datetime.utcnow()
        self.last_execution = None

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return result.

        Args:
            input_data: Input data dictionary for processing

        Returns:
            Dict[str, Any]: Processed result

        Raises:
            AgentError: If processing fails
        """
        pass

    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing.

        Args:
            input_data: Input data to validate

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValidationError: If validation fails with details
        """
        pass

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with validation and error handling.

        Args:
            input_data: Input data for processing

        Returns:
            Dict[str, Any]: Execution result

        Raises:
            AgentError: If execution fails
        """
        try:
            self.logger.info(f"Agent {self.name} starting execution")
            self.status = "running"

            # Validate input
            if not await self.validate_input(input_data):
                raise AgentError(
                    f"Invalid input data for agent {self.name}",
                    agent_name=self.name,
                    details={"input": input_data}
                )

            # Process request
            result = await self.process(input_data)

            # Update status
            self.status = "completed"
            self.last_execution = datetime.utcnow()
            self.logger.info(f"Agent {self.name} completed successfully")

            return {
                "success": True,
                "agent": self.name,
                "result": result,
                "timestamp": self.last_execution.isoformat()
            }

        except Exception as e:
            self.status = "failed"
            self.logger.error(f"Agent {self.name} failed: {str(e)}")
            raise AgentError(
                f"Agent {self.name} execution failed: {str(e)}",
                agent_name=self.name,
                details={"error": str(e), "input": input_data}
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Dict[str, Any]: Status information
        """
        return {
            "agent": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_execution": self.last_execution.isoformat() if self.last_execution else None
        }

    def reset(self) -> None:
        """Reset agent to initial state."""
        self.status = "initialized"
        self.last_execution = None
        self.logger.info(f"Agent {self.name} reset to initial state")
