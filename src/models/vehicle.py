"""
Vehicle model for Project Handler.
Represents vehicles in the transportation fleet with operating cost tracking.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, JSON
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


class FuelType(str, enum.Enum):
    """Fuel type enumeration."""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    CNG = "cng"  # Compressed Natural Gas


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

    # Operating Costs - Fuel/Energy
    fuel_type = Column(Enum(FuelType), default=FuelType.GASOLINE)
    fuel_consumption_per_100km = Column(Float, nullable=True)  # Liters per 100km (gasoline/diesel)
    electric_consumption_kwh_per_100km = Column(Float, nullable=True)  # kWh per 100km (electric)
    fuel_tank_capacity_liters = Column(Float, nullable=True)
    battery_capacity_kwh = Column(Float, nullable=True)  # For electric vehicles

    # Current fuel/electricity prices (can be updated regularly)
    current_fuel_price_per_liter = Column(Float, nullable=True)  # USD per liter
    current_electricity_price_per_kwh = Column(Float, nullable=True)  # USD per kWh

    # Maintenance costs (per kilometer)
    tire_wear_cost_per_km = Column(Float, default=0.02)  # Tire replacement cost spread over life
    brake_wear_cost_per_km = Column(Float, default=0.01)  # Brake maintenance per km
    oil_change_cost_per_km = Column(Float, default=0.01)  # Oil & filters per km
    general_maintenance_cost_per_km = Column(Float, default=0.03)  # General wear & tear

    # Depreciation
    depreciation_cost_per_km = Column(Float, default=0.15)  # Vehicle depreciation per km

    # Insurance and registration (daily cost)
    insurance_cost_per_day = Column(Float, default=10.0)  # Daily insurance cost

    # Toll pass (if vehicle has automatic toll system)
    has_toll_pass = Column(Boolean, default=False)
    toll_pass_discount_percent = Column(Float, default=0.0)  # Discount on tolls (0-100)

    # Operating cost metadata (for tracking historical data)
    operating_cost_data = Column(JSON, nullable=True)  # Store historical cost data

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bookings = relationship("Booking", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, plate='{self.license_plate}', type='{self.vehicle_type}', status='{self.status}')>"
