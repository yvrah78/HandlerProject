"""
Custom exceptions for Project Handler.
Provides standardized error handling across the application.
"""
from typing import Any, Dict, Optional


class ProjectHandlerException(Exception):
    """Base exception for all Project Handler errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or "GENERAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(ProjectHandlerException):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class DatabaseError(ProjectHandlerException):
    """Raised when there's a database-related error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class ValidationError(ProjectHandlerException):
    """Raised when data validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class AgentError(ProjectHandlerException):
    """Raised when an agent encounters an error."""

    def __init__(self, message: str, agent_name: str, details: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        super().__init__(message, code="AGENT_ERROR", details=details)


class IntegrationError(ProjectHandlerException):
    """Raised when an external integration fails."""

    def __init__(
        self,
        message: str,
        integration_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.integration_name = integration_name
        super().__init__(message, code="INTEGRATION_ERROR", details=details)


class AuthenticationError(ProjectHandlerException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class AuthorizationError(ProjectHandlerException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Unauthorized access", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTHZ_ERROR", details=details)


class NotFoundError(ProjectHandlerException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, code="NOT_FOUND", details=details)
