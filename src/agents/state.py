"""
Agent State Management for Project Handler.
Tracks and persists agent state across interactions.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json

from src.core.logging import get_logger

logger = get_logger(__name__)


class AgentStateEnum(str, Enum):
    """Agent state enumeration."""

    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentState:
    """
    Manages agent state and execution history.

    Tracks:
    - Current state (idle, processing, waiting, error)
    - Execution history
    - Context variables
    - Performance metrics
    """

    def __init__(
        self, agent_name: str, persist_to_db: bool = False
    ):
        """
        Initialize agent state.

        Args:
            agent_name: Name of the agent
            persist_to_db: Whether to persist state to database
        """
        self.agent_name = agent_name
        self.persist_to_db = persist_to_db

        # State tracking
        self.current_state = AgentStateEnum.IDLE
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

        # Execution tracking
        self.execution_count = 0
        self.error_count = 0
        self.last_execution_time = None

        # Context variables
        self._context: Dict[str, Any] = {}

        # Execution history
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100

        logger.info(f"Agent state initialized for {agent_name}")

    def set_state(self, new_state: AgentStateEnum) -> None:
        """
        Set agent state.

        Args:
            new_state: New state
        """
        old_state = self.current_state
        self.current_state = new_state
        self.last_updated = datetime.utcnow()
        logger.info(f"Agent {self.agent_name} state: {old_state} → {new_state}")

    def set_processing(self) -> None:
        """Set state to processing."""
        self.set_state(AgentStateEnum.PROCESSING)

    def set_waiting(self) -> None:
        """Set state to waiting."""
        self.set_state(AgentStateEnum.WAITING)

    def set_completed(self) -> None:
        """Set state to completed."""
        self.set_state(AgentStateEnum.COMPLETED)
        self.execution_count += 1

    def set_error(self) -> None:
        """Set state to error."""
        self.set_state(AgentStateEnum.ERROR)
        self.error_count += 1

    def set_idle(self) -> None:
        """Set state to idle."""
        self.set_state(AgentStateEnum.IDLE)

    def get_state(self) -> AgentStateEnum:
        """
        Get current state.

        Returns:
            AgentStateEnum: Current state
        """
        return self.current_state

    def get_context(self, key: Optional[str] = None) -> Any:
        """
        Get context variables.

        Args:
            key: Specific key to retrieve (None = all)

        Returns:
            Any: Context value or dict
        """
        if key is None:
            return self._context.copy()
        return self._context.get(key)

    def set_context(self, key: str, value: Any) -> None:
        """
        Set context variable.

        Args:
            key: Variable key
            value: Variable value
        """
        self._context[key] = value
        logger.debug(f"Context set: {key}")

    def update_context(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple context variables.

        Args:
            updates: Dictionary of updates
        """
        self._context.update(updates)
        logger.debug(f"Context updated with {len(updates)} variables")

    def clear_context(self) -> None:
        """Clear all context variables."""
        self._context.clear()
        logger.debug("Context cleared")

    def add_to_history(
        self,
        event_type: str,
        data: Dict[str, Any],
        status: str = "success",
    ) -> None:
        """
        Add execution event to history.

        Args:
            event_type: Type of event
            data: Event data
            status: Event status (success, error, warning)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "status": status,
            "data": data,
        }

        self._history.append(entry)

        # Trim history if exceeds max
        if len(self._history) > self._max_history:
            self._history.pop(0)

        logger.debug(f"Event added to history: {event_type}")

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get execution history.

        Args:
            limit: Maximum entries to return

        Returns:
            List[Dict[str, Any]]: History entries
        """
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear execution history."""
        self._history.clear()
        logger.info(f"History cleared for agent {self.agent_name}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get complete agent status.

        Returns:
            Dict[str, Any]: Status information
        """
        return {
            "agent": self.agent_name,
            "state": self.current_state.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "error_rate": (
                self.error_count / self.execution_count
                if self.execution_count > 0
                else 0
            ),
            "context_variables": len(self._context),
            "history_size": len(self._history),
        }

    def export_state(self) -> Dict[str, Any]:
        """
        Export complete state as dictionary.

        Returns:
            Dict[str, Any]: Complete state
        """
        return {
            "agent": self.agent_name,
            "state": self.current_state.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "context": self._context,
            "history": self._history,
        }

    def export_json(self) -> str:
        """
        Export state as JSON.

        Returns:
            str: JSON representation of state
        """
        state_dict = self.export_state()
        return json.dumps(state_dict, default=str, indent=2)

    def reset(self) -> None:
        """Reset agent state to initial."""
        self.current_state = AgentStateEnum.IDLE
        self.execution_count = 0
        self.error_count = 0
        self._context.clear()
        self._history.clear()
        logger.info(f"Agent state reset for {self.agent_name}")


class AgentStateManager:
    """
    Manages state for multiple agents.

    Provides centralized management of agent states.
    """

    def __init__(self):
        """Initialize state manager."""
        self._states: Dict[str, AgentState] = {}

    def create_state(self, agent_name: str) -> AgentState:
        """
        Create or get agent state.

        Args:
            agent_name: Name of agent

        Returns:
            AgentState: Agent state instance
        """
        if agent_name not in self._states:
            self._states[agent_name] = AgentState(agent_name)
        return self._states[agent_name]

    def get_state(self, agent_name: str) -> Optional[AgentState]:
        """
        Get agent state.

        Args:
            agent_name: Name of agent

        Returns:
            Optional[AgentState]: Agent state or None
        """
        return self._states.get(agent_name)

    def get_all_states(self) -> Dict[str, AgentState]:
        """
        Get all agent states.

        Returns:
            Dict[str, AgentState]: Mapping of agent names to states
        """
        return self._states.copy()

    def remove_state(self, agent_name: str) -> None:
        """
        Remove agent state.

        Args:
            agent_name: Name of agent
        """
        if agent_name in self._states:
            del self._states[agent_name]

    def reset_all(self) -> None:
        """Reset all agent states."""
        for state in self._states.values():
            state.reset()


# Global state manager instance
_state_manager: Optional[AgentStateManager] = None


def get_state_manager() -> AgentStateManager:
    """
    Get global state manager.

    Returns:
        AgentStateManager: Global state manager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = AgentStateManager()
    return _state_manager
