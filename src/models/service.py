"""
Service model for Project Handler.
Represents different types of transportation services offered.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class ServiceType(str, enum.Enum):
    """Service type enumeration."""
    LOCAL = "local"
    LONG_DISTANCE = "long_distance"
    AIRPORT = "airport"
    CORPORATE = "corporate"
    EXPRESS = "express"
    SCHEDULED = "scheduled"


class Service(Base):
    """Service entity model."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    service_type = Column(Enum(ServiceType), nullable=False)
    description = Column(Text, nullable=True)

    # Pricing
    base_price = Column(Float, nullable=False, default=0.0)
    price_per_km = Column(Float, nullable=False, default=0.0)
    price_per_minute = Column(Float, nullable=False, default=0.0)
    minimum_charge = Column(Float, nullable=False, default=0.0)

    # Availability
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bookings = relationship("Booking", back_populates="service")

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}', type='{self.service_type}')>"
