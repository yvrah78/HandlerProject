"""
Message Bus System for Inter-Agent Communication.

This module provides an event-driven message bus that enables:
- Agent-to-agent messaging
- Event broadcasting
- Shared context passing
- Asynchronous communication
- Message history and tracking
"""
from typing import Dict, Any, List, Callable, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
import uuid
from src.core.logging import get_logger


class EventType(Enum):
    """Event types for the message bus."""

    # Task Events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Agent Events
    AGENT_REGISTERED = "agent.registered"
    AGENT_READY = "agent.ready"
    AGENT_BUSY = "agent.busy"
    AGENT_IDLE = "agent.idle"
    AGENT_ERROR = "agent.error"

    # Workflow Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Communication Events
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_BROADCAST = "message.broadcast"

    # Data Events
    DATA_UPDATED = "data.updated"
    DATA_CREATED = "data.created"
    DATA_DELETED = "data.deleted"

    # System Events
    SYSTEM_ALERT = "system.alert"
    SYSTEM_ERROR = "system.error"
    SYSTEM_SHUTDOWN = "system.shutdown"


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Message:
    """
    Message object for inter-agent communication.

    Attributes:
        id: Unique message identifier
        event_type: Type of event
        sender: Name of the sending agent
        data: Message payload
        priority: Message priority level
        timestamp: When the message was created
        correlation_id: ID for tracking related messages
        metadata: Additional metadata
        recipients: Specific recipients (None = broadcast)
    """

    event_type: EventType
    sender: str
    data: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    recipients: Optional[Set[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "sender": self.sender,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "recipients": list(self.recipients) if self.recipients else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            id=data["id"],
            event_type=EventType(data["event_type"]),
            sender=data["sender"],
            data=data["data"],
            priority=MessagePriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
            recipients=set(data["recipients"]) if data.get("recipients") else None
        )


class MessageBus:
    """
    Event-driven message bus for agent communication.

    Implements pub/sub pattern with:
    - Event subscriptions
    - Message broadcasting
    - Message routing
    - Message history
    - Async handling
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize message bus.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.logger = get_logger("message_bus")

        # Subscriptions: event_type -> set of (subscriber_name, callback)
        self._subscriptions: Dict[EventType, List[tuple[str, Callable]]] = defaultdict(list)

        # Message history
        self._message_history: List[Message] = []
        self._max_history = max_history

        # Active subscribers
        self._active_subscribers: Set[str] = set()

        # Message queue for async processing
        self._message_queue: asyncio.Queue = asyncio.Queue()

        # Stats
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_broadcast": 0,
            "errors": 0
        }

        # Running flag
        self._running = False
        self._processor_task = None

        self.logger.info("Message bus initialized")

    def subscribe(
        self,
        event_type: EventType,
        subscriber_name: str,
        callback: Callable
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            subscriber_name: Name of the subscriber
            callback: Async callback function to handle events
        """
        self._subscriptions[event_type].append((subscriber_name, callback))
        self._active_subscribers.add(subscriber_name)

        self.logger.info(
            f"Subscriber '{subscriber_name}' subscribed to {event_type.value}"
        )

    def unsubscribe(
        self,
        event_type: EventType,
        subscriber_name: str
    ) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            subscriber_name: Name of the subscriber
        """
        self._subscriptions[event_type] = [
            (name, callback)
            for name, callback in self._subscriptions[event_type]
            if name != subscriber_name
        ]

        # Remove from active subscribers if no more subscriptions
        if not any(
            subscriber_name in [name for name, _ in subs]
            for subs in self._subscriptions.values()
        ):
            self._active_subscribers.discard(subscriber_name)

        self.logger.info(
            f"Subscriber '{subscriber_name}' unsubscribed from {event_type.value}"
        )

    async def publish(
        self,
        message: Message,
        wait_for_completion: bool = False
    ) -> None:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
            wait_for_completion: If True, wait for all handlers to complete
        """
        # Add to history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

        # Update stats
        if message.recipients:
            self._stats["messages_sent"] += len(message.recipients)
        else:
            self._stats["messages_broadcast"] += 1

        self.logger.debug(
            f"Publishing message {message.id} - "
            f"Event: {message.event_type.value}, "
            f"Sender: {message.sender}, "
            f"Priority: {message.priority.value}"
        )

        # Get subscribers for this event type
        subscribers = self._subscriptions.get(message.event_type, [])

        # Filter by recipients if specified
        if message.recipients:
            subscribers = [
                (name, callback)
                for name, callback in subscribers
                if name in message.recipients
            ]

        # Execute callbacks
        if wait_for_completion:
            await self._execute_callbacks(message, subscribers)
        else:
            # Queue for async processing
            await self._message_queue.put((message, subscribers))

    async def _execute_callbacks(
        self,
        message: Message,
        subscribers: List[tuple[str, Callable]]
    ) -> None:
        """
        Execute all callbacks for a message.

        Args:
            message: The message to process
            subscribers: List of (subscriber_name, callback) tuples
        """
        for subscriber_name, callback in subscribers:
            try:
                self.logger.debug(
                    f"Delivering message {message.id} to {subscriber_name}"
                )

                # Execute callback
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)

                self._stats["messages_received"] += 1

            except Exception as e:
                self._stats["errors"] += 1
                self.logger.error(
                    f"Error delivering message {message.id} to {subscriber_name}: {e}"
                )

    async def start(self) -> None:
        """Start the message bus processor."""
        if self._running:
            self.logger.warning("Message bus already running")
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_queue())
        self.logger.info("Message bus started")

    async def stop(self) -> None:
        """Stop the message bus processor."""
        if not self._running:
            return

        self._running = False

        # Wait for queue to empty
        await self._message_queue.join()

        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Message bus stopped")

    async def _process_queue(self) -> None:
        """Process messages from the queue."""
        while self._running:
            try:
                # Get message from queue with timeout
                try:
                    message, subscribers = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Execute callbacks
                await self._execute_callbacks(message, subscribers)

                # Mark task as done
                self._message_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error processing message queue: {e}")

    def get_message_history(
        self,
        event_type: Optional[EventType] = None,
        sender: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Get message history.

        Args:
            event_type: Filter by event type
            sender: Filter by sender
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        messages = self._message_history

        if event_type:
            messages = [m for m in messages if m.event_type == event_type]

        if sender:
            messages = [m for m in messages if m.sender == sender]

        return messages[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            "active_subscribers": len(self._active_subscribers),
            "total_subscriptions": sum(
                len(subs) for subs in self._subscriptions.values()
            ),
            "queue_size": self._message_queue.qsize(),
            "history_size": len(self._message_history),
            "running": self._running
        }

    def get_subscribers(self, event_type: Optional[EventType] = None) -> Dict[str, List[str]]:
        """
        Get current subscribers.

        Args:
            event_type: Optional event type filter

        Returns:
            Dictionary mapping event types to subscriber names
        """
        if event_type:
            return {
                event_type.value: [name for name, _ in self._subscriptions[event_type]]
            }

        return {
            event.value: [name for name, _ in subs]
            for event, subs in self._subscriptions.items()
        }

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()
        self.logger.info("Message history cleared")


# Global message bus instance
_message_bus_instance: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """
    Get the global message bus instance.

    Returns:
        MessageBus instance
    """
    global _message_bus_instance

    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()

    return _message_bus_instance


async def publish_event(
    event_type: EventType,
    sender: str,
    data: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL,
    correlation_id: Optional[str] = None,
    recipients: Optional[Set[str]] = None
) -> str:
    """
    Convenience function to publish an event.

    Args:
        event_type: Type of event
        sender: Name of sender
        data: Event data
        priority: Message priority
        correlation_id: Optional correlation ID
        recipients: Optional specific recipients

    Returns:
        Message ID
    """
    message = Message(
        event_type=event_type,
        sender=sender,
        data=data,
        priority=priority,
        correlation_id=correlation_id,
        recipients=recipients
    )

    bus = get_message_bus()
    await bus.publish(message)

    return message.id
