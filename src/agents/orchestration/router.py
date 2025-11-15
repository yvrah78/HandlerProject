"""
Intelligent Router for task routing and agent selection.

Routes tasks to appropriate agents based on:
- Agent capabilities
- Current load
- Task requirements
- Routing strategy
"""
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from src.core.logging import get_logger
from src.agents.orchestration.task_analyzer import TaskAnalysis, TaskType


class RoutingStrategy(Enum):
    """Routing strategies for task distribution."""

    CAPABILITY_BASED = "capability_based"  # Route based on agent capabilities
    LOAD_BALANCED = "load_balanced"        # Route to least loaded agent
    ROUND_ROBIN = "round_robin"            # Simple round-robin distribution
    PRIORITY_BASED = "priority_based"      # Route high-priority to best agents
    HYBRID = "hybrid"                      # Combination of strategies


@dataclass
class RoutingDecision:
    """
    Result of routing decision.

    Attributes:
        primary_agent: Primary agent to handle the task
        backup_agents: Backup agents if primary fails
        routing_strategy: Strategy used for routing
        confidence: Confidence score (0-100)
        reasoning: Explanation of routing decision
    """

    primary_agent: str
    backup_agents: List[str]
    routing_strategy: RoutingStrategy
    confidence: int
    reasoning: str


class IntelligentRouter:
    """
    Routes tasks to appropriate agents using various strategies.

    Considers:
    - Agent capabilities and specializations
    - Current agent load and availability
    - Task requirements and priority
    - Historical performance
    """

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.HYBRID):
        """
        Initialize intelligent router.

        Args:
            strategy: Default routing strategy
        """
        self.logger = get_logger("intelligent_router")
        self.default_strategy = strategy

        # Agent capabilities registry
        self._agent_capabilities: Dict[str, Set[str]] = {
            "communications": {
                "communication", "sms", "email", "phone", "notifications"
            },
            "financial": {
                "financial", "payments", "invoicing", "quotes", "billing"
            },
            "operations": {
                "operations", "routing", "fleet_management", "booking",
                "scheduling", "dispatch"
            },
            "analytics": {
                "analytics", "reporting", "metrics", "predictions", "insights"
            },
            "coordinator": {
                "coordination", "orchestration", "workflow"
            }
        }

        # Round-robin counter
        self._round_robin_counter = 0

        # Routing history for learning
        self._routing_history: List[Dict[str, Any]] = []

        self.logger.info(f"Intelligent router initialized with strategy: {strategy.value}")

    def route(
        self,
        task_analysis: TaskAnalysis,
        agent_loads: Optional[Dict[str, float]] = None,
        strategy: Optional[RoutingStrategy] = None
    ) -> RoutingDecision:
        """
        Route a task to an appropriate agent.

        Args:
            task_analysis: Analysis of the task
            agent_loads: Current load of each agent (0-1)
            strategy: Routing strategy to use (defaults to class default)

        Returns:
            RoutingDecision with selected agent and reasoning
        """
        strategy = strategy or self.default_strategy
        agent_loads = agent_loads or {}

        self.logger.debug(
            f"Routing task of type {task_analysis.task_type.value} "
            f"using strategy {strategy.value}"
        )

        # Route based on strategy
        if strategy == RoutingStrategy.CAPABILITY_BASED:
            decision = self._route_by_capability(task_analysis)
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            decision = self._route_by_load(task_analysis, agent_loads)
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            decision = self._route_round_robin(task_analysis)
        elif strategy == RoutingStrategy.PRIORITY_BASED:
            decision = self._route_by_priority(task_analysis, agent_loads)
        else:  # HYBRID
            decision = self._route_hybrid(task_analysis, agent_loads)

        # Record routing decision
        self._routing_history.append({
            "task_type": task_analysis.task_type.value,
            "agent": decision.primary_agent,
            "strategy": strategy.value,
            "confidence": decision.confidence
        })

        self.logger.info(
            f"Routed task to {decision.primary_agent} "
            f"(confidence: {decision.confidence}%)"
        )

        return decision

    def _route_by_capability(self, task_analysis: TaskAnalysis) -> RoutingDecision:
        """Route based on agent capabilities."""
        required_agents = task_analysis.required_agents

        if not required_agents:
            primary = "coordinator"
            backups = list(self._agent_capabilities.keys())
        else:
            primary = required_agents[0]
            backups = required_agents[1:] if len(required_agents) > 1 else []

        return RoutingDecision(
            primary_agent=primary,
            backup_agents=backups,
            routing_strategy=RoutingStrategy.CAPABILITY_BASED,
            confidence=95,
            reasoning=f"Agent '{primary}' has required capabilities for {task_analysis.task_type.value}"
        )

    def _route_by_load(
        self,
        task_analysis: TaskAnalysis,
        agent_loads: Dict[str, float]
    ) -> RoutingDecision:
        """Route to least loaded capable agent."""
        capable_agents = task_analysis.required_agents or list(self._agent_capabilities.keys())

        # Sort by load (lowest first)
        sorted_agents = sorted(
            capable_agents,
            key=lambda agent: agent_loads.get(agent, 0.0)
        )

        primary = sorted_agents[0] if sorted_agents else "coordinator"
        backups = sorted_agents[1:3] if len(sorted_agents) > 1 else []

        load = agent_loads.get(primary, 0.0)
        confidence = max(50, int((1 - load) * 100))

        return RoutingDecision(
            primary_agent=primary,
            backup_agents=backups,
            routing_strategy=RoutingStrategy.LOAD_BALANCED,
            confidence=confidence,
            reasoning=f"Agent '{primary}' has lowest load ({load:.2f}) among capable agents"
        )

    def _route_round_robin(self, task_analysis: TaskAnalysis) -> RoutingDecision:
        """Route using round-robin strategy."""
        capable_agents = task_analysis.required_agents or list(self._agent_capabilities.keys())

        if not capable_agents:
            capable_agents = ["coordinator"]

        # Select next agent in round-robin
        index = self._round_robin_counter % len(capable_agents)
        primary = capable_agents[index]

        # Increment counter
        self._round_robin_counter += 1

        # Backups are other capable agents
        backups = [a for a in capable_agents if a != primary][:2]

        return RoutingDecision(
            primary_agent=primary,
            backup_agents=backups,
            routing_strategy=RoutingStrategy.ROUND_ROBIN,
            confidence=70,
            reasoning=f"Round-robin selection: agent '{primary}'"
        )

    def _route_by_priority(
        self,
        task_analysis: TaskAnalysis,
        agent_loads: Dict[str, float]
    ) -> RoutingDecision:
        """Route high-priority tasks to best available agents."""
        capable_agents = task_analysis.required_agents or list(self._agent_capabilities.keys())

        # For high-priority tasks, prefer agents with lower load
        if task_analysis.priority_score > 70:
            sorted_agents = sorted(
                capable_agents,
                key=lambda agent: agent_loads.get(agent, 0.0)
            )
        else:
            # For normal priority, use first capable agent
            sorted_agents = capable_agents

        primary = sorted_agents[0] if sorted_agents else "coordinator"
        backups = sorted_agents[1:3] if len(sorted_agents) > 1 else []

        confidence = min(95, 60 + task_analysis.priority_score // 3)

        return RoutingDecision(
            primary_agent=primary,
            backup_agents=backups,
            routing_strategy=RoutingStrategy.PRIORITY_BASED,
            confidence=confidence,
            reasoning=f"Priority-based routing for task with priority {task_analysis.priority_score}"
        )

    def _route_hybrid(
        self,
        task_analysis: TaskAnalysis,
        agent_loads: Dict[str, float]
    ) -> RoutingDecision:
        """
        Hybrid routing using multiple strategies.

        Combines capability-based and load-balanced routing.
        """
        # Start with capable agents
        capable_agents = task_analysis.required_agents or list(self._agent_capabilities.keys())

        if not capable_agents:
            return RoutingDecision(
                primary_agent="coordinator",
                backup_agents=[],
                routing_strategy=RoutingStrategy.HYBRID,
                confidence=60,
                reasoning="No capable agents found, defaulting to coordinator"
            )

        # If high priority, prefer less loaded agents
        if task_analysis.priority_score > 70:
            sorted_agents = sorted(
                capable_agents,
                key=lambda agent: agent_loads.get(agent, 0.0)
            )
        else:
            # For normal priority, prefer first capable agent
            sorted_agents = capable_agents

        primary = sorted_agents[0]
        backups = sorted_agents[1:3] if len(sorted_agents) > 1 else []

        # Calculate confidence based on multiple factors
        load_factor = 1 - agent_loads.get(primary, 0.0)
        capability_factor = 1.0 if primary in capable_agents else 0.5
        confidence = int(min(95, 50 + (load_factor * 30) + (capability_factor * 20)))

        return RoutingDecision(
            primary_agent=primary,
            backup_agents=backups,
            routing_strategy=RoutingStrategy.HYBRID,
            confidence=confidence,
            reasoning=f"Hybrid routing: capable agent '{primary}' with load {agent_loads.get(primary, 0.0):.2f}"
        )

    def register_agent_capabilities(self, agent_name: str, capabilities: Set[str]) -> None:
        """
        Register or update agent capabilities.

        Args:
            agent_name: Name of the agent
            capabilities: Set of capability strings
        """
        self._agent_capabilities[agent_name] = capabilities
        self.logger.info(f"Registered capabilities for agent '{agent_name}': {capabilities}")

    def get_capable_agents(self, required_capabilities: Set[str]) -> List[str]:
        """
        Get agents that have all required capabilities.

        Args:
            required_capabilities: Set of required capabilities

        Returns:
            List of agent names with required capabilities
        """
        capable = []

        for agent_name, agent_caps in self._agent_capabilities.items():
            if required_capabilities.issubset(agent_caps):
                capable.append(agent_name)

        return capable

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.

        Returns:
            Statistics dictionary
        """
        if not self._routing_history:
            return {"total_routes": 0}

        total = len(self._routing_history)

        # Count by agent
        agent_counts = {}
        for record in self._routing_history:
            agent = record["agent"]
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        # Average confidence
        avg_confidence = sum(r["confidence"] for r in self._routing_history) / total

        return {
            "total_routes": total,
            "agent_distribution": agent_counts,
            "average_confidence": avg_confidence,
            "default_strategy": self.default_strategy.value
        }
