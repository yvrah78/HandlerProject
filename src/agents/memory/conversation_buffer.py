"""
Conversation Buffer Memory for Project Handler agents.
Stores complete conversation history up to max_size.
"""
from typing import List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.agents.memory.base_memory import BaseMemory
from src.core.logging import get_logger

logger = get_logger(__name__)


class ConversationBufferMemory(BaseMemory):
    """
    Simple conversation buffer that stores all messages up to max_size.

    When max_size is reached, oldest messages are removed first (FIFO).
    Good for recent conversation context preservation.
    """

    def __init__(
        self,
        max_size: int = 50,
        ttl_seconds: Optional[int] = None,
        system_message: Optional[str] = None,
    ):
        """
        Initialize conversation buffer memory.

        Args:
            max_size: Maximum messages to store
            ttl_seconds: Time-to-live for messages
            system_message: Optional system message to always include
        """
        super().__init__(max_size=max_size, ttl_seconds=ttl_seconds)
        self.system_message = system_message
        self.total_interactions = 0

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to buffer.

        Args:
            message: Message to add
        """
        # Add timestamp metadata
        if not hasattr(message, "metadata"):
            message.metadata = {}
        message.metadata["timestamp"] = datetime.utcnow()

        # Add message to buffer
        self._messages.append(message)

        # Trim if exceeded max_size
        if len(self._messages) > self.max_size:
            removed = self._messages.pop(0)
            logger.debug(
                f"Memory buffer full. Removed oldest message: "
                f"{removed.content[:50]}..."
            )

        # Track interactions
        if isinstance(message, (HumanMessage, AIMessage)):
            self.total_interactions += 1

    def get_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """
        Get messages from buffer.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List[BaseMessage]: Messages from memory
        """
        # Filter expired messages if TTL set
        messages = [m for m in self._messages if not self._should_remove(m)]

        # Apply limit
        if limit:
            return messages[-limit:]

        return messages

    def clear(self) -> None:
        """Clear all messages from memory."""
        self._messages = []
        self.total_interactions = 0
        logger.info("Conversation buffer cleared")

    def get_summary(self) -> str:
        """
        Get summary of conversation.

        Returns:
            str: Human-readable summary
        """
        if not self._messages:
            return "No conversation history."

        human_count = sum(1 for m in self._messages if isinstance(m, HumanMessage))
        ai_count = sum(1 for m in self._messages if isinstance(m, AIMessage))

        summary = f"Conversation buffer summary:\n"
        summary += f"- Total messages: {len(self._messages)}\n"
        summary += f"- Human messages: {human_count}\n"
        summary += f"- AI messages: {ai_count}\n"
        summary += f"- Total interactions: {self.total_interactions}\n"

        # Show last few messages
        if self._messages:
            summary += "\nRecent messages:\n"
            for msg in self._messages[-3:]:
                msg_type = "Human" if isinstance(msg, HumanMessage) else "AI"
                content_preview = msg.content[:60].replace("\n", " ")
                summary += f"- [{msg_type}] {content_preview}...\n"

        return summary

    def get_conversation_length(self) -> int:
        """
        Get number of messages in buffer.

        Returns:
            int: Message count
        """
        return len(self._messages)

    def get_last_message(self) -> Optional[BaseMessage]:
        """
        Get the last message in buffer.

        Returns:
            Optional[BaseMessage]: Last message or None
        """
        return self._messages[-1] if self._messages else None

    def get_last_n_messages(self, n: int) -> List[BaseMessage]:
        """
        Get last N messages.

        Args:
            n: Number of messages to retrieve

        Returns:
            List[BaseMessage]: Last N messages
        """
        return self._messages[-n:] if self._messages else []

    def export_conversation(self) -> List[dict]:
        """
        Export conversation as list of dictionaries.

        Returns:
            List[dict]: Conversation in dict format
        """
        result = []
        for msg in self._messages:
            msg_type = "human" if isinstance(msg, HumanMessage) else "ai"
            result.append(
                {
                    "type": msg_type,
                    "content": msg.content,
                    "timestamp": msg.metadata.get("timestamp").isoformat()
                    if hasattr(msg, "metadata") and "timestamp" in msg.metadata
                    else None,
                }
            )
        return result
