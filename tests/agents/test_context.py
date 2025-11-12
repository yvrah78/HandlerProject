"""
Tests for context management system.
Tests ContextScope and ContextManager.
"""
import pytest

from src.agents.context import ContextScope, ContextManager


class TestContextScope:
    """Tests for context scope."""

    def test_scope_initialization(self):
        """Test scope initialization."""
        scope = ContextScope("global")
        assert scope.name == "global"
        assert scope.parent is None
        assert len(scope.variables) == 0

    def test_set_and_get(self):
        """Test setting and getting variables."""
        scope = ContextScope("test")
        scope.set("key1", "value1")

        assert scope.get("key1") == "value1"
        assert scope.get("nonexistent") is None

    def test_parent_relationship(self):
        """Test parent-child relationship."""
        parent = ContextScope("parent")
        child = ContextScope("child", parent=parent)

        assert child.parent == parent
        assert parent.parent is None

    def test_resolve_hierarchy(self):
        """Test variable resolution in hierarchy."""
        parent = ContextScope("parent")
        child = ContextScope("child", parent=parent)

        parent.set("parent_var", "parent_value")
        child.set("child_var", "child_value")

        # Child can see its own and parent's variables
        assert child.resolve("child_var") == "child_value"
        assert child.resolve("parent_var") == "parent_value"

        # Parent cannot see child's variables
        assert parent.resolve("child_var") is None
        assert parent.resolve("parent_var") == "parent_value"

    def test_clear(self):
        """Test clearing scope."""
        scope = ContextScope("test")
        scope.set("key", "value")

        scope.clear()
        assert scope.get("key") is None

    def test_to_dict(self):
        """Test converting scope to dict."""
        scope = ContextScope("test")
        scope.set("key1", "value1")
        scope.set("key2", "value2")

        d = scope.to_dict()
        assert d["key1"] == "value1"
        assert d["key2"] == "value2"


class TestContextManager:
    """Tests for context manager."""

    def test_initialization(self):
        """Test context manager initialization."""
        manager = ContextManager()

        assert manager.current_scope.name == "global"
        assert len(manager.scope_stack) == 1

    def test_set_and_get(self):
        """Test setting and getting in current scope."""
        manager = ContextManager()

        manager.set("key", "value")
        assert manager.get("key") == "value"

    def test_push_scope(self):
        """Test pushing a new scope."""
        manager = ContextManager()

        scope = manager.push_scope("task1")
        assert scope.name == "task1"
        assert len(manager.scope_stack) == 2
        assert manager.current_scope == scope

    def test_pop_scope(self):
        """Test popping scope."""
        manager = ContextManager()

        manager.push_scope("task1")
        popped = manager.pop_scope()

        assert popped.name == "task1"
        assert len(manager.scope_stack) == 1
        assert manager.current_scope.name == "global"

    def test_scope_isolation(self):
        """Test scope isolation."""
        manager = ContextManager()

        manager.set("global_var", "global_value")

        manager.push_scope("task1")
        manager.set("task_var", "task_value")

        # Task scope can see both
        assert manager.get("task_var") == "task_value"
        assert manager.get("global_var") == "global_value"

        manager.pop_scope()

        # Global scope only sees global var
        assert manager.get("global_var") == "global_value"
        assert manager.get("task_var") is None

    def test_get_scope_chain(self):
        """Test getting scope chain for variable."""
        manager = ContextManager()

        manager.set("var", "global_value")
        manager.push_scope("task1")
        manager.set("var", "task_value")

        chain = manager.get_scope_chain("var")

        # Should find variable in both scopes
        assert len(chain) == 2
        assert chain[0][0] == "task1"  # Current scope first
        assert chain[1][0] == "global"  # Parent scope

    def test_propagate_to_global(self):
        """Test propagating variable to global scope."""
        manager = ContextManager()

        manager.push_scope("task1")
        manager.set("task_var", "task_value")

        manager.propagate("propagated", "propagated_value")

        manager.pop_scope()

        # Should be in global scope now
        assert manager.get("propagated") == "propagated_value"

    def test_merge_scope(self):
        """Test merging dictionary into scope."""
        manager = ContextManager()

        merge_dict = {"var1": "value1", "var2": "value2"}
        manager.merge_scope(merge_dict)

        assert manager.get("var1") == "value1"
        assert manager.get("var2") == "value2"

    def test_export_context(self):
        """Test exporting context."""
        manager = ContextManager()

        manager.set("global_var", "global_value")
        manager.push_scope("task1")
        manager.set("task_var", "task_value")

        exported = manager.export_context()

        assert "global" in exported
        assert "scopes" in exported
        assert len(exported["scopes"]) > 0

    def test_nested_scopes(self):
        """Test nested scopes."""
        manager = ContextManager()

        manager.push_scope("level1")
        manager.set("level1_var", "level1_value")

        manager.push_scope("level2")
        manager.set("level2_var", "level2_value")

        # Can see all variables
        assert manager.get("level2_var") == "level2_value"
        assert manager.get("level1_var") == "level1_value"
        assert manager.get("global_var", "default") == "default"

    def test_clear_current_scope(self):
        """Test clearing current scope."""
        manager = ContextManager()

        manager.push_scope("task1")
        manager.set("var", "value")

        manager.clear_current_scope()

        assert manager.get("var") is None

    def test_clear_all(self):
        """Test clearing all scopes."""
        manager = ContextManager()

        manager.set("global_var", "value")
        manager.push_scope("task1")
        manager.set("task_var", "value")

        manager.clear_all()

        assert len(manager.scope_stack) == 1
        assert manager.get("global_var") is None
        assert manager.get("task_var") is None

    def test_get_context_info(self):
        """Test getting context information."""
        manager = ContextManager()

        manager.set("var1", "value1")
        manager.set("var2", "value2")

        manager.push_scope("task1")
        manager.set("var3", "value3")

        info = manager.get_context_info()

        assert info["current_scope"] == "task1"
        assert info["scope_depth"] == 2
        assert info["variable_count"] == 1  # Only task scope variables
        assert info["total_variables"] == 3  # All variables

    def test_default_value(self):
        """Test default value in get()."""
        manager = ContextManager()

        value = manager.get("nonexistent", default="default_value")
        assert value == "default_value"

    def test_scope_stack_integrity(self):
        """Test scope stack integrity after operations."""
        manager = ContextManager()

        initial_depth = len(manager.scope_stack)

        manager.push_scope("task1")
        manager.push_scope("task2")

        assert len(manager.scope_stack) == initial_depth + 2

        manager.pop_scope()
        manager.pop_scope()

        assert len(manager.scope_stack) == initial_depth


class TestContextIntegration:
    """Integration tests for context system."""

    def test_multi_task_context_isolation(self):
        """Test context isolation for multiple tasks."""
        manager = ContextManager()

        # Simulate task 1
        manager.push_scope("task1")
        manager.set("task_id", "task_1")
        manager.set("status", "running")

        # Store task1 state
        task1_context = manager.export_context()

        # Pop and start task 2
        manager.pop_scope()
        manager.push_scope("task2")
        manager.set("task_id", "task_2")
        manager.set("status", "processing")

        # Tasks have different contexts
        assert manager.get("task_id") == "task_2"

        manager.pop_scope()
        manager.push_scope("task1")

        # Task 1 context is restored... wait, it won't be because we popped it
        # This is expected behavior - context is not persistent across pops
        assert manager.get("task_id") is None  # Because we popped the scope

    def test_context_propagation_to_global(self):
        """Test propagating important data to global scope."""
        manager = ContextManager()

        manager.push_scope("agent_task")
        manager.set("result", "important_result")
        manager.propagate("result", "important_result")

        manager.pop_scope()

        # Result is now available globally
        assert manager.get("result") == "important_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
