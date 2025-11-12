"""
Pydantic schemas for Invoice model.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.invoice import InvoiceStatus


class InvoiceBase(BaseModel):
    """Base invoice schema with common fields."""
    booking_id: int
    customer_id: int
    amount: float = Field(..., gt=0)
    tax_amount: float = Field(default=0.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    total_amount: float = Field(..., gt=0)
    payment_terms: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    pass


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    amount: Optional[float] = Field(None, gt=0)
    tax_amount: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, gt=0)
    payment_terms: Optional[str] = Field(None, max_length=255)
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None


class Invoice(InvoiceBase):
    """Schema for invoice response."""
    id: int
    invoice_number: str
    status: InvoiceStatus
    issued_date: datetime
    due_date: datetime
    paid_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list."""
    items: list[Invoice]
    total: int
    page: int
    page_size: int
    total_pages: int
