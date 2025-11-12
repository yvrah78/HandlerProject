"""
Transform Chain for Project Handler.
Applies transformations to data during chain execution.
"""
from typing import Dict, Any, Callable, List, Optional
from src.agents.chains.base_chain import Chain, ChainOutput
from src.core.logging import get_logger

logger = get_logger(__name__)


class TransformChain(Chain):
    """
    Chain that transforms input data using transformation functions.

    Useful for data preprocessing, formatting, and validation.
    """

    def __init__(
        self,
        name: str,
        transforms: List[Callable[[Dict[str, Any]], Dict[str, Any]]],
        input_keys: Optional[List[str]] = None,
        output_keys: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        """
        Initialize transform chain.

        Args:
            name: Chain name
            transforms: List of transform functions to apply in sequence
            input_keys: Input keys
            output_keys: Output keys
            verbose: Enable verbose logging
        """
        self.transforms = transforms

        super().__init__(
            name=name,
            description=f"Transform chain with {len(transforms)} transformations",
            input_keys=input_keys or [],
            output_keys=output_keys or [],
            verbose=verbose,
        )

        logger.info(
            f"Transform chain '{self.name}' initialized with {len(transforms)} transforms"
        )

    async def execute(self, input_data: Dict[str, Any]) -> ChainOutput:
        """
        Apply transformations in sequence.

        Args:
            input_data: Input data

        Returns:
            ChainOutput: Transformed data
        """
        current_data = input_data.copy()
        intermediate_steps = []

        try:
            for i, transform in enumerate(self.transforms):
                if self.verbose:
                    logger.info(
                        f"Applying transform {i + 1}/{len(self.transforms)}"
                    )

                # Apply transformation
                result = transform(current_data)

                # Validate result
                if not isinstance(result, dict):
                    return ChainOutput(
                        success=False,
                        error=f"Transform {i} returned non-dict: {type(result)}",
                        intermediate_steps=intermediate_steps,
                    )

                # Record step
                intermediate_steps.append(
                    {
                        "transform": i,
                        "input_keys": list(current_data.keys()),
                        "output_keys": list(result.keys()),
                    }
                )

                current_data = result

            return ChainOutput(
                success=True,
                data=current_data,
                intermediate_steps=intermediate_steps,
            )

        except Exception as e:
            logger.error(f"Transform chain failed: {str(e)}")
            return ChainOutput(
                success=False,
                error=f"Transform failed: {str(e)}",
                intermediate_steps=intermediate_steps,
            )

    def add_transform(self, transform: Callable) -> None:
        """
        Add a transformation function.

        Args:
            transform: Callable that transforms data
        """
        self.transforms.append(transform)
        logger.info(f"Transform added to chain '{self.name}'")

    def get_info(self) -> Dict[str, Any]:
        """
        Get transform chain information.

        Returns:
            Dict[str, Any]: Chain information
        """
        info = super().get_info()
        info.update(
            {
                "transform_count": len(self.transforms),
                "transforms": [t.__name__ for t in self.transforms],
            }
        )
        return info


class FunctionTransformChain(TransformChain):
    """
    Transform chain using a single async function.

    Useful for complex transformations in a single step.
    """

    def __init__(
        self,
        name: str,
        transform_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        input_keys: Optional[List[str]] = None,
        output_keys: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        """
        Initialize function transform chain.

        Args:
            name: Chain name
            transform_func: Single transformation function
            input_keys: Input keys
            output_keys: Output keys
            verbose: Enable verbose logging
        """
        self.transform_func = transform_func

        super().__init__(
            name=name,
            transforms=[transform_func],
            input_keys=input_keys,
            output_keys=output_keys,
            verbose=verbose,
        )
