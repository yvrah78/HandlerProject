"""
Base Tool class for Project Handler agents.
Provides abstract interface for tool implementation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class ToolInput(BaseModel):
    """Base model for tool input validation."""

    class Config:
        extra = "allow"  # Allow extra fields


class ToolOutput(BaseModel):
    """Base model for tool output."""

    success: bool = Field(..., description="Whether tool executed successfully")
    data: Any = Field(default=None, description="Tool result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Execution timestamp",
    )


class BaseTool(ABC):
    """
    Abstract base class for agent tools.

    Tools represent actions or capabilities that agents can use.
    Each tool has input validation, execution logic, and output formatting.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Optional[Type[ToolInput]] = None,
        required_permissions: Optional[List[str]] = None,
    ):
        """
        Initialize base tool.

        Args:
            name: Unique tool name
            description: Tool description
            input_schema: Pydantic model for input validation
            required_permissions: List of required permissions
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema or ToolInput
        self.required_permissions = required_permissions or []
        self.execution_count = 0
        self.last_execution = None
        self.created_at = datetime.utcnow()

        logger.info(f"Tool initialized: {self.name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Execute the tool.

        Args:
            input_data: Input data for the tool

        Returns:
            ToolOutput: Tool execution result

        Raises:
            Exception: If execution fails
        """
        pass

    async def run(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Run tool with validation and error handling.

        Args:
            input_data: Input data for the tool

        Returns:
            ToolOutput: Tool execution result
        """
        try:
            # Validate input
            try:
                validated_input = self.input_schema(**input_data)
                input_dict = validated_input.dict()
            except Exception as e:
                logger.error(f"Input validation failed for tool {self.name}: {str(e)}")
                return ToolOutput(
                    success=False,
                    error=f"Invalid input: {str(e)}",
                )

            # Execute tool
            logger.info(f"Executing tool: {self.name}")
            result = await self.execute(input_dict)

            # Update stats
            self.execution_count += 1
            self.last_execution = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {self.name}: {str(e)}")
            return ToolOutput(
                success=False,
                error=f"Tool execution failed: {str(e)}",
            )

    def get_info(self) -> Dict[str, Any]:
        """
        Get tool information.

        Returns:
            Dict[str, Any]: Tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat()
            if self.last_execution
            else None,
            "created_at": self.created_at.isoformat(),
            "required_permissions": self.required_permissions,
        }

    def get_schema(self) -> Dict[str, Any]:
        """
        Get input schema for the tool.

        Returns:
            Dict[str, Any]: JSON schema of input
        """
        if self.input_schema:
            return self.input_schema.schema()
        return {}

    def check_permission(self, permission: str) -> bool:
        """
        Check if tool has required permission.

        Args:
            permission: Permission to check

        Returns:
            bool: True if has permission
        """
        return permission in self.required_permissions

    def has_all_permissions(self, permissions: List[str]) -> bool:
        """
        Check if tool has all required permissions.

        Args:
            permissions: List of permissions to check

        Returns:
            bool: True if has all permissions
        """
        return all(self.check_permission(p) for p in permissions)
