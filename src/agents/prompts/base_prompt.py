"""
Base Prompt Template for Project Handler agents.
Provides template functionality for dynamic prompt generation.
"""
from typing import Dict, Any, List, Optional
from string import Template
from src.core.logging import get_logger

logger = get_logger(__name__)


class PromptTemplate:
    """
    Template system for generating prompts dynamically.

    Supports variable substitution, examples, and formatting.
    """

    def __init__(
        self,
        template: str,
        input_variables: List[str],
        examples: Optional[List[Dict[str, str]]] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize prompt template.

        Args:
            template: Template string with {variable} placeholders
            input_variables: List of required variables
            examples: Optional list of example inputs/outputs
            description: Template description
        """
        self.template = template
        self.input_variables = input_variables
        self.examples = examples or []
        self.description = description

    def format(self, **kwargs) -> str:
        """
        Format template with variables.

        Args:
            **kwargs: Variable values

        Returns:
            str: Formatted prompt

        Raises:
            ValueError: If missing required variables
        """
        # Check all required variables are provided
        missing = [v for v in self.input_variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Format template
        try:
            formatted = self.template.format(**kwargs)
            return formatted
        except KeyError as e:
            raise ValueError(f"Invalid template variable: {e}")

    def add_examples(self, examples: List[Dict[str, str]]) -> None:
        """
        Add examples to template.

        Args:
            examples: List of example dicts
        """
        self.examples.extend(examples)

    def get_examples_text(self) -> str:
        """
        Get formatted examples as text.

        Returns:
            str: Formatted examples
        """
        if not self.examples:
            return ""

        text = "\nExamples:\n"
        for i, example in enumerate(self.examples, 1):
            text += f"\nExample {i}:\n"
            for key, value in example.items():
                text += f"  {key}: {value}\n"

        return text

    def get_info(self) -> Dict[str, Any]:
        """
        Get template information.

        Returns:
            Dict[str, Any]: Template metadata
        """
        return {
            "description": self.description,
            "input_variables": self.input_variables,
            "example_count": len(self.examples),
            "template_length": len(self.template),
        }


class ChainedPromptTemplate:
    """
    Chains multiple templates together for complex prompts.

    Useful for building prompts step-by-step with context.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize chained template.

        Args:
            name: Name of the prompt chain
            description: Optional description
        """
        self.name = name
        self.description = description
        self._templates: List[PromptTemplate] = []
        self._separators: List[str] = []

    def add_template(
        self, template: PromptTemplate, separator: str = "\n\n"
    ) -> None:
        """
        Add template to chain.

        Args:
            template: Template to add
            separator: Separator between templates
        """
        self._templates.append(template)
        self._separators.append(separator)

    def format(self, **kwargs) -> str:
        """
        Format all templates in chain.

        Args:
            **kwargs: Variables for all templates

        Returns:
            str: Combined formatted prompt
        """
        if not self._templates:
            return ""

        formatted_parts = []
        for template in self._templates:
            try:
                formatted = template.format(**kwargs)
                formatted_parts.append(formatted)
            except ValueError as e:
                logger.warning(f"Error formatting template: {e}")
                continue

        # Join with separators
        result = formatted_parts[0] if formatted_parts else ""
        for i, part in enumerate(formatted_parts[1:], 1):
            separator = self._separators[i - 1] if i - 1 < len(self._separators) else "\n\n"
            result += separator + part

        return result

    def get_all_variables(self) -> List[str]:
        """
        Get all variables from all templates.

        Returns:
            List[str]: All required variables
        """
        variables = set()
        for template in self._templates:
            variables.update(template.input_variables)
        return list(variables)
