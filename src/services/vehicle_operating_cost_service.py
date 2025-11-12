"""
Vehicle Operating Cost Service for Project Handler.
Calculates comprehensive operating costs for vehicles including fuel, maintenance, tolls, etc.
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.core.exceptions import ValidationError
from src.models.vehicle import Vehicle, FuelType

logger = get_logger(__name__)


class VehicleOperatingCostService:
    """
    Service for calculating vehicle operating costs.

    Calculates:
    - Fuel/electricity consumption costs
    - Maintenance costs (tires, brakes, oil, general)
    - Depreciation
    - Insurance allocation
    - Toll costs (with discounts if applicable)
    - Traffic delay costs (additional fuel from idling)
    """

    # Default fuel prices (USD) - can be overridden by vehicle-specific prices
    DEFAULT_GASOLINE_PRICE_PER_LITER = 1.20
    DEFAULT_DIESEL_PRICE_PER_LITER = 1.30
    DEFAULT_ELECTRICITY_PRICE_PER_KWH = 0.15
    DEFAULT_CNG_PRICE_PER_LITER = 0.90

    # Traffic multipliers for fuel consumption
    TRAFFIC_LIGHT = 1.1  # 10% more fuel in light traffic
    TRAFFIC_MEDIUM = 1.25  # 25% more fuel in medium traffic
    TRAFFIC_HEAVY = 1.5  # 50% more fuel in heavy traffic

    def __init__(self, db: Session):
        """
        Initialize vehicle operating cost service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logger
        self.logger.info("VehicleOperatingCostService initialized")

    def calculate_operating_cost(
        self,
        vehicle_id: int,
        distance_km: float,
        duration_minutes: int,
        toll_cost: float = 0.0,
        traffic_level: str = "normal"  # normal, light, medium, heavy
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive operating cost for a vehicle trip.

        Args:
            vehicle_id: Vehicle ID
            distance_km: Distance in kilometers
            duration_minutes: Trip duration in minutes
            toll_cost: Total toll cost from route (USD)
            traffic_level: Traffic level (normal, light, medium, heavy)

        Returns:
            dict: Detailed operating cost breakdown

        Raises:
            ValidationError: If vehicle not found or invalid data
        """
        # Get vehicle from database
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise ValidationError(f"Vehicle with ID {vehicle_id} not found")

        distance = Decimal(str(distance_km))
        duration = Decimal(str(duration_minutes))

        # 1. Calculate fuel/electricity cost
        fuel_cost_result = self._calculate_fuel_cost(
            vehicle, distance_km, traffic_level
        )

        # 2. Calculate maintenance costs
        maintenance_cost_result = self._calculate_maintenance_cost(
            vehicle, distance_km
        )

        # 3. Calculate depreciation
        depreciation_cost = float(Decimal(str(vehicle.depreciation_cost_per_km)) * distance)

        # 4. Calculate insurance allocation (based on trip duration)
        # Allocate daily insurance cost proportionally to trip duration
        insurance_cost = self._calculate_insurance_allocation(
            vehicle, duration_minutes
        )

        # 5. Apply toll costs (with discount if applicable)
        toll_cost_after_discount = toll_cost
        if vehicle.has_toll_pass and vehicle.toll_pass_discount_percent > 0:
            discount = toll_cost * (vehicle.toll_pass_discount_percent / 100)
            toll_cost_after_discount = toll_cost - discount
        else:
            discount = 0.0

        # 6. Calculate total operating cost
        total_operating_cost = (
            fuel_cost_result["total_fuel_cost"] +
            maintenance_cost_result["total_maintenance_cost"] +
            depreciation_cost +
            insurance_cost +
            toll_cost_after_discount
        )

        # 7. Calculate cost per kilometer
        cost_per_km = total_operating_cost / distance_km if distance_km > 0 else 0

        self.logger.info(
            f"Operating cost calculated for vehicle {vehicle_id}: "
            f"${total_operating_cost:.2f} for {distance_km}km"
        )

        return {
            # Vehicle info
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle.vehicle_type.value,
            "fuel_type": vehicle.fuel_type.value,
            "license_plate": vehicle.license_plate,

            # Distance and duration
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "traffic_level": traffic_level,

            # Fuel/electricity costs
            "fuel_cost": fuel_cost_result["total_fuel_cost"],
            "fuel_breakdown": fuel_cost_result,

            # Maintenance costs
            "maintenance_cost": maintenance_cost_result["total_maintenance_cost"],
            "maintenance_breakdown": maintenance_cost_result,

            # Other costs
            "depreciation_cost": depreciation_cost,
            "insurance_cost": insurance_cost,
            "toll_cost_original": toll_cost,
            "toll_cost_after_discount": toll_cost_after_discount,
            "toll_discount": toll_cost - toll_cost_after_discount,

            # Totals
            "total_operating_cost": total_operating_cost,
            "cost_per_km": cost_per_km,
            "currency": "USD"
        }

    def _calculate_fuel_cost(
        self,
        vehicle: Vehicle,
        distance_km: float,
        traffic_level: str
    ) -> Dict[str, float]:
        """
        Calculate fuel or electricity cost.

        Args:
            vehicle: Vehicle object
            distance_km: Distance in kilometers
            traffic_level: Traffic level

        Returns:
            dict: Fuel cost breakdown
        """
        # Get traffic multiplier
        traffic_multiplier = {
            "normal": 1.0,
            "light": self.TRAFFIC_LIGHT,
            "medium": self.TRAFFIC_MEDIUM,
            "heavy": self.TRAFFIC_HEAVY
        }.get(traffic_level.lower(), 1.0)

        if vehicle.fuel_type in [FuelType.GASOLINE, FuelType.DIESEL, FuelType.CNG]:
            # Combustion engine
            consumption_per_100km = vehicle.fuel_consumption_per_100km or 0.0

            # Apply traffic multiplier
            actual_consumption_per_100km = consumption_per_100km * traffic_multiplier

            # Calculate fuel needed
            fuel_needed_liters = (distance_km / 100) * actual_consumption_per_100km

            # Get fuel price
            if vehicle.current_fuel_price_per_liter:
                fuel_price = vehicle.current_fuel_price_per_liter
            else:
                fuel_price = {
                    FuelType.GASOLINE: self.DEFAULT_GASOLINE_PRICE_PER_LITER,
                    FuelType.DIESEL: self.DEFAULT_DIESEL_PRICE_PER_LITER,
                    FuelType.CNG: self.DEFAULT_CNG_PRICE_PER_LITER
                }.get(vehicle.fuel_type, self.DEFAULT_GASOLINE_PRICE_PER_LITER)

            total_fuel_cost = fuel_needed_liters * fuel_price

            return {
                "consumption_per_100km": consumption_per_100km,
                "traffic_multiplier": traffic_multiplier,
                "actual_consumption_per_100km": actual_consumption_per_100km,
                "fuel_needed_liters": fuel_needed_liters,
                "fuel_price_per_liter": fuel_price,
                "total_fuel_cost": total_fuel_cost,
                "type": "combustion"
            }

        elif vehicle.fuel_type == FuelType.ELECTRIC:
            # Electric vehicle
            consumption_per_100km = vehicle.electric_consumption_kwh_per_100km or 0.0

            # Traffic has less impact on electric vehicles (regenerative braking)
            actual_consumption_per_100km = consumption_per_100km * min(traffic_multiplier, 1.2)

            # Calculate electricity needed
            electricity_needed_kwh = (distance_km / 100) * actual_consumption_per_100km

            # Get electricity price
            electricity_price = vehicle.current_electricity_price_per_kwh or self.DEFAULT_ELECTRICITY_PRICE_PER_KWH

            total_fuel_cost = electricity_needed_kwh * electricity_price

            return {
                "consumption_per_100km": consumption_per_100km,
                "traffic_multiplier": min(traffic_multiplier, 1.2),
                "actual_consumption_per_100km": actual_consumption_per_100km,
                "electricity_needed_kwh": electricity_needed_kwh,
                "electricity_price_per_kwh": electricity_price,
                "total_fuel_cost": total_fuel_cost,
                "type": "electric"
            }

        elif vehicle.fuel_type == FuelType.HYBRID:
            # Hybrid: estimate 70% electric, 30% combustion in city
            # Adjust based on traffic (more traffic = more electric mode)
            electric_ratio = 0.7 if traffic_multiplier > 1.1 else 0.5

            # Calculate electric part
            electric_consumption = (vehicle.electric_consumption_kwh_per_100km or 0.0) * electric_ratio
            electric_kwh = (distance_km / 100) * electric_consumption
            electric_price = vehicle.current_electricity_price_per_kwh or self.DEFAULT_ELECTRICITY_PRICE_PER_KWH
            electric_cost = electric_kwh * electric_price

            # Calculate combustion part
            combustion_consumption = (vehicle.fuel_consumption_per_100km or 0.0) * (1 - electric_ratio)
            fuel_liters = (distance_km / 100) * combustion_consumption * traffic_multiplier
            fuel_price = vehicle.current_fuel_price_per_liter or self.DEFAULT_GASOLINE_PRICE_PER_LITER
            fuel_cost = fuel_liters * fuel_price

            total_fuel_cost = electric_cost + fuel_cost

            return {
                "electric_ratio": electric_ratio,
                "electric_kwh": electric_kwh,
                "electric_cost": electric_cost,
                "fuel_liters": fuel_liters,
                "fuel_cost": fuel_cost,
                "total_fuel_cost": total_fuel_cost,
                "type": "hybrid"
            }

        # Default case (no fuel data)
        return {
            "total_fuel_cost": 0.0,
            "type": "unknown"
        }

    def _calculate_maintenance_cost(
        self,
        vehicle: Vehicle,
        distance_km: float
    ) -> Dict[str, float]:
        """
        Calculate maintenance costs.

        Args:
            vehicle: Vehicle object
            distance_km: Distance in kilometers

        Returns:
            dict: Maintenance cost breakdown
        """
        tire_cost = vehicle.tire_wear_cost_per_km * distance_km
        brake_cost = vehicle.brake_wear_cost_per_km * distance_km
        oil_cost = vehicle.oil_change_cost_per_km * distance_km
        general_cost = vehicle.general_maintenance_cost_per_km * distance_km

        total = tire_cost + brake_cost + oil_cost + general_cost

        return {
            "tire_wear_cost": tire_cost,
            "brake_wear_cost": brake_cost,
            "oil_change_cost": oil_cost,
            "general_maintenance_cost": general_cost,
            "total_maintenance_cost": total
        }

    def _calculate_insurance_allocation(
        self,
        vehicle: Vehicle,
        duration_minutes: int
    ) -> float:
        """
        Calculate insurance cost allocation for trip.

        Allocates daily insurance cost proportionally to trip duration.

        Args:
            vehicle: Vehicle object
            duration_minutes: Trip duration in minutes

        Returns:
            float: Insurance cost for this trip
        """
        # Minutes in a day
        minutes_per_day = 24 * 60

        # Proportional insurance cost
        insurance_cost = (vehicle.insurance_cost_per_day / minutes_per_day) * duration_minutes

        return insurance_cost

    def get_vehicle_efficiency_score(self, vehicle_id: int) -> Dict[str, Any]:
        """
        Get efficiency score for a vehicle based on operating costs.

        Args:
            vehicle_id: Vehicle ID

        Returns:
            dict: Efficiency metrics
        """
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise ValidationError(f"Vehicle with ID {vehicle_id} not found")

        # Calculate cost per km
        total_cost_per_km = (
            vehicle.depreciation_cost_per_km +
            vehicle.tire_wear_cost_per_km +
            vehicle.brake_wear_cost_per_km +
            vehicle.oil_change_cost_per_km +
            vehicle.general_maintenance_cost_per_km
        )

        # Add estimated fuel cost per km (assuming average consumption)
        if vehicle.fuel_type in [FuelType.GASOLINE, FuelType.DIESEL]:
            consumption = vehicle.fuel_consumption_per_100km or 10.0
            fuel_price = vehicle.current_fuel_price_per_liter or self.DEFAULT_GASOLINE_PRICE_PER_LITER
            fuel_cost_per_km = (consumption / 100) * fuel_price
        elif vehicle.fuel_type == FuelType.ELECTRIC:
            consumption = vehicle.electric_consumption_kwh_per_100km or 20.0
            electricity_price = vehicle.current_electricity_price_per_kwh or self.DEFAULT_ELECTRICITY_PRICE_PER_KWH
            fuel_cost_per_km = (consumption / 100) * electricity_price
        else:
            fuel_cost_per_km = 0.0

        total_cost_per_km += fuel_cost_per_km

        # Efficiency score (lower cost = higher score, max 100)
        # Assume $1/km is average, score inversely proportional
        efficiency_score = min(100, max(0, 100 - (total_cost_per_km * 50)))

        return {
            "vehicle_id": vehicle_id,
            "total_cost_per_km": total_cost_per_km,
            "fuel_cost_per_km": fuel_cost_per_km,
            "maintenance_cost_per_km": total_cost_per_km - fuel_cost_per_km,
            "efficiency_score": efficiency_score,
            "fuel_type": vehicle.fuel_type.value
        }
