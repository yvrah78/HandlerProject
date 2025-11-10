"""
Invoice model for Project Handler.
Represents financial invoices in the system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Invoice entity model."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Invoice identification
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)

    # Amounts
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

    # Payment terms
    payment_terms = Column(String(255), nullable=True)  # e.g., "Net 30"

    # Status
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # Dates
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    sent_date = Column(DateTime(timezone=True), nullable=True)

    # Stripe integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    booking = relationship("Booking", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_number='{self.invoice_number}', total={self.total_amount}, status='{self.status}')>"
