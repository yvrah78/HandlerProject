"""
Pydantic schemas for Customer model.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.customer import CustomerType


# Base schema with common fields
class CustomerBase(BaseModel):
    """Base customer schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    company: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    company_address: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: str = "USA"
    contact_person_name: Optional[str] = Field(None, max_length=255)
    contact_person_phone: Optional[str] = Field(None, max_length=20)
    contact_person_email: Optional[EmailStr] = None
    preferred_payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


# Schema for creating a customer
class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


# Schema for updating a customer
class CustomerUpdate(BaseModel):
    """Schema for updating a customer (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    customer_type: Optional[CustomerType] = None
    company: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    company_address: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = None
    contact_person_name: Optional[str] = Field(None, max_length=255)
    contact_person_phone: Optional[str] = Field(None, max_length=20)
    contact_person_email: Optional[EmailStr] = None
    preferred_payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


# Schema for response (includes DB fields)
class Customer(CustomerBase):
    """Schema for customer response."""
    id: int
    is_active: bool
    rating: int
    total_bookings: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# List response
class CustomerListResponse(BaseModel):
    """Schema for paginated customer list."""
    items: list[Customer]
    total: int
    page: int
    page_size: int
    total_pages: int
