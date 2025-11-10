"""
Vehicle model for Project Handler.
Represents vehicles in the transportation fleet.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class VehicleType(str, enum.Enum):
    """Vehicle type enumeration."""
    VAN = "van"
    TRUCK_SMALL = "truck_small"
    TRUCK_MEDIUM = "truck_medium"
    TRUCK_LARGE = "truck_large"
    REFRIGERATED = "refrigerated"
    FLATBED = "flatbed"
    CAR = "car"
    SUV = "suv"


class VehicleStatus(str, enum.Enum):
    """Vehicle status enumeration."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class Vehicle(Base):
    """Vehicle entity model."""

    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    license_plate = Column(String(20), unique=True, index=True, nullable=False)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(50), nullable=True)

    # Type and capacity
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    capacity_kg = Column(Float, nullable=False)  # Weight capacity in kg
    capacity_m3 = Column(Float, nullable=True)   # Volume capacity in m³
    max_passengers = Column(Integer, default=2)

    # Status
    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    is_active = Column(Boolean, default=True)

    # Maintenance
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    mileage_km = Column(Float, default=0.0)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bookings = relationship("Booking", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, plate='{self.license_plate}', type='{self.vehicle_type}', status='{self.status}')>"
