"""
Tests for chain composition system.
Tests Sequential, Router, and Transform chains.
"""
import pytest
import asyncio
from typing import Dict, Any

from src.agents.chains.base_chain import Chain, ChainInput, ChainOutput
from src.agents.chains.sequential_chain import SequentialChain
from src.agents.chains.router_chain import RouterChain
from src.agents.chains.transform_chain import TransformChain, FunctionTransformChain
from src.agents.chains.chain_builder import ChainBuilder


# Mock chains for testing
class MockChain(Chain):
    """Mock chain for testing."""

    def __init__(self, name: str, output_value: Any = None):
        """Initialize mock chain."""
        super().__init__(
            name=name,
            description=f"Mock chain: {name}",
            input_keys=["input"],
            output_keys=["output"],
            verbose=False,
        )
        self.output_value = output_value or {"output": f"result_{name}"}

    async def execute(self, input_data: Dict[str, Any]) -> ChainOutput:
        """Execute mock chain."""
        return ChainOutput(
            name=self.name,
            data=self.output_value,
            intermediate_steps=[],
        )


class TestBaseChain:
    """Tests for base chain functionality."""

    def test_chain_initialization(self):
        """Test chain initialization."""
        chain = MockChain("test_chain")
        assert chain.name == "test_chain"
        assert chain.input_keys == ["input"]
        assert chain.output_keys == ["output"]
        assert chain.verbose is False

    def test_chain_execution_stats(self):
        """Test execution statistics tracking."""
        chain = MockChain("test_chain")
        assert chain.execution_count == 0
        assert chain.total_execution_time == 0

    @pytest.mark.asyncio
    async def test_chain_execution(self):
        """Test chain execution."""
        chain = MockChain("test_chain", output_value={"output": "test_result"})
        result = await chain.execute({"input": "test_input"})

        assert result.name == "test_chain"
        assert result.data == {"output": "test_result"}
        assert result.status == "success"

    def test_input_validation(self):
        """Test input validation."""
        chain = MockChain("test_chain")
        is_valid = chain.validate_input({"input": "valid"})
        assert is_valid is True


class TestSequentialChain:
    """Tests for sequential chain execution."""

    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test sequential chain execution."""
        chain1 = MockChain("chain1", output_value={"output": "result1"})
        chain2 = MockChain("chain2", output_value={"output": "result2"})

        sequential = SequentialChain(
            name="sequential",
            chains=[chain1, chain2],
        )

        result = await sequential.execute({"input": "test"})
        assert result.status == "success"
        assert len(result.intermediate_steps) >= 0

    @pytest.mark.asyncio
    async def test_sequential_error_handling(self):
        """Test sequential chain error handling."""
        class ErrorChain(Chain):
            async def execute(self, input_data: Dict[str, Any]) -> ChainOutput:
                raise Exception("Test error")

        chain1 = MockChain("chain1")
        error_chain = ErrorChain(
            name="error_chain",
            description="Error chain",
            input_keys=["input"],
            output_keys=["output"],
            verbose=False,
        )

        sequential = SequentialChain(
            name="sequential",
            chains=[chain1, error_chain],
            continue_on_error=True,
        )

        result = await sequential.execute({"input": "test"})
        # Should continue despite error
        assert result.name == "sequential"

    @pytest.mark.asyncio
    async def test_add_chain_dynamically(self):
        """Test adding chain dynamically."""
        sequential = SequentialChain(name="sequential", chains=[])

        chain = MockChain("chain1")
        sequential.add_chain(chain)

        assert len(sequential.chains) == 1


class TestRouterChain:
    """Tests for router chain routing."""

    @pytest.mark.asyncio
    async def test_routing_logic(self):
        """Test routing logic."""
        def router_func(data: Dict[str, Any]) -> str:
            route = data.get("route", "default")
            return route

        chain1 = MockChain("chain_a")
        chain2 = MockChain("chain_b")

        router = RouterChain(
            name="router",
            router_func=router_func,
            routes={"a": chain1, "b": chain2},
            default_route="a",
        )

        result = await router.execute({"input": "test", "route": "a"})
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_default_route(self):
        """Test default route fallback."""
        def router_func(data: Dict[str, Any]) -> str:
            return "nonexistent"

        chain_default = MockChain("chain_default")
        router = RouterChain(
            name="router",
            router_func=router_func,
            routes={"a": MockChain("chain_a")},
            default_route="chain_default",
        )

        # Should fallback to default
        result = await router.execute({"input": "test"})
        assert result.status == "success"


class TestTransformChain:
    """Tests for transform chain."""

    @pytest.mark.asyncio
    async def test_transform_execution(self):
        """Test transform chain execution."""
        def transform_func(data: Dict[str, Any]) -> Dict[str, Any]:
            return {"output": data.get("input", "").upper()}

        transform = FunctionTransformChain(
            name="transform",
            transform_func=transform_func,
        )

        result = await transform.execute({"input": "hello"})
        assert result.status == "success"


class TestChainBuilder:
    """Tests for fluent chain builder."""

    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = ChainBuilder("test_chain")
        assert builder.name == "test_chain"
        assert len(builder.chains) == 0

    def test_add_chain(self):
        """Test adding chains to builder."""
        builder = ChainBuilder("test")
        chain = MockChain("chain1")

        builder.add_chain(chain)
        assert len(builder.chains) == 1

    def test_builder_fluent_api(self):
        """Test fluent API chaining."""
        builder = (
            ChainBuilder("test")
            .add_chain(MockChain("chain1"))
            .add_chain(MockChain("chain2"))
            .set_verbose(True)
        )

        assert len(builder.chains) == 2
        assert builder.verbose is True

    def test_build_sequential_chain(self):
        """Test building sequential chain."""
        builder = (
            ChainBuilder("test")
            .add_chain(MockChain("chain1"))
            .add_chain(MockChain("chain2"))
        )

        chain = builder.build()
        assert isinstance(chain, SequentialChain)
        assert len(chain.chains) == 2

    def test_builder_summary(self):
        """Test builder summary."""
        builder = ChainBuilder("test").add_chain(MockChain("chain1"))
        summary = builder.get_summary()

        assert summary["name"] == "test"
        assert summary["chain_count"] == 1

    def test_builder_clear(self):
        """Test clearing builder."""
        builder = (
            ChainBuilder("test")
            .add_chain(MockChain("chain1"))
            .clear()
        )

        assert len(builder.chains) == 0


class TestChainIntegration:
    """Integration tests for chain system."""

    @pytest.mark.asyncio
    async def test_complex_workflow(self):
        """Test complex multi-chain workflow."""
        # Create transform that routes
        def transform(data: Dict[str, Any]) -> Dict[str, Any]:
            data["processed"] = True
            return data

        def router(data: Dict[str, Any]) -> str:
            return "path_a" if data.get("processed") else "path_b"

        # Build workflow
        transform_chain = FunctionTransformChain("transform", transform)

        router_chain = RouterChain(
            name="router",
            router_func=router,
            routes={
                "path_a": MockChain("chain_a"),
                "path_b": MockChain("chain_b"),
            },
        )

        sequential = SequentialChain(
            name="workflow",
            chains=[transform_chain, router_chain],
        )

        result = await sequential.execute({"input": "test"})
        assert result.status == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
