"""
Quote model for Project Handler.
Represents price quotes for transportation services.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class QuoteStatus(str, enum.Enum):
    """Quote status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Quote(Base):
    """Quote entity model."""

    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)

    # Quote identification
    quote_number = Column(String(50), unique=True, index=True, nullable=False)

    # Route info
    origin = Column(String(500), nullable=False)
    destination = Column(String(500), nullable=False)
    distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)

    # Pricing breakdown
    base_price = Column(Float, nullable=False, default=0.0)
    distance_price = Column(Float, nullable=False, default=0.0)
    time_price = Column(Float, nullable=False, default=0.0)
    additional_fees = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False)

    # Pricing details (JSON)
    pricing_details = Column(JSON, nullable=True)

    # Service details
    cargo_description = Column(String(1000), nullable=True)
    special_requirements = Column(Text, nullable=True)

    # Status
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)

    # Validity
    valid_until = Column(DateTime(timezone=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="quotes")
    service = relationship("Service", backref="quotes")

    def __repr__(self):
        return f"<Quote(id={self.id}, number='{self.quote_number}', total={self.total_amount}, status='{self.status}')>"
