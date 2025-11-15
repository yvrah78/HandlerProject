"""
Load Balancer for agent workload management.

Monitors agent load and distributes tasks efficiently to:
- Prevent overload
- Maximize throughput
- Ensure fair distribution
- Maintain system health
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
from src.core.logging import get_logger


@dataclass
class AgentLoad:
    """
    Agent load information.

    Attributes:
        agent_name: Name of the agent
        active_tasks: Number of currently active tasks
        completed_tasks: Total completed tasks
        failed_tasks: Total failed tasks
        average_task_duration: Average task duration in seconds
        load_percentage: Current load (0.0 - 1.0)
        is_available: Whether agent is accepting new tasks
        last_updated: Last update timestamp
    """

    agent_name: str
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_task_duration: float = 0.0
    load_percentage: float = 0.0
    is_available: bool = True
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "average_task_duration": self.average_task_duration,
            "load_percentage": self.load_percentage,
            "is_available": self.is_available,
            "last_updated": self.last_updated.isoformat()
        }


class LoadBalancer:
    """
    Manages agent load and distributes tasks efficiently.

    Features:
    - Real-time load monitoring
    - Agent health tracking
    - Load-based task distribution
    - Performance metrics
    - Auto-scaling recommendations
    """

    def __init__(
        self,
        max_tasks_per_agent: int = 10,
        load_threshold: float = 0.8
    ):
        """
        Initialize load balancer.

        Args:
            max_tasks_per_agent: Maximum concurrent tasks per agent
            load_threshold: Load threshold for warnings (0.0 - 1.0)
        """
        self.logger = get_logger("load_balancer")

        self.max_tasks_per_agent = max_tasks_per_agent
        self.load_threshold = load_threshold

        # Agent load tracking
        self._agent_loads: Dict[str, AgentLoad] = {}

        # Task timing tracking
        self._task_timings: Dict[str, List[float]] = defaultdict(list)

        # Load history for analytics
        self._load_history: List[Dict[str, Any]] = []
        self._max_history = 1000

        self.logger.info(
            f"Load balancer initialized "
            f"(max_tasks={max_tasks_per_agent}, threshold={load_threshold})"
        )

    def register_agent(self, agent_name: str) -> None:
        """
        Register an agent with the load balancer.

        Args:
            agent_name: Name of the agent
        """
        if agent_name not in self._agent_loads:
            self._agent_loads[agent_name] = AgentLoad(agent_name=agent_name)
            self.logger.info(f"Agent '{agent_name}' registered with load balancer")

    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent.

        Args:
            agent_name: Name of the agent
        """
        if agent_name in self._agent_loads:
            del self._agent_loads[agent_name]
            self.logger.info(f"Agent '{agent_name}' unregistered from load balancer")

    def task_started(self, agent_name: str, task_id: str) -> None:
        """
        Record that a task has started on an agent.

        Args:
            agent_name: Name of the agent
            task_id: Task ID
        """
        self._ensure_agent_registered(agent_name)

        load = self._agent_loads[agent_name]
        load.active_tasks += 1
        load.load_percentage = load.active_tasks / self.max_tasks_per_agent
        load.last_updated = datetime.utcnow()

        # Check if agent is overloaded
        if load.load_percentage >= self.load_threshold:
            self.logger.warning(
                f"Agent '{agent_name}' is heavily loaded "
                f"({load.load_percentage:.1%})"
            )

        self.logger.debug(
            f"Task {task_id} started on agent '{agent_name}' "
            f"(load: {load.load_percentage:.1%})"
        )

        # Record load snapshot
        self._record_load_snapshot()

    def task_completed(
        self,
        agent_name: str,
        task_id: str,
        duration: float,
        success: bool = True
    ) -> None:
        """
        Record that a task has completed.

        Args:
            agent_name: Name of the agent
            task_id: Task ID
            duration: Task duration in seconds
            success: Whether task completed successfully
        """
        self._ensure_agent_registered(agent_name)

        load = self._agent_loads[agent_name]
        load.active_tasks = max(0, load.active_tasks - 1)
        load.load_percentage = load.active_tasks / self.max_tasks_per_agent
        load.last_updated = datetime.utcnow()

        if success:
            load.completed_tasks += 1
        else:
            load.failed_tasks += 1

        # Update average task duration
        timings = self._task_timings[agent_name]
        timings.append(duration)

        # Keep only recent timings (last 100)
        if len(timings) > 100:
            timings.pop(0)

        load.average_task_duration = sum(timings) / len(timings)

        self.logger.debug(
            f"Task {task_id} completed on agent '{agent_name}' "
            f"in {duration:.2f}s (load: {load.load_percentage:.1%})"
        )

        # Record load snapshot
        self._record_load_snapshot()

    def get_least_loaded_agent(
        self,
        agent_names: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Get the least loaded available agent.

        Args:
            agent_names: Optional list of agent names to consider

        Returns:
            Name of least loaded agent or None
        """
        if agent_names:
            agents = {
                name: load
                for name, load in self._agent_loads.items()
                if name in agent_names
            }
        else:
            agents = self._agent_loads

        # Filter to available agents
        available = {
            name: load
            for name, load in agents.items()
            if load.is_available and load.active_tasks < self.max_tasks_per_agent
        }

        if not available:
            self.logger.warning("No available agents found")
            return None

        # Find agent with lowest load
        least_loaded = min(
            available.items(),
            key=lambda x: x[1].load_percentage
        )

        return least_loaded[0]

    def get_agent_load(self, agent_name: str) -> Optional[AgentLoad]:
        """
        Get load information for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentLoad or None if not found
        """
        return self._agent_loads.get(agent_name)

    def get_all_loads(self) -> Dict[str, AgentLoad]:
        """
        Get load information for all agents.

        Returns:
            Dictionary of agent names to AgentLoad
        """
        return self._agent_loads.copy()

    def set_agent_availability(
        self,
        agent_name: str,
        available: bool
    ) -> None:
        """
        Set agent availability.

        Args:
            agent_name: Name of the agent
            available: Whether agent should accept new tasks
        """
        self._ensure_agent_registered(agent_name)

        self._agent_loads[agent_name].is_available = available
        self._agent_loads[agent_name].last_updated = datetime.utcnow()

        status = "available" if available else "unavailable"
        self.logger.info(f"Agent '{agent_name}' marked as {status}")

    def get_system_load(self) -> Dict[str, Any]:
        """
        Get overall system load metrics.

        Returns:
            System load statistics
        """
        if not self._agent_loads:
            return {
                "total_agents": 0,
                "available_agents": 0,
                "total_active_tasks": 0,
                "average_load": 0.0,
                "overloaded_agents": 0
            }

        total_agents = len(self._agent_loads)
        available_agents = sum(
            1 for load in self._agent_loads.values()
            if load.is_available
        )
        total_active_tasks = sum(
            load.active_tasks
            for load in self._agent_loads.values()
        )
        average_load = sum(
            load.load_percentage
            for load in self._agent_loads.values()
        ) / total_agents

        overloaded_agents = sum(
            1 for load in self._agent_loads.values()
            if load.load_percentage >= self.load_threshold
        )

        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "total_active_tasks": total_active_tasks,
            "average_load": average_load,
            "overloaded_agents": overloaded_agents,
            "capacity_used": total_active_tasks / (total_agents * self.max_tasks_per_agent)
        }

    def get_recommendations(self) -> List[str]:
        """
        Get load balancing recommendations.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        system_load = self.get_system_load()

        # Check overall capacity
        if system_load["capacity_used"] > 0.8:
            recommendations.append(
                "System capacity is high (>80%). Consider adding more agents."
            )

        # Check for overloaded agents
        if system_load["overloaded_agents"] > 0:
            recommendations.append(
                f"{system_load['overloaded_agents']} agent(s) are overloaded. "
                "Redistribute tasks or increase capacity."
            )

        # Check for idle agents
        idle_agents = [
            name for name, load in self._agent_loads.items()
            if load.is_available and load.active_tasks == 0
        ]

        if len(idle_agents) > len(self._agent_loads) // 2:
            recommendations.append(
                f"{len(idle_agents)} agent(s) are idle. System may be underutilized."
            )

        # Check for unavailable agents
        unavailable = [
            name for name, load in self._agent_loads.items()
            if not load.is_available
        ]

        if unavailable:
            recommendations.append(
                f"{len(unavailable)} agent(s) are unavailable: {', '.join(unavailable)}"
            )

        if not recommendations:
            recommendations.append("System load is balanced and healthy.")

        return recommendations

    def _ensure_agent_registered(self, agent_name: str) -> None:
        """Ensure an agent is registered."""
        if agent_name not in self._agent_loads:
            self.register_agent(agent_name)

    def _record_load_snapshot(self) -> None:
        """Record a snapshot of current load for analytics."""
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_load": self.get_system_load(),
            "agent_loads": {
                name: load.to_dict()
                for name, load in self._agent_loads.items()
            }
        }

        self._load_history.append(snapshot)

        # Trim history
        if len(self._load_history) > self._max_history:
            self._load_history.pop(0)

    def get_load_history(
        self,
        minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get load history for the past N minutes.

        Args:
            minutes: Number of minutes to retrieve

        Returns:
            List of load snapshots
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        return [
            snapshot for snapshot in self._load_history
            if datetime.fromisoformat(snapshot["timestamp"]) >= cutoff
        ]

    def reset_agent_stats(self, agent_name: str) -> None:
        """
        Reset statistics for an agent.

        Args:
            agent_name: Name of the agent
        """
        if agent_name in self._agent_loads:
            load = self._agent_loads[agent_name]
            load.completed_tasks = 0
            load.failed_tasks = 0
            load.average_task_duration = 0.0
            self._task_timings[agent_name].clear()

            self.logger.info(f"Reset statistics for agent '{agent_name}'")
