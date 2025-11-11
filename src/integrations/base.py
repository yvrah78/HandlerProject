"""
Base integration class for Project Handler.
Provides common functionality for all external API integrations.
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, TypeVar
from functools import wraps

from src.core.logging import get_logger
from src.core.exceptions import IntegrationError, ConfigurationError

T = TypeVar('T')


class BaseIntegration(ABC):
    """
    Base class for all external API integrations.

    Provides:
    - Logging
    - Retry logic for transient failures
    - Error handling
    - Configuration validation
    """

    def __init__(self, integration_name: str):
        """
        Initialize base integration.

        Args:
            integration_name: Name of the integration (e.g., "twilio", "stripe")
        """
        self.integration_name = integration_name
        self.logger = get_logger(f"{__name__}.{integration_name}")

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate that all required configuration is present.

        Raises:
            ConfigurationError: If required configuration is missing
        """
        pass

    def _check_config_value(self, value: str, name: str) -> None:
        """
        Check that a configuration value is set.

        Args:
            value: Configuration value to check
            name: Name of the configuration parameter

        Raises:
            ConfigurationError: If value is empty or missing
        """
        if not value or value.strip() == "":
            raise ConfigurationError(
                f"Missing required configuration: {name}",
                details={
                    "integration": self.integration_name,
                    "parameter": name
                }
            )

    async def _retry_on_failure(
        self,
        func: Callable[..., T],
        *args,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        **kwargs
    ) -> T:
        """
        Retry a function call on failure with exponential backoff.

        Args:
            func: Function to retry
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for delay after each retry
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function call

        Raises:
            IntegrationError: If all retries are exhausted
        """
        last_exception = None
        delay = initial_delay

        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # Don't retry on authentication/configuration errors
                if isinstance(e, (ConfigurationError, PermissionError)):
                    raise IntegrationError(
                        f"Configuration error in {self.integration_name}: {str(e)}",
                        integration_name=self.integration_name,
                        details={"error": str(e), "attempt": attempt + 1}
                    )

                if attempt < max_retries:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {self.integration_name}: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                else:
                    self.logger.error(
                        f"All {max_retries + 1} attempts failed for {self.integration_name}: {str(e)}"
                    )

        # If we get here, all retries failed
        raise IntegrationError(
            f"Failed to complete operation in {self.integration_name} after {max_retries + 1} attempts: {str(last_exception)}",
            integration_name=self.integration_name,
            details={
                "max_retries": max_retries,
                "last_error": str(last_exception),
                "error_type": type(last_exception).__name__
            }
        )

    def _sanitize_phone_number(self, phone: str) -> str:
        """
        Sanitize and validate phone number format.

        Args:
            phone: Phone number to sanitize

        Returns:
            Sanitized phone number

        Raises:
            IntegrationError: If phone number is invalid
        """
        if not phone:
            raise IntegrationError(
                "Phone number is required",
                integration_name=self.integration_name
            )

        # Remove common formatting characters
        sanitized = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Basic validation
        if not sanitized.startswith('+'):
            # Assume US number if no country code
            if len(sanitized) == 10:
                sanitized = f"+1{sanitized}"
            else:
                raise IntegrationError(
                    f"Invalid phone number format: {phone}. Must include country code or be a 10-digit US number.",
                    integration_name=self.integration_name
                )

        return sanitized

    def _sanitize_email(self, email: str) -> str:
        """
        Sanitize and validate email address.

        Args:
            email: Email address to sanitize

        Returns:
            Sanitized email address

        Raises:
            IntegrationError: If email is invalid
        """
        if not email:
            raise IntegrationError(
                "Email address is required",
                integration_name=self.integration_name
            )

        email = email.strip().lower()

        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            raise IntegrationError(
                f"Invalid email address format: {email}",
                integration_name=self.integration_name
            )

        return email

    def _format_currency_amount(self, amount: float, currency: str = "usd") -> int:
        """
        Format currency amount for APIs that expect smallest unit (cents, etc.).

        Args:
            amount: Amount in major currency units (dollars, euros, etc.)
            currency: Currency code

        Returns:
            Amount in smallest currency unit (cents, cents, etc.)
        """
        # Most currencies use 2 decimal places
        # Some currencies like JPY use 0 decimal places
        zero_decimal_currencies = ['jpy', 'krw', 'vnd', 'clp']

        if currency.lower() in zero_decimal_currencies:
            return int(amount)
        else:
            return int(amount * 100)

    def _log_api_call(
        self,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> None:
        """
        Log an API call for monitoring and debugging.

        Args:
            operation: Name of the operation being performed
            details: Additional details about the operation
            success: Whether the operation was successful
        """
        log_data = {
            "integration": self.integration_name,
            "operation": operation,
            "success": success,
        }

        if details:
            # Remove sensitive data from logs
            safe_details = {
                k: v for k, v in details.items()
                if k not in ['api_key', 'token', 'secret', 'password', 'auth']
            }
            log_data.update(safe_details)

        if success:
            self.logger.info(f"API call successful: {operation}", extra=log_data)
        else:
            self.logger.error(f"API call failed: {operation}", extra=log_data)
