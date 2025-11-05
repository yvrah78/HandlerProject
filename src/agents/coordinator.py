"""
Coordinator Agent for Project Handler.
Orchestrates and delegates tasks to specialized agents.
"""
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError


class CoordinatorAgent(BaseAgent):
    """
    Main coordinator agent that orchestrates tasks across specialized agents.

    This agent receives requests and delegates them to appropriate
    specialized agents (communications, financial, operations, analytics).
    """

    def __init__(self):
        super().__init__(
            name="coordinator",
            description="Main orchestration agent for task delegation"
        )
        self.specialized_agents = {}

    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register a specialized agent.

        Args:
            agent_type: Type identifier for the agent
            agent: Agent instance to register
        """
        self.specialized_agents[agent_type] = agent
        self.logger.info(f"Registered {agent_type} agent: {agent.name}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process coordination request.

        Args:
            input_data: Must contain 'task_type' and 'data' fields

        Returns:
            Dict[str, Any]: Coordination result
        """
        task_type = input_data.get("task_type")
        task_data = input_data.get("data", {})

        self.logger.info(f"Coordinating task of type: {task_type}")

        # Route to appropriate agent
        if task_type in self.specialized_agents:
            agent = self.specialized_agents[task_type]
            result = await agent.execute(task_data)
            return {
                "task_type": task_type,
                "delegated_to": agent.name,
                "result": result
            }

        # Handle task directly if no specialized agent
        return {
            "task_type": task_type,
            "status": "handled_directly",
            "message": f"Task {task_type} processed by coordinator"
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate coordinator input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(input_data, dict):
            raise ValidationError(
                "Input must be a dictionary",
                details={"received_type": type(input_data).__name__}
            )

        if "task_type" not in input_data:
            raise ValidationError(
                "Missing required field: task_type",
                details={"received_keys": list(input_data.keys())}
            )

        return True

    def get_registered_agents(self) -> Dict[str, str]:
        """
        Get list of registered agents.

        Returns:
            Dict[str, str]: Mapping of agent types to names
        """
        return {
            agent_type: agent.name
            for agent_type, agent in self.specialized_agents.items()
        }
