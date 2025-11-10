"""
Pydantic schemas for Booking model.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.booking import BookingStatus


# Base schema
class BookingBase(BaseModel):
    """Base booking schema."""
    customer_id: int
    service_id: Optional[int] = None
    origin: str = Field(..., min_length=1, max_length=500)
    destination: str = Field(..., min_length=1, max_length=500)
    pickup_datetime: datetime
    delivery_datetime: Optional[datetime] = None
    cargo_description: Optional[str] = Field(None, max_length=1000)
    cargo_weight: Optional[float] = Field(None, gt=0)
    cargo_volume: Optional[float] = Field(None, gt=0)
    special_requirements: Optional[str] = None
    notes: Optional[str] = None


# Create schema
class BookingCreate(BookingBase):
    """Schema for creating a booking."""
    pass


# Update schema
class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    service_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    origin: Optional[str] = Field(None, min_length=1, max_length=500)
    destination: Optional[str] = Field(None, min_length=1, max_length=500)
    pickup_datetime: Optional[datetime] = None
    delivery_datetime: Optional[datetime] = None
    actual_pickup_datetime: Optional[datetime] = None
    actual_delivery_datetime: Optional[datetime] = None
    cargo_description: Optional[str] = Field(None, max_length=1000)
    cargo_weight: Optional[float] = Field(None, gt=0)
    cargo_volume: Optional[float] = Field(None, gt=0)
    special_requirements: Optional[str] = None
    quoted_price: Optional[float] = Field(None, ge=0)
    final_price: Optional[float] = Field(None, ge=0)
    status: Optional[BookingStatus] = None
    is_paid: Optional[bool] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


# Response schema
class Booking(BookingBase):
    """Schema for booking response."""
    id: int
    booking_number: str
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    quote_id: Optional[int] = None
    actual_pickup_datetime: Optional[datetime] = None
    actual_delivery_datetime: Optional[datetime] = None
    quoted_price: Optional[float] = None
    final_price: Optional[float] = None
    status: BookingStatus
    is_paid: bool
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# List response
class BookingListResponse(BaseModel):
    """Schema for paginated booking list."""
    items: list[Booking]
    total: int
    page: int
    page_size: int
    total_pages: int
