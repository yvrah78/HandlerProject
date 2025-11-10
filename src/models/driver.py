"""
Driver model for Project Handler.
Represents drivers in the transportation system.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class DriverStatus(str, enum.Enum):
    """Driver status enumeration."""
    AVAILABLE = "available"
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    ON_BREAK = "on_break"
    UNAVAILABLE = "unavailable"


class Driver(Base):
    """Driver entity model."""

    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)

    # Personal info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=True)

    # License info
    license_number = Column(String(50), unique=True, index=True, nullable=False)
    license_type = Column(String(20), nullable=False)  # e.g., "A", "B", "C", "E"
    license_expiry_date = Column(Date, nullable=False)

    # Employment
    hire_date = Column(Date, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    # Status
    status = Column(Enum(DriverStatus), default=DriverStatus.AVAILABLE)
    is_active = Column(Boolean, default=True)

    # Performance
    rating = Column(Integer, default=5)  # 1-5 stars
    total_trips = Column(Integer, default=0)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bookings = relationship("Booking", back_populates="driver")

    @property
    def full_name(self):
        """Get driver's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Driver(id={self.id}, name='{self.full_name}', license='{self.license_number}', status='{self.status}')>"
