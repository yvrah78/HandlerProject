"""
Operations tools for Operations Agent.
Tools for routing, fleet management, driver assignment, and scheduling.
"""
from typing import Dict, Any, Optional, List, Tuple
from pydantic import Field
from datetime import datetime

from src.agents.tools.base_tool import BaseTool, ToolInput, ToolOutput
from src.core.logging import get_logger
from src.core.database import get_db
from src.models.vehicle import Vehicle, VehicleStatus
from src.models.driver import Driver, DriverStatus
from src.models.booking import Booking

logger = get_logger(__name__)


class OptimizeRouteInput(ToolInput):
    """Input for optimize_route tool."""

    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Ending location")
    waypoints: Optional[List[str]] = Field(None, description="Intermediate stops")
    vehicle_id: Optional[int] = Field(None, description="Vehicle ID (for constraints)")


class AssignDriverInput(ToolInput):
    """Input for assign_driver tool."""

    booking_id: int = Field(..., description="Booking ID")
    driver_id: int = Field(..., description="Driver ID to assign")


class GetFleetStatusInput(ToolInput):
    """Input for get_fleet_status tool."""

    status_filter: Optional[str] = Field(None, description="Filter by status")


class TrackVehicleInput(ToolInput):
    """Input for track_vehicle tool."""

    vehicle_id: int = Field(..., description="Vehicle ID to track")


class OptimizeRouteTool(BaseTool):
    """Tool for optimizing routes using Google Maps."""

    def __init__(self):
        super().__init__(
            name="optimize_route",
            description="Optimize route between locations using Google Maps",
            input_schema=OptimizeRouteInput,
            required_permissions=["read:routes", "use:maps"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute route optimization."""
        try:
            origin = input_data.get("origin")
            destination = input_data.get("destination")
            waypoints = input_data.get("waypoints", [])

            # In a real scenario, this would call Google Maps API
            # For now, return mock optimized route
            route_data = {
                "origin": origin,
                "destination": destination,
                "waypoints": waypoints,
                "distance_km": 15.5,
                "duration_minutes": 25,
                "polyline": "encoded_polyline_here",
                "steps": [
                    {
                        "instruction": "Head east on Main St",
                        "distance_m": 500,
                        "duration_s": 45,
                    },
                    {
                        "instruction": "Turn left on 5th Ave",
                        "distance_m": 1200,
                        "duration_s": 90,
                    },
                ],
            }

            logger.info(
                f"Route optimized: {origin} → {destination} "
                f"({route_data['distance_km']}km, {route_data['duration_minutes']}min)"
            )

            return ToolOutput(
                success=True,
                data=route_data,
            )

        except Exception as e:
            logger.error(f"Error optimizing route: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class AssignDriverTool(BaseTool):
    """Tool for assigning drivers to bookings."""

    def __init__(self):
        super().__init__(
            name="assign_driver",
            description="Assign driver to booking",
            input_schema=AssignDriverInput,
            required_permissions=["write:bookings", "write:drivers"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute driver assignment."""
        try:
            booking_id = input_data.get("booking_id")
            driver_id = input_data.get("driver_id")

            db = get_db()

            # Get booking and driver
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            driver = db.query(Driver).filter(Driver.id == driver_id).first()

            if not booking:
                return ToolOutput(
                    success=False,
                    error=f"Booking {booking_id} not found",
                )

            if not driver:
                return ToolOutput(
                    success=False,
                    error=f"Driver {driver_id} not found",
                )

            if driver.status != DriverStatus.AVAILABLE:
                return ToolOutput(
                    success=False,
                    error=f"Driver not available (status: {driver.status})",
                )

            # Assign driver
            booking.driver_id = driver_id
            driver.status = DriverStatus.ON_DUTY
            db.commit()

            logger.info(f"Driver {driver.id} assigned to booking {booking.id}")

            return ToolOutput(
                success=True,
                data={
                    "booking_id": booking.id,
                    "driver_id": driver.id,
                    "driver_name": driver.full_name,
                    "status": "assigned",
                },
            )

        except Exception as e:
            logger.error(f"Error assigning driver: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class GetFleetStatusTool(BaseTool):
    """Tool for getting fleet status."""

    def __init__(self):
        super().__init__(
            name="get_fleet_status",
            description="Get current fleet status and vehicle availability",
            input_schema=GetFleetStatusInput,
            required_permissions=["read:vehicles"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute get fleet status."""
        try:
            status_filter = input_data.get("status_filter")

            db = get_db()
            query = db.query(Vehicle).filter(Vehicle.is_active == True)

            if status_filter:
                query = query.filter(Vehicle.status == status_filter)

            vehicles = query.all()

            fleet_summary = {
                "total_vehicles": len(vehicles),
                "by_status": {},
                "vehicles": [],
            }

            # Count by status
            for vehicle in vehicles:
                status = vehicle.status
                if status not in fleet_summary["by_status"]:
                    fleet_summary["by_status"][status] = 0
                fleet_summary["by_status"][status] += 1

                # Add vehicle detail
                fleet_summary["vehicles"].append(
                    {
                        "id": vehicle.id,
                        "plate": vehicle.license_plate,
                        "type": vehicle.vehicle_type,
                        "status": vehicle.status,
                        "mileage_km": vehicle.mileage_km,
                    }
                )

            return ToolOutput(
                success=True,
                data=fleet_summary,
            )

        except Exception as e:
            logger.error(f"Error getting fleet status: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class TrackVehicleTool(BaseTool):
    """Tool for tracking vehicle information."""

    def __init__(self):
        super().__init__(
            name="track_vehicle",
            description="Get vehicle tracking and status information",
            input_schema=TrackVehicleInput,
            required_permissions=["read:vehicles"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute vehicle tracking."""
        try:
            vehicle_id = input_data.get("vehicle_id")

            db = get_db()
            vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

            if not vehicle:
                return ToolOutput(
                    success=False,
                    error=f"Vehicle {vehicle_id} not found",
                )

            vehicle_info = {
                "id": vehicle.id,
                "license_plate": vehicle.license_plate,
                "model": f"{vehicle.brand} {vehicle.model}",
                "status": vehicle.status,
                "mileage_km": vehicle.mileage_km,
                "last_maintenance": (
                    vehicle.last_maintenance_date.isoformat()
                    if vehicle.last_maintenance_date
                    else None
                ),
                "next_maintenance": (
                    vehicle.next_maintenance_date.isoformat()
                    if vehicle.next_maintenance_date
                    else None
                ),
                "fuel_type": vehicle.fuel_type,
                "capacity_kg": vehicle.capacity_kg,
            }

            return ToolOutput(
                success=True,
                data=vehicle_info,
            )

        except Exception as e:
            logger.error(f"Error tracking vehicle: {str(e)}")
            return ToolOutput(success=False, error=str(e))


def register_operations_tools(registry) -> None:
    """
    Register all operations tools in the registry.

    Args:
        registry: ToolRegistry instance
    """
    registry.register(OptimizeRouteTool(), category="operations")
    registry.register(AssignDriverTool(), category="operations")
    registry.register(GetFleetStatusTool(), category="operations")
    registry.register(TrackVehicleTool(), category="operations")
    logger.info("Operations tools registered")
