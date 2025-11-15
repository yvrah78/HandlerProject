"""
LangChain-enabled agent base class.

This module provides a base class for agents that use LangChain
for intelligent decision-making and task execution.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from src.agents.base_agent import BaseAgent
from src.core.langchain_config import get_langchain_config, LLMProvider
from src.core.logging import get_logger
from src.core.exceptions import AgentError


logger = get_logger(__name__)


# Default ReAct prompt template for agents
REACT_PROMPT_TEMPLATE = """You are an AI agent named {agent_name} with the following capabilities:
{agent_description}

You have access to the following tools:
{tools}

Use the following format:

Question: the input question or task you must solve
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin! Remember to provide detailed, accurate responses.

Previous conversation:
{chat_history}

Question: {input}
{agent_scratchpad}"""


class LangChainAgent(BaseAgent):
    """
    Base class for LangChain-enabled agents.

    Extends BaseAgent with LangChain capabilities including:
    - LLM-powered reasoning (via Claude or other models)
    - Tool usage and chaining
    - Memory and context management
    - ReAct (Reasoning + Acting) pattern
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: List[BaseTool],
        llm_provider: LLMProvider = LLMProvider.CLAUDE,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_iterations: int = 10,
        enable_memory: bool = True
    ):
        """
        Initialize LangChain-enabled agent.

        Args:
            name: Agent name
            description: Agent description/capabilities
            tools: List of LangChain tools available to agent
            llm_provider: LLM provider to use
            model: Specific model name (optional)
            temperature: LLM temperature (0-1)
            max_iterations: Maximum reasoning iterations
            enable_memory: Whether to enable conversation memory
        """
        super().__init__(name, description)

        self.tools = tools
        self.llm_provider = llm_provider
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations

        # Get LangChain config
        self.lc_config = get_langchain_config()

        # Initialize LLM
        self.llm = self.lc_config.get_llm(
            provider=llm_provider,
            model=model,
            temperature=temperature
        )

        # Initialize memory
        self.memory = None
        if enable_memory:
            self.memory = self.lc_config.get_memory(memory_type="buffer")

        # Initialize callback handler
        self.callback_handler = self.lc_config.get_callback_handler(name)

        # Create agent executor
        self.agent_executor = self._create_agent_executor()

        logger.info(
            f"LangChain agent '{name}' initialized with {len(tools)} tools",
            extra={"provider": llm_provider, "model": model or "default"}
        )

    def _create_agent_executor(self) -> AgentExecutor:
        """
        Create LangChain agent executor.

        Returns:
            AgentExecutor: Configured agent executor
        """
        # Create prompt
        prompt = PromptTemplate(
            template=REACT_PROMPT_TEMPLATE,
            input_variables=["agent_name", "agent_description", "tools",
                           "tool_names", "chat_history", "input", "agent_scratchpad"],
        )

        # Fill in agent-specific details
        tool_names = [tool.name for tool in self.tools]
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])

        # Create partial prompt with agent details
        agent_prompt = prompt.partial(
            agent_name=self.name,
            agent_description=self.description,
            tools=tool_descriptions,
            tool_names=", ".join(tool_names)
        )

        # Create ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=agent_prompt
        )

        # Create executor
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            callbacks=[self.callback_handler]
        )

        return executor

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task using LangChain agent.

        Args:
            input_data: Input data with 'task' or 'query' key

        Returns:
            Dict[str, Any]: Processing result
        """
        # Extract task/query from input
        task = input_data.get("task") or input_data.get("query") or str(input_data)

        logger.info(f"Processing task with LangChain: {task[:100]}")

        try:
            # Execute agent
            result = self.agent_executor.invoke({
                "input": task,
                "chat_history": self.memory.buffer if self.memory else ""
            })

            # Extract output
            output = result.get("output", "No output generated")

            logger.info(f"LangChain agent completed task successfully")

            return {
                "status": "success",
                "output": output,
                "intermediate_steps": result.get("intermediate_steps", []),
                "tool_usage": self._extract_tool_usage(result),
            }

        except Exception as e:
            logger.error(f"LangChain agent error: {str(e)}", exc_info=True)
            raise AgentError(
                f"LangChain processing failed: {str(e)}",
                agent_name=self.name,
                details={"task": task}
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid
        """
        # For LangChain agents, we accept any dict with task/query or any dict
        return isinstance(input_data, dict)

    def _extract_tool_usage(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract tool usage information from agent result.

        Args:
            result: Agent execution result

        Returns:
            List[Dict[str, str]]: Tool usage information
        """
        tool_usage = []
        intermediate_steps = result.get("intermediate_steps", [])

        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) == 2:
                action, observation = step
                if hasattr(action, 'tool'):
                    tool_usage.append({
                        "tool": action.tool,
                        "input": str(action.tool_input)[:100],
                        "output": str(observation)[:100]
                    })

        return tool_usage

    def add_tool(self, tool: BaseTool):
        """
        Add a tool to the agent.

        Args:
            tool: LangChain tool to add
        """
        self.tools.append(tool)
        # Recreate agent executor with new tools
        self.agent_executor = self._create_agent_executor()
        logger.info(f"Tool '{tool.name}' added to agent '{self.name}'")

    def remove_tool(self, tool_name: str):
        """
        Remove a tool from the agent.

        Args:
            tool_name: Name of tool to remove
        """
        self.tools = [t for t in self.tools if t.name != tool_name]
        # Recreate agent executor
        self.agent_executor = self._create_agent_executor()
        logger.info(f"Tool '{tool_name}' removed from agent '{self.name}'")

    def clear_memory(self):
        """Clear agent's conversation memory."""
        if self.memory:
            self.memory.clear()
            logger.info(f"Memory cleared for agent '{self.name}'")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Dict[str, Any]: Agent statistics
        """
        base_stats = self.get_status()
        base_stats.update({
            "langchain_enabled": True,
            "llm_provider": self.llm_provider,
            "tool_count": len(self.tools),
            "tools": [tool.name for tool in self.tools],
            "has_memory": self.memory is not None,
            "llm_calls": self.callback_handler.call_count,
            "total_tokens": self.callback_handler.total_tokens,
        })
        return base_stats
