"""
Advanced Context Management for Project Handler agents.
Manages context stack, propagation, and variable resolution.
"""
from typing import Dict, Any, Optional, List, Stack
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class ContextScope:
    """Represents a scope level in the context hierarchy."""

    def __init__(self, name: str, parent: Optional["ContextScope"] = None):
        """Initialize context scope."""
        self.name = name
        self.parent = parent
        self.variables: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()

    def set(self, key: str, value: Any) -> None:
        """Set variable in this scope."""
        self.variables[key] = value

    def get(self, key: str) -> Optional[Any]:
        """Get variable from this scope only."""
        return self.variables.get(key)

    def resolve(self, key: str) -> Optional[Any]:
        """Resolve variable checking up the hierarchy."""
        if key in self.variables:
            return self.variables[key]
        if self.parent:
            return self.parent.resolve(key)
        return None

    def clear(self) -> None:
        """Clear all variables in this scope."""
        self.variables.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert scope to dictionary."""
        return self.variables.copy()


class ContextManager:
    """
    Advanced context management for agents.

    Supports:
    - Hierarchical scopes
    - Context stacking
    - Variable propagation
    - Scope isolation
    """

    def __init__(self):
        """Initialize context manager."""
        self.global_scope = ContextScope("global")
        self.current_scope = self.global_scope
        self.scope_stack: List[ContextScope] = [self.global_scope]

    def push_scope(self, scope_name: str) -> ContextScope:
        """
        Push a new scope onto the stack.

        Args:
            scope_name: Name of the new scope

        Returns:
            ContextScope: New scope
        """
        new_scope = ContextScope(scope_name, parent=self.current_scope)
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope

        logger.debug(f"Scope pushed: {scope_name}")

        return new_scope

    def pop_scope(self) -> Optional[ContextScope]:
        """
        Pop the current scope from the stack.

        Returns:
            ContextScope: Popped scope or None if at global level
        """
        if len(self.scope_stack) > 1:
            popped = self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]

            logger.debug(f"Scope popped: {popped.name}")

            return popped

        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set variable in current scope.

        Args:
            key: Variable key
            value: Variable value
        """
        self.current_scope.set(key, value)
        logger.debug(f"Set {key} in scope {self.current_scope.name}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get variable from context (searches up scope hierarchy).

        Args:
            key: Variable key
            default: Default value if not found

        Returns:
            Variable value or default
        """
        value = self.current_scope.resolve(key)
        return value if value is not None else default

    def get_scope_chain(self, key: str) -> List[tuple]:
        """
        Get chain of scopes containing a variable.

        Args:
            key: Variable key

        Returns:
            List of (scope_name, value) tuples
        """
        chain = []
        scope = self.current_scope

        while scope:
            if key in scope.variables:
                chain.append((scope.name, scope.variables[key]))
            scope = scope.parent

        return chain

    def propagate(self, key: str, value: Any) -> None:
        """
        Propagate variable to global scope.

        Args:
            key: Variable key
            value: Variable value
        """
        self.global_scope.set(key, value)
        logger.debug(f"Propagated {key} to global scope")

    def merge_scope(self, scope_dict: Dict[str, Any]) -> None:
        """
        Merge dictionary into current scope.

        Args:
            scope_dict: Dictionary to merge
        """
        for key, value in scope_dict.items():
            self.current_scope.set(key, value)

    def export_context(self) -> Dict[str, Any]:
        """
        Export entire context hierarchy.

        Returns:
            Dict with all scopes and variables
        """
        result = {
            "global": self.global_scope.to_dict(),
            "scopes": [],
        }

        for scope in self.scope_stack[1:]:  # Skip global
            result["scopes"].append(
                {
                    "name": scope.name,
                    "variables": scope.to_dict(),
                }
            )

        return result

    def clear_current_scope(self) -> None:
        """Clear variables in current scope."""
        self.current_scope.clear()
        logger.debug(f"Cleared scope: {self.current_scope.name}")

    def clear_all(self) -> None:
        """Clear all scopes except global."""
        self.global_scope.clear()
        self.scope_stack = [self.global_scope]
        self.current_scope = self.global_scope
        logger.info("Cleared all contexts")

    def get_context_info(self) -> Dict[str, Any]:
        """
        Get context information.

        Returns:
            Dict with context stats
        """
        return {
            "current_scope": self.current_scope.name,
            "scope_depth": len(self.scope_stack),
            "variable_count": len(self.current_scope.to_dict()),
            "total_variables": sum(
                len(scope.to_dict()) for scope in self.scope_stack
            ),
        }
