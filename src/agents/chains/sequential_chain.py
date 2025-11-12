"""
Sequential Chain for Project Handler.
Executes multiple chains in sequence, passing output as input to next chain.
"""
from typing import List, Dict, Any, Optional
from src.agents.chains.base_chain import Chain, ChainOutput
from src.core.logging import get_logger

logger = get_logger(__name__)


class SequentialChain(Chain):
    """
    Chain that executes a sequence of chains in order.

    Each chain's output becomes input for the next chain.
    Stops on first error unless continue_on_error is True.
    """

    def __init__(
        self,
        name: str,
        chains: List[Chain],
        input_keys: Optional[List[str]] = None,
        output_keys: Optional[List[str]] = None,
        continue_on_error: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize sequential chain.

        Args:
            name: Chain name
            chains: List of chains to execute sequentially
            input_keys: Input keys for the sequence
            output_keys: Output keys from final chain
            continue_on_error: Continue even if a chain fails
            verbose: Enable verbose logging
        """
        self.chains = chains
        self.continue_on_error = continue_on_error

        # Infer keys from first and last chains if not provided
        if not input_keys and chains:
            input_keys = chains[0].input_keys
        if not output_keys and chains:
            output_keys = chains[-1].output_keys

        super().__init__(
            name=name,
            description=f"Sequential execution of {len(chains)} chains",
            input_keys=input_keys,
            output_keys=output_keys,
            verbose=verbose,
        )

        logger.info(
            f"Sequential chain '{self.name}' initialized with {len(chains)} chains"
        )

    async def execute(self, input_data: Dict[str, Any]) -> ChainOutput:
        """
        Execute chains in sequence.

        Args:
            input_data: Initial input data

        Returns:
            ChainOutput: Final output from all chains
        """
        current_data = input_data.copy()
        intermediate_steps = []

        for i, chain in enumerate(self.chains):
            if self.verbose:
                logger.info(f"Executing chain {i + 1}/{len(self.chains)}: {chain.name}")

            try:
                # Execute chain
                result = await chain.run(current_data)

                # Record intermediate step
                intermediate_steps.append(
                    {
                        "chain": chain.name,
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                    }
                )

                # Check for errors
                if not result.success:
                    if not self.continue_on_error:
                        return ChainOutput(
                            success=False,
                            error=f"Chain '{chain.name}' failed: {result.error}",
                            intermediate_steps=intermediate_steps,
                        )
                    else:
                        logger.warning(
                            f"Chain '{chain.name}' failed but continuing: {result.error}"
                        )
                        continue

                # Update current data with result
                if result.data:
                    if isinstance(result.data, dict):
                        current_data.update(result.data)
                    else:
                        current_data["output"] = result.data

            except Exception as e:
                logger.error(f"Error executing chain {i}: {str(e)}")

                if not self.continue_on_error:
                    return ChainOutput(
                        success=False,
                        error=f"Exception in chain '{chain.name}': {str(e)}",
                        intermediate_steps=intermediate_steps,
                    )
                else:
                    intermediate_steps.append(
                        {
                            "chain": chain.name,
                            "success": False,
                            "error": str(e),
                        }
                    )
                    continue

        # Return final output
        return ChainOutput(
            success=True,
            data=current_data,
            intermediate_steps=intermediate_steps,
        )

    def get_chain_sequence(self) -> List[str]:
        """
        Get sequence of chain names.

        Returns:
            List[str]: Chain names in order
        """
        return [chain.name for chain in self.chains]

    def add_chain(self, chain: Chain) -> None:
        """
        Add a chain to the sequence.

        Args:
            chain: Chain to add
        """
        self.chains.append(chain)
        logger.info(f"Chain '{chain.name}' added to sequence '{self.name}'")

    def remove_chain(self, index: int) -> None:
        """
        Remove a chain from the sequence.

        Args:
            index: Index of chain to remove
        """
        if 0 <= index < len(self.chains):
            removed = self.chains.pop(index)
            logger.info(f"Chain '{removed.name}' removed from sequence '{self.name}'")

    def get_info(self) -> Dict[str, Any]:
        """
        Get chain information including sub-chains.

        Returns:
            Dict[str, Any]: Chain information
        """
        info = super().get_info()
        info.update(
            {
                "chain_count": len(self.chains),
                "chains": [chain.name for chain in self.chains],
                "continue_on_error": self.continue_on_error,
            }
        )
        return info
