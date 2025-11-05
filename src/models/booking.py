"""
Booking model for Project Handler.
Represents transportation bookings in the system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class BookingStatus(str, enum.Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Booking(Base):
    """Booking entity model."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    origin = Column(String(500), nullable=False)
    destination = Column(String(500), nullable=False)
    pickup_datetime = Column(DateTime(timezone=True), nullable=False)
    delivery_datetime = Column(DateTime(timezone=True), nullable=True)

    cargo_description = Column(String(1000), nullable=True)
    cargo_weight = Column(Float, nullable=True)

    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships will be added when foreign keys are set up
    # customer = relationship("Customer", back_populates="bookings")

    def __repr__(self):
        return f"<Booking(id={self.id}, customer_id={self.customer_id}, status='{self.status}')>"
