"""
Base LangChain tools shared across all agents.

These tools provide common functionality like database access,
validation, and logging that any agent might need.
"""
from typing import Optional, Type, Any, Dict
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from src.core.database import get_db
from src.core.logging import get_logger


logger = get_logger(__name__)


class DatabaseQueryInput(BaseModel):
    """Input schema for database query tool."""
    model_name: str = Field(description="Name of the model to query (e.g., 'Customer', 'Booking')")
    filter_by: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter criteria as key-value pairs (e.g., {'id': 123})"
    )
    limit: int = Field(default=10, description="Maximum number of results to return")


class DatabaseQueryTool(BaseTool):
    """
    Tool for querying the database.

    Allows agents to fetch data from the database using model names
    and filter criteria.
    """
    name = "database_query"
    description = """
    Query the database for records. Use this when you need to fetch
    customer data, bookings, invoices, or any other stored information.
    Input should be the model name and optional filter criteria.
    """
    args_schema: Type[BaseModel] = DatabaseQueryInput

    def _run(
        self,
        model_name: str,
        filter_by: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Execute database query.

        Args:
            model_name: Name of the model to query
            filter_by: Filter criteria
            limit: Maximum results
            run_manager: Callback manager

        Returns:
            str: JSON string of query results
        """
        try:
            # Import models dynamically
            from src.models import (
                Customer, Booking, Invoice, Payment,
                Quote, Route, Service, Vehicle, Driver
            )

            model_map = {
                "Customer": Customer,
                "Booking": Booking,
                "Invoice": Invoice,
                "Payment": Payment,
                "Quote": Quote,
                "Route": Route,
                "Service": Service,
                "Vehicle": Vehicle,
                "Driver": Driver,
            }

            if model_name not in model_map:
                return f"Error: Unknown model '{model_name}'. Available models: {list(model_map.keys())}"

            model_class = model_map[model_name]

            # Build query
            db = next(get_db())
            query = db.query(model_class)

            if filter_by:
                for key, value in filter_by.items():
                    if hasattr(model_class, key):
                        query = query.filter(getattr(model_class, key) == value)

            results = query.limit(limit).all()

            # Convert to dict representation
            result_dicts = [
                {
                    column.name: getattr(result, column.name)
                    for column in result.__table__.columns
                }
                for result in results
            ]

            import json
            return json.dumps(result_dicts, default=str, indent=2)

        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return f"Error executing query: {str(e)}"

    async def _arun(
        self,
        model_name: str,
        filter_by: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(model_name, filter_by, limit, run_manager)


class ValidationInput(BaseModel):
    """Input schema for validation tool."""
    data_type: str = Field(description="Type of data to validate (e.g., 'email', 'phone', 'amount')")
    value: str = Field(description="Value to validate")


class ValidationTool(BaseTool):
    """
    Tool for validating data.

    Provides validation for common data types like emails, phone numbers,
    amounts, dates, etc.
    """
    name = "validate_data"
    description = """
    Validate data before processing. Use this to check if emails are valid,
    phone numbers are properly formatted, amounts are positive, etc.
    """
    args_schema: Type[BaseModel] = ValidationInput

    def _run(
        self,
        data_type: str,
        value: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Validate data.

        Args:
            data_type: Type of validation
            value: Value to validate
            run_manager: Callback manager

        Returns:
            str: Validation result
        """
        import re

        validators = {
            "email": lambda v: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v)),
            "phone": lambda v: bool(re.match(r'^\+?1?\d{9,15}$', v.replace('-', '').replace(' ', ''))),
            "amount": lambda v: self._validate_amount(v),
            "date": lambda v: self._validate_date(v),
        }

        if data_type not in validators:
            return f"Error: Unknown validation type '{data_type}'. Available: {list(validators.keys())}"

        try:
            is_valid = validators[data_type](value)
            return f"{{'valid': {str(is_valid).lower()}, 'value': '{value}', 'type': '{data_type}'}}"
        except Exception as e:
            return f"{{'valid': false, 'error': '{str(e)}'}}"

    def _validate_amount(self, value: str) -> bool:
        """Validate monetary amount."""
        try:
            amount = float(value.replace('$', '').replace(',', ''))
            return amount >= 0
        except ValueError:
            return False

    def _validate_date(self, value: str) -> bool:
        """Validate date string."""
        from dateutil import parser
        try:
            parser.parse(value)
            return True
        except (ValueError, TypeError):
            return False

    async def _arun(
        self,
        data_type: str,
        value: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(data_type, value, run_manager)


class LoggingInput(BaseModel):
    """Input schema for logging tool."""
    level: str = Field(description="Log level: 'info', 'warning', 'error'")
    message: str = Field(description="Message to log")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class LoggingTool(BaseTool):
    """
    Tool for structured logging.

    Allows agents to log important events, warnings, and errors
    with proper context for debugging and analytics.
    """
    name = "log_event"
    description = """
    Log important events, warnings, or errors. Use this to record
    significant actions or issues that need attention.
    """
    args_schema: Type[BaseModel] = LoggingInput

    def _run(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Log event.

        Args:
            level: Log level
            message: Log message
            context: Additional context
            run_manager: Callback manager

        Returns:
            str: Confirmation
        """
        log_fn = {
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
        }.get(level.lower(), logger.info)

        log_fn(message, extra=context or {})

        return f"{{'logged': true, 'level': '{level}', 'message': '{message}'}}"

    async def _arun(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(level, message, context, run_manager)
