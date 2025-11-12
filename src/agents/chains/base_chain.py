"""
Base Chain class for Project Handler.
Provides abstract interface for chain composition and execution.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class ChainInput(BaseModel):
    """Base model for chain input."""

    class Config:
        extra = "allow"


class ChainOutput(BaseModel):
    """Base model for chain output."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = None
    timestamp: str = None

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)


class Chain(ABC):
    """
    Abstract base class for all chains in the system.

    Chains represent a sequence of operations that can be composed
    and executed together. They form the backbone of agent workflows.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        input_keys: Optional[List[str]] = None,
        output_keys: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        """
        Initialize chain.

        Args:
            name: Unique chain name
            description: Chain description
            input_keys: Expected input keys
            output_keys: Expected output keys
            verbose: Enable verbose logging
        """
        self.name = name
        self.description = description or f"{name} Chain"
        self.input_keys = input_keys or []
        self.output_keys = output_keys or []
        self.verbose = verbose

        # Execution tracking
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.created_at = datetime.utcnow()

        logger.info(f"Chain initialized: {self.name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ChainOutput:
        """
        Execute the chain.

        Args:
            input_data: Input data for the chain

        Returns:
            ChainOutput: Chain execution result
        """
        pass

    async def run(self, input_data: Dict[str, Any]) -> ChainOutput:
        """
        Run chain with validation and error handling.

        Args:
            input_data: Input data for the chain

        Returns:
            ChainOutput: Chain execution result
        """
        import time

        start_time = time.time()

        try:
            # Validate input
            missing_keys = [k for k in self.input_keys if k not in input_data]
            if missing_keys:
                return ChainOutput(
                    success=False,
                    error=f"Missing required input keys: {missing_keys}",
                )

            if self.verbose:
                logger.info(f"Chain '{self.name}' starting execution")

            # Execute chain
            result = await self.execute(input_data)

            # Update stats
            self.execution_count += 1
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time

            if self.verbose:
                logger.info(
                    f"Chain '{self.name}' completed in {execution_time:.3f}s"
                )

            return result

        except Exception as e:
            logger.error(f"Chain execution failed: {self.name}: {str(e)}")
            execution_time = time.time() - start_time

            return ChainOutput(
                success=False,
                error=f"Chain execution failed: {str(e)}",
            )

    def get_info(self) -> Dict[str, Any]:
        """
        Get chain information.

        Returns:
            Dict[str, Any]: Chain metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_keys": self.input_keys,
            "output_keys": self.output_keys,
            "execution_count": self.execution_count,
            "avg_execution_time": (
                self.total_execution_time / self.execution_count
                if self.execution_count > 0
                else 0
            ),
            "created_at": self.created_at.isoformat(),
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid
        """
        missing_keys = [k for k in self.input_keys if k not in input_data]
        if missing_keys:
            logger.warning(
                f"Chain input validation failed. Missing keys: {missing_keys}"
            )
            return False
        return True

    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate output data.

        Args:
            output_data: Output to validate

        Returns:
            bool: True if valid
        """
        missing_keys = [k for k in self.output_keys if k not in output_data]
        if missing_keys:
            logger.warning(
                f"Chain output validation failed. Missing keys: {missing_keys}"
            )
            return False
        return True

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self.execution_count = 0
        self.total_execution_time = 0.0
        logger.info(f"Stats reset for chain {self.name}")
