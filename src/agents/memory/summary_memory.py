"""
Summary Memory for Project Handler agents.
Automatically summarizes older messages to save tokens.
"""
from typing import List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from src.agents.memory.base_memory import BaseMemory
from src.core.logging import get_logger

logger = get_logger(__name__)


class SummaryMemory(BaseMemory):
    """
    Advanced memory that maintains conversation summaries.

    Keeps recent messages in full detail and older messages as summarized.
    Good for long conversations where token efficiency is important.
    """

    def __init__(
        self,
        max_size: int = 50,
        summary_threshold: int = 10,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize summary memory.

        Args:
            max_size: Maximum messages to store (including summary)
            summary_threshold: Number of messages before auto-summarize
            ttl_seconds: Time-to-live for messages
        """
        super().__init__(max_size=max_size, ttl_seconds=ttl_seconds)
        self.summary_threshold = summary_threshold
        self.summary: Optional[str] = None
        self.summarized_message_count = 0

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message and potentially trigger summarization.

        Args:
            message: Message to add
        """
        # Add timestamp metadata
        if not hasattr(message, "metadata"):
            message.metadata = {}
        message.metadata["timestamp"] = datetime.utcnow()

        self._messages.append(message)

        # Auto-summarize if threshold reached
        if len(self._messages) >= self.summary_threshold and not self.summary:
            self._summarize()

    def get_messages(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """
        Get messages with summary context.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List[BaseMessage]: Messages with summary if available
        """
        # Filter expired messages
        messages = [m for m in self._messages if not self._should_remove(m)]

        result = []

        # Add summary as context if available
        if self.summary:
            summary_msg = SystemMessage(
                content=f"Previous conversation summary:\n{self.summary}"
            )
            result.append(summary_msg)

        # Add recent messages
        if limit:
            result.extend(messages[-limit:])
        else:
            result.extend(messages)

        return result

    def clear(self) -> None:
        """Clear all messages and summary."""
        self._messages = []
        self.summary = None
        self.summarized_message_count = 0
        logger.info("Summary memory cleared")

    def _summarize(self) -> None:
        """
        Summarize older messages.

        This is a placeholder for actual summarization.
        In production, you would call Claude or another LLM to summarize.
        """
        if len(self._messages) < self.summary_threshold:
            return

        # For now, create a basic summary
        human_count = sum(1 for m in self._messages if isinstance(m, HumanMessage))
        ai_count = sum(1 for m in self._messages if isinstance(m, AIMessage))

        self.summary = f"Conversation included {human_count} user messages and {ai_count} AI responses."
        self.summarized_message_count = len(self._messages) - 5

        # Keep only last 5 messages + summary
        self._messages = self._messages[-5:]

        logger.info(
            f"Auto-summarized {self.summarized_message_count} messages. "
            f"Kept {len(self._messages)} recent messages."
        )

    def get_summary(self) -> str:
        """
        Get memory summary.

        Returns:
            str: Summary of memory state
        """
        summary_text = "Summary Memory Status:\n"
        summary_text += f"- Current messages: {len(self._messages)}\n"
        summary_text += f"- Summarized messages: {self.summarized_message_count}\n"

        if self.summary:
            summary_text += f"\nConversation Summary:\n{self.summary}\n"

        # Show recent messages
        if self._messages:
            summary_text += "\nRecent Messages:\n"
            for msg in self._messages[-3:]:
                msg_type = "Human" if isinstance(msg, HumanMessage) else "AI"
                content_preview = msg.content[:50].replace("\n", " ")
                summary_text += f"- [{msg_type}] {content_preview}...\n"

        return summary_text

    def get_context_summary(self) -> str:
        """
        Get a concise summary for use as context.

        Returns:
            str: Concise summary for context
        """
        if not self.summary:
            return "No previous context."

        return self.summary

    def update_summary(self, new_summary: str) -> None:
        """
        Manually update the conversation summary.

        Args:
            new_summary: New summary text
        """
        self.summary = new_summary
        logger.info("Conversation summary updated")

    def get_memory_stats(self) -> dict:
        """
        Get detailed memory statistics.

        Returns:
            dict: Memory statistics
        """
        return {
            "current_messages": len(self._messages),
            "total_messages_ever": len(self._messages) + self.summarized_message_count,
            "summarized_messages": self.summarized_message_count,
            "has_summary": self.summary is not None,
            "summary_length": len(self.summary) if self.summary else 0,
        }
