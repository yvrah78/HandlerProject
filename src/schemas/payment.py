"""
Pydantic schemas for Payment model.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.payment import PaymentMethod, PaymentStatus


class PaymentBase(BaseModel):
    """Base payment schema with common fields."""
    invoice_id: int
    customer_id: int
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: PaymentMethod
    card_last4: Optional[str] = Field(None, max_length=4)
    card_brand: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""
    pass


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    card_last4: Optional[str] = Field(None, max_length=4)
    card_brand: Optional[str] = Field(None, max_length=50)
    refund_amount: Optional[float] = Field(None, ge=0)
    refund_reason: Optional[str] = None
    notes: Optional[str] = None


class PaymentProcessRequest(BaseModel):
    """Schema for processing a payment via Stripe."""
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: PaymentMethod
    idempotency_key: Optional[str] = None


class PaymentRefundRequest(BaseModel):
    """Schema for refunding a payment."""
    refund_amount: Optional[float] = Field(None, gt=0)
    refund_reason: Optional[str] = None


class Payment(PaymentBase):
    """Schema for payment response."""
    id: int
    transaction_id: str
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    refund_amount: float
    refund_date: Optional[datetime] = None
    stripe_payment_intent_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list."""
    items: list[Payment]
    total: int
    page: int
    page_size: int
    total_pages: int
