"""
Pydantic schemas for Vehicle model.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.vehicle import VehicleType, FuelType, VehicleStatus


class VehicleBase(BaseModel):
    """Base vehicle schema with common fields."""
    license_plate: str = Field(..., min_length=1, max_length=20)
    brand: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    year: int = Field(..., ge=1900, le=2100)
    color: Optional[str] = Field(None, max_length=50)
    vehicle_type: VehicleType
    capacity_kg: float = Field(..., gt=0)
    capacity_m3: Optional[float] = Field(None, gt=0)
    max_passengers: int = Field(default=2, ge=1)
    fuel_type: FuelType = FuelType.GASOLINE
    fuel_consumption_per_100km: Optional[float] = Field(None, gt=0)
    electric_consumption_kwh_per_100km: Optional[float] = Field(None, gt=0)
    fuel_tank_capacity_liters: Optional[float] = Field(None, gt=0)
    battery_capacity_kwh: Optional[float] = Field(None, gt=0)
    current_fuel_price_per_liter: Optional[float] = Field(None, gt=0)
    current_electricity_price_per_kwh: Optional[float] = Field(None, gt=0)
    tire_wear_cost_per_km: float = Field(default=0.02, ge=0)
    brake_wear_cost_per_km: float = Field(default=0.01, ge=0)
    oil_change_cost_per_km: float = Field(default=0.01, ge=0)
    general_maintenance_cost_per_km: float = Field(default=0.03, ge=0)
    depreciation_cost_per_km: float = Field(default=0.15, ge=0)
    insurance_cost_per_day: float = Field(default=10.0, ge=0)
    has_toll_pass: bool = Field(default=False)
    toll_pass_discount_percent: float = Field(default=0.0, ge=0, le=100)
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    """Schema for creating a vehicle."""
    pass


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    license_plate: Optional[str] = Field(None, min_length=1, max_length=20)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    color: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[VehicleType] = None
    capacity_kg: Optional[float] = Field(None, gt=0)
    capacity_m3: Optional[float] = Field(None, gt=0)
    max_passengers: Optional[int] = Field(None, ge=1)
    status: Optional[VehicleStatus] = None
    is_active: Optional[bool] = None
    mileage_km: Optional[float] = Field(None, ge=0)
    fuel_type: Optional[FuelType] = None
    fuel_consumption_per_100km: Optional[float] = Field(None, gt=0)
    electric_consumption_kwh_per_100km: Optional[float] = Field(None, gt=0)
    fuel_tank_capacity_liters: Optional[float] = Field(None, gt=0)
    battery_capacity_kwh: Optional[float] = Field(None, gt=0)
    current_fuel_price_per_liter: Optional[float] = Field(None, gt=0)
    current_electricity_price_per_kwh: Optional[float] = Field(None, gt=0)
    tire_wear_cost_per_km: Optional[float] = Field(None, ge=0)
    brake_wear_cost_per_km: Optional[float] = Field(None, ge=0)
    oil_change_cost_per_km: Optional[float] = Field(None, ge=0)
    general_maintenance_cost_per_km: Optional[float] = Field(None, ge=0)
    depreciation_cost_per_km: Optional[float] = Field(None, ge=0)
    insurance_cost_per_day: Optional[float] = Field(None, ge=0)
    has_toll_pass: Optional[bool] = None
    toll_pass_discount_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class Vehicle(VehicleBase):
    """Schema for vehicle response."""
    id: int
    status: VehicleStatus
    is_active: bool
    mileage_km: float
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VehicleListResponse(BaseModel):
    """Schema for paginated vehicle list."""
    items: list[Vehicle]
    total: int
    page: int
    page_size: int
    total_pages: int
