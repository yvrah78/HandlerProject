"""
Chain Builder for Project Handler.
Provides fluent API for building complex chain compositions.
"""
from typing import Dict, Any, Callable, List, Optional
from src.agents.chains.base_chain import Chain
from src.agents.chains.sequential_chain import SequentialChain
from src.agents.chains.router_chain import RouterChain
from src.agents.chains.transform_chain import TransformChain, FunctionTransformChain
from src.core.logging import get_logger

logger = get_logger(__name__)


class ChainBuilder:
    """
    Fluent builder for composing complex chain workflows.

    Allows easy construction of sequential, router, and transform chains.
    """

    def __init__(self, name: str):
        """
        Initialize chain builder.

        Args:
            name: Name for the final chain
        """
        self.name = name
        self.chains: List[Chain] = []
        self.verbose = False
        self.continue_on_error = False

    def add_chain(self, chain: Chain) -> "ChainBuilder":
        """
        Add a chain to the sequence.

        Args:
            chain: Chain to add

        Returns:
            ChainBuilder: Self for chaining
        """
        self.chains.append(chain)
        return self

    def add_chains(self, chains: List[Chain]) -> "ChainBuilder":
        """
        Add multiple chains at once.

        Args:
            chains: List of chains to add

        Returns:
            ChainBuilder: Self for chaining
        """
        self.chains.extend(chains)
        return self

    def add_transform(
        self, transform_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> "ChainBuilder":
        """
        Add a transform function as a chain.

        Args:
            transform_func: Transform function

        Returns:
            ChainBuilder: Self for chaining
        """
        transform_name = f"{self.name}_transform_{len(self.chains)}"
        chain = FunctionTransformChain(transform_name, transform_func)
        self.chains.append(chain)
        return self

    def add_router(
        self,
        router_name: str,
        router_func: Callable[[Dict[str, Any]], str],
        routes: Dict[str, Chain],
        default_route: Optional[str] = None,
    ) -> "ChainBuilder":
        """
        Add a router chain.

        Args:
            router_name: Name for the router
            router_func: Function that determines route
            routes: Mapping of route keys to chains
            default_route: Default route if not found

        Returns:
            ChainBuilder: Self for chaining
        """
        router = RouterChain(
            router_name,
            router_func,
            routes,
            default_route,
            verbose=self.verbose,
        )
        self.chains.append(router)
        return self

    def set_verbose(self, verbose: bool = True) -> "ChainBuilder":
        """
        Enable/disable verbose logging.

        Args:
            verbose: Verbose flag

        Returns:
            ChainBuilder: Self for chaining
        """
        self.verbose = verbose
        return self

    def set_continue_on_error(self, continue_on_error: bool = True) -> "ChainBuilder":
        """
        Set error handling behavior.

        Args:
            continue_on_error: Continue execution on error

        Returns:
            ChainBuilder: Self for chaining
        """
        self.continue_on_error = continue_on_error
        return self

    def build(self) -> SequentialChain:
        """
        Build the final chain.

        Returns:
            SequentialChain: Composed chain

        Raises:
            ValueError: If no chains added
        """
        if not self.chains:
            raise ValueError("No chains added to builder")

        chain = SequentialChain(
            name=self.name,
            chains=self.chains,
            continue_on_error=self.continue_on_error,
            verbose=self.verbose,
        )

        logger.info(
            f"Chain '{self.name}' built with {len(self.chains)} sub-chains"
        )

        return chain

    def build_router(
        self,
        router_name: str,
        router_func: Callable[[Dict[str, Any]], str],
        default_route: Optional[str] = None,
    ) -> RouterChain:
        """
        Build a router chain from current chains.

        Args:
            router_name: Name for the router
            router_func: Function that determines route
            default_route: Default route

        Returns:
            RouterChain: Router chain

        Raises:
            ValueError: If no chains added
        """
        if not self.chains:
            raise ValueError("No chains added to builder")

        routes = {chain.name: chain for chain in self.chains}

        router = RouterChain(
            router_name,
            router_func,
            routes,
            default_route,
            verbose=self.verbose,
        )

        logger.info(f"Router chain '{router_name}' built with {len(routes)} routes")

        return router

    def get_summary(self) -> Dict[str, Any]:
        """
        Get builder summary.

        Returns:
            Dict[str, Any]: Summary information
        """
        return {
            "name": self.name,
            "chain_count": len(self.chains),
            "chains": [chain.name for chain in self.chains],
            "verbose": self.verbose,
            "continue_on_error": self.continue_on_error,
        }

    def clear(self) -> "ChainBuilder":
        """
        Clear all chains.

        Returns:
            ChainBuilder: Self for chaining
        """
        self.chains.clear()
        return self
