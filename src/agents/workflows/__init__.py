"""
Predefined Workflows for Common Business Processes.

This module contains ready-to-use workflows for:
- Booking creation and management
- Payment processing
- Communication automation
"""
from src.agents.workflows.booking_workflow import create_booking_workflow
from src.agents.workflows.payment_workflow import create_payment_workflow
from src.agents.workflows.communication_workflow import create_communication_workflow

__all__ = [
    "create_booking_workflow",
    "create_payment_workflow",
    "create_communication_workflow",
]
