"""
Tool Registry for Project Handler agents.
Manages tool registration, discovery, and execution.
"""
from typing import Dict, List, Optional, Any
from src.agents.tools.base_tool import BaseTool, ToolOutput
from src.core.logging import get_logger
from src.core.exceptions import AgentError

logger = get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing agent tools.

    Provides centralized tool management including registration,
    discovery, and execution with permission checking.
    """

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(
        self, tool: BaseTool, category: str = "general"
    ) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
            category: Tool category for organization

        Raises:
            AgentError: If tool with same name already registered
        """
        if tool.name in self._tools:
            raise AgentError(
                f"Tool '{tool.name}' already registered",
                details={"tool_name": tool.name},
            )

        self._tools[tool.name] = tool

        # Add to category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)

        logger.info(f"Registered tool: {tool.name} (category: {category})")

    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool.

        Args:
            tool_name: Name of tool to unregister

        Raises:
            AgentError: If tool not found
        """
        if tool_name not in self._tools:
            raise AgentError(
                f"Tool '{tool_name}' not found",
                details={"tool_name": tool_name},
            )

        del self._tools[tool_name]

        # Remove from categories
        for category in self._categories.values():
            if tool_name in category:
                category.remove(tool_name)

        logger.info(f"Unregistered tool: {tool_name}")

    def get(self, tool_name: str) -> BaseTool:
        """
        Get a tool by name.

        Args:
            tool_name: Name of tool to retrieve

        Returns:
            BaseTool: The requested tool

        Raises:
            AgentError: If tool not found
        """
        if tool_name not in self._tools:
            raise AgentError(
                f"Tool '{tool_name}' not found",
                details={"tool_name": tool_name},
                available_tools=list(self._tools.keys()),
            )

        return self._tools[tool_name]

    async def execute(
        self, tool_name: str, input_data: Dict[str, Any]
    ) -> ToolOutput:
        """
        Execute a tool.

        Args:
            tool_name: Name of tool to execute
            input_data: Input for the tool

        Returns:
            ToolOutput: Execution result

        Raises:
            AgentError: If tool not found or execution fails
        """
        tool = self.get(tool_name)
        logger.info(f"Executing tool: {tool_name}")

        try:
            result = await tool.run(input_data)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}: {str(e)}")
            raise AgentError(
                f"Tool execution failed: {str(e)}",
                details={"tool_name": tool_name, "error": str(e)},
            )

    def list_tools(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available tools.

        Args:
            category: Filter by category (None = all)

        Returns:
            List[Dict[str, Any]]: Tool information
        """
        tools_to_list = self._tools

        if category and category in self._categories:
            tool_names = self._categories[category]
            tools_to_list = {
                name: tool for name, tool in self._tools.items() if name in tool_names
            }

        return [tool.get_info() for tool in tools_to_list.values()]

    def get_categories(self) -> Dict[str, List[str]]:
        """
        Get tool categories.

        Returns:
            Dict[str, List[str]]: Mapping of categories to tool names
        """
        return self._categories.copy()

    def get_tools_by_permission(self, permission: str) -> List[str]:
        """
        Get all tools requiring a specific permission.

        Args:
            permission: Permission to search for

        Returns:
            List[str]: Tool names requiring the permission
        """
        return [
            name
            for name, tool in self._tools.items()
            if tool.check_permission(permission)
        ]

    def validate_permissions(
        self, tool_name: str, available_permissions: List[str]
    ) -> bool:
        """
        Validate if tool can be executed with given permissions.

        Args:
            tool_name: Tool to check
            available_permissions: Available permissions

        Returns:
            bool: True if tool can be executed

        Raises:
            AgentError: If tool not found
        """
        tool = self.get(tool_name)
        return all(p in available_permissions for p in tool.required_permissions)

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get registry information.

        Returns:
            Dict[str, Any]: Registry metadata
        """
        return {
            "total_tools": len(self._tools),
            "categories": {
                cat: len(tools) for cat, tools in self._categories.items()
            },
            "tools": list(self._tools.keys()),
        }

    def clear(self) -> None:
        """Clear all tools from registry."""
        self._tools.clear()
        self._categories.clear()
        logger.info("Tool registry cleared")
