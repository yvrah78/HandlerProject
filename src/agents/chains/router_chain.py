"""
Router Chain for Project Handler.
Routes execution to different chains based on conditions.
"""
from typing import Dict, Any, Callable, Optional
from src.agents.chains.base_chain import Chain, ChainOutput
from src.core.logging import get_logger

logger = get_logger(__name__)


class RouterChain(Chain):
    """
    Chain that routes to different chains based on conditions.

    Useful for conditional branching in agent workflows.
    """

    def __init__(
        self,
        name: str,
        router_func: Callable[[Dict[str, Any]], str],
        chains: Dict[str, Chain],
        default_chain: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize router chain.

        Args:
            name: Chain name
            router_func: Function that determines which chain to use
                         Takes input dict, returns chain key
            chains: Mapping of route keys to Chain instances
            default_chain: Default chain if router_func result not in chains
            verbose: Enable verbose logging
        """
        self.router_func = router_func
        self.chains = chains
        self.default_chain = default_chain

        # Collect input/output keys from all chains
        input_keys = []
        output_keys = []
        for chain in chains.values():
            input_keys.extend(chain.input_keys)
            output_keys.extend(chain.output_keys)

        # Remove duplicates
        input_keys = list(set(input_keys))
        output_keys = list(set(output_keys))

        super().__init__(
            name=name,
            description=f"Router chain with {len(chains)} routes",
            input_keys=input_keys,
            output_keys=output_keys,
            verbose=verbose,
        )

        logger.info(
            f"Router chain '{self.name}' initialized with {len(chains)} routes"
        )

    async def execute(self, input_data: Dict[str, Any]) -> ChainOutput:
        """
        Route and execute appropriate chain.

        Args:
            input_data: Input data

        Returns:
            ChainOutput: Output from selected chain
        """
        try:
            # Determine route
            route_key = self.router_func(input_data)

            if self.verbose:
                logger.info(f"Router selected route: {route_key}")

            # Get chain for route
            if route_key not in self.chains:
                if self.default_chain and self.default_chain in self.chains:
                    route_key = self.default_chain
                    logger.warning(
                        f"Route '{route_key}' not found, using default chain"
                    )
                else:
                    return ChainOutput(
                        success=False,
                        error=f"Route '{route_key}' not found and no default chain",
                    )

            chain = self.chains[route_key]

            if self.verbose:
                logger.info(f"Executing chain: {chain.name}")

            # Execute selected chain
            result = await chain.run(input_data)

            return ChainOutput(
                success=result.success,
                data=result.data,
                error=result.error,
                intermediate_steps=[
                    {
                        "router": self.name,
                        "selected_route": route_key,
                        "chain": chain.name,
                        "success": result.success,
                    }
                ],
            )

        except Exception as e:
            logger.error(f"Router chain execution failed: {str(e)}")
            return ChainOutput(
                success=False,
                error=f"Router chain error: {str(e)}",
            )

    def get_routes(self) -> list:
        """
        Get available routes.

        Returns:
            list: List of route keys
        """
        return list(self.chains.keys())

    def add_route(self, key: str, chain: Chain) -> None:
        """
        Add a new route.

        Args:
            key: Route key
            chain: Chain for this route
        """
        self.chains[key] = chain
        logger.info(f"Route '{key}' added to router '{self.name}'")

    def remove_route(self, key: str) -> None:
        """
        Remove a route.

        Args:
            key: Route key to remove
        """
        if key in self.chains:
            del self.chains[key]
            logger.info(f"Route '{key}' removed from router '{self.name}'")

    def get_info(self) -> Dict[str, Any]:
        """
        Get router chain information.

        Returns:
            Dict[str, Any]: Router information
        """
        info = super().get_info()
        info.update(
            {
                "route_count": len(self.chains),
                "routes": list(self.chains.keys()),
                "default_route": self.default_chain,
            }
        )
        return info
