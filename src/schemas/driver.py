"""
Pydantic schemas for Driver model.
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime, date
from src.models.driver import DriverStatus


class DriverBase(BaseModel):
    """Base driver schema with common fields."""
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    date_of_birth: Optional[date] = None
    license_number: str = Field(..., max_length=50)
    license_type: str = Field(..., max_length=20)
    license_expiry_date: date
    hire_date: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    """Schema for creating a driver."""
    pass


class DriverUpdate(BaseModel):
    """Schema for updating a driver."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    date_of_birth: Optional[date] = None
    license_number: Optional[str] = Field(None, max_length=50)
    license_type: Optional[str] = Field(None, max_length=20)
    license_expiry_date: Optional[date] = None
    hire_date: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    status: Optional[DriverStatus] = None
    is_active: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class Driver(DriverBase):
    """Schema for driver response."""
    id: int
    status: DriverStatus
    is_active: bool
    rating: int
    total_trips: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DriverListResponse(BaseModel):
    """Schema for paginated driver list."""
    items: list[Driver]
    total: int
    page: int
    page_size: int
    total_pages: int
