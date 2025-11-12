"""
Base Memory class for Project Handler agents.
Provides abstract interface for different memory implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage


class BaseMemory(ABC):
    """
    Abstract base class for agent memory systems.

    Defines interface for storing, retrieving, and managing conversation history.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: Optional[int] = None):
        """
        Initialize base memory.

        Args:
            max_size: Maximum number of messages to store
            ttl_seconds: Time-to-live for messages (None = no expiration)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.created_at = datetime.utcnow()
        self._messages: List[BaseMessage] = []

    @abstractmethod
    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to memory.

        Args:
            message: Message to add
        """
        pass

    @abstractmethod
    def get_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """
        Retrieve messages from memory.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List[BaseMessage]: Messages from memory
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all messages from memory."""
        pass

    @abstractmethod
    def get_summary(self) -> str:
        """
        Get a summary of conversation history.

        Returns:
            str: Summary of the conversation
        """
        pass

    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get information about memory status.

        Returns:
            Dict[str, Any]: Memory information
        """
        return {
            "type": self.__class__.__name__,
            "max_size": self.max_size,
            "current_size": len(self._messages),
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at.isoformat(),
        }

    def _should_remove(self, message: BaseMessage) -> bool:
        """
        Check if message should be removed based on TTL.

        Args:
            message: Message to check

        Returns:
            bool: True if message should be removed
        """
        if self.ttl_seconds is None:
            return False

        # Check if message has timestamp metadata
        if hasattr(message, "metadata") and "timestamp" in message.metadata:
            timestamp = message.metadata["timestamp"]
            age_seconds = (datetime.utcnow() - timestamp).total_seconds()
            return age_seconds > self.ttl_seconds

        return False
