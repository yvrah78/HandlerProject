"""
Pydantic schemas package.
Exports all schemas for API validation.
"""
from src.schemas.customer import (
    CustomerBase, CustomerCreate, CustomerUpdate, Customer, CustomerListResponse
)
from src.schemas.booking import (
    BookingBase, BookingCreate, BookingUpdate, Booking, BookingListResponse
)

__all__ = [
    # Customer
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    "Customer",
    "CustomerListResponse",
    # Booking
    "BookingBase",
    "BookingCreate",
    "BookingUpdate",
    "Booking",
    "BookingListResponse",
]
