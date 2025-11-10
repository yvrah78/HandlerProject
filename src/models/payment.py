"""
Payment model for Project Handler.
Represents payment transactions in the system.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(Base):
    """Payment entity model."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Payment identification
    transaction_id = Column(String(255), unique=True, index=True, nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True)  # For Stripe

    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Method and status
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Card details (last 4 digits only for security)
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(50), nullable=True)  # visa, mastercard, etc.

    # Dates
    payment_date = Column(DateTime(timezone=True), nullable=True)

    # Refund
    refund_amount = Column(Float, default=0.0)
    refund_date = Column(DateTime(timezone=True), nullable=True)
    refund_reason = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)  # For failed payments

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("Customer", backref="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, transaction_id='{self.transaction_id}', amount={self.amount}, status='{self.status}')>"
