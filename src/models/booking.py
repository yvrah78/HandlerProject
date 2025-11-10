"""
Booking model for Project Handler.
Represents transportation bookings in the system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, Text, Boolean
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

    # Foreign keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)

    # Booking number
    booking_number = Column(String(50), unique=True, index=True, nullable=False)

    # Location
    origin = Column(String(500), nullable=False)
    destination = Column(String(500), nullable=False)

    # Time
    pickup_datetime = Column(DateTime(timezone=True), nullable=False)
    delivery_datetime = Column(DateTime(timezone=True), nullable=True)
    actual_pickup_datetime = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_datetime = Column(DateTime(timezone=True), nullable=True)

    # Cargo details
    cargo_description = Column(String(1000), nullable=True)
    cargo_weight = Column(Float, nullable=True)
    cargo_volume = Column(Float, nullable=True)
    special_requirements = Column(Text, nullable=True)

    # Pricing (from quote)
    quoted_price = Column(Float, nullable=True)
    final_price = Column(Float, nullable=True)

    # Status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    is_paid = Column(Boolean, default=False)

    # Notes
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    vehicle = relationship("Vehicle", back_populates="bookings")
    driver = relationship("Driver", back_populates="bookings")
    quote = relationship("Quote", backref="booking", uselist=False)
    route = relationship("Route", back_populates="booking", uselist=False)
    invoices = relationship("Invoice", back_populates="booking")

    def __repr__(self):
        return f"<Booking(id={self.id}, number='{self.booking_number}', customer_id={self.customer_id}, status='{self.status}')>"
