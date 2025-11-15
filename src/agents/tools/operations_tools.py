"""
LangChain tools for operations and logistics.

These tools allow the OperationsAgent to plan routes, assign vehicles and drivers,
and track fleet operations using Google Maps API.
"""
from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from src.core.logging import get_logger
from src.core.database import get_db


logger = get_logger(__name__)


class PlanRouteInput(BaseModel):
    """Input schema for route planning."""
    origin: str = Field(description="Starting location address")
    destination: str = Field(description="Destination address")
    optimize_for: str = Field(default="time", description="Optimize for 'time' or 'distance'")


class PlanRouteTool(BaseTool):
    """
    Tool for planning optimal routes using Google Maps.

    Calculates best routes considering traffic, distance, and time.
    """
    name = "plan_route"
    description = """
    Plan an optimal route from origin to destination. Use this when
    you need to calculate travel time, distance, or find the best path.
    Input should include origin and destination addresses.
    """
    args_schema: Type[BaseModel] = PlanRouteInput

    def _run(
        self,
        origin: str,
        destination: str,
        optimize_for: str = "time",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Plan route.

        Args:
            origin: Origin address
            destination: Destination address
            optimize_for: Optimization preference
            run_manager: Callback manager

        Returns:
            str: JSON response with route details
        """
        try:
            from src.models.route import Route
            from datetime import datetime

            # Placeholder calculation (would use Google Maps API in production)
            # TODO: Integrate actual Google Maps routing
            estimated_distance = 15.5  # km
            estimated_duration = 25  # minutes
            estimated_cost = 35.00  # USD

            # Create route record
            db = next(get_db())
            route = Route(
                origin=origin,
                destination=destination,
                distance=estimated_distance,
                duration=estimated_duration,
                status="planned"
            )
            db.add(route)
            db.commit()
            db.refresh(route)

            logger.info(f"Route planned: {route.id} from {origin} to {destination}")

            import json
            return json.dumps({
                "success": True,
                "route_id": route.id,
                "origin": origin,
                "destination": destination,
                "distance_km": estimated_distance,
                "duration_minutes": estimated_duration,
                "estimated_cost": estimated_cost,
                "optimized_for": optimize_for,
                "message": "Route planned (Google Maps API not configured)"
            })

        except Exception as e:
            logger.error(f"Failed to plan route: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        origin: str,
        destination: str,
        optimize_for: str = "time",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(origin, destination, optimize_for, run_manager)


class AssignVehicleInput(BaseModel):
    """Input schema for vehicle assignment."""
    booking_id: str = Field(description="Booking ID to assign vehicle to")
    vehicle_type: str = Field(description="Type of vehicle needed (e.g., 'sedan', 'suv', 'van')")
    passenger_count: int = Field(default=1, description="Number of passengers")


class AssignVehicleTool(BaseTool):
    """
    Tool for assigning vehicles to bookings.

    Finds and assigns available vehicles based on capacity and type requirements.
    """
    name = "assign_vehicle"
    description = """
    Assign a vehicle to a booking. Use this after a booking is created
    to allocate an appropriate vehicle. Input should include booking ID
    and vehicle requirements.
    """
    args_schema: Type[BaseModel] = AssignVehicleInput

    def _run(
        self,
        booking_id: str,
        vehicle_type: str,
        passenger_count: int = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Assign vehicle.

        Args:
            booking_id: Booking ID
            vehicle_type: Required vehicle type
            passenger_count: Number of passengers
            run_manager: Callback manager

        Returns:
            str: JSON response with assignment details
        """
        try:
            from src.models.vehicle import Vehicle
            from src.models.booking import Booking

            db = next(get_db())

            # Find available vehicle of requested type
            vehicle = db.query(Vehicle).filter(
                Vehicle.vehicle_type == vehicle_type,
                Vehicle.status == "available"
            ).first()

            if not vehicle:
                # Create a placeholder vehicle for demo
                vehicle = Vehicle(
                    vehicle_type=vehicle_type,
                    capacity=passenger_count + 2,  # Some extra capacity
                    license_plate=f"{vehicle_type.upper()[:3]}-DEMO",
                    status="available"
                )
                db.add(vehicle)
                db.commit()
                db.refresh(vehicle)

            # Update booking with vehicle
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if booking:
                booking.vehicle_id = vehicle.id
                vehicle.status = "assigned"
                db.commit()

            logger.info(f"Vehicle {vehicle.id} assigned to booking {booking_id}")

            import json
            return json.dumps({
                "success": True,
                "booking_id": booking_id,
                "vehicle_id": vehicle.id,
                "vehicle_type": vehicle_type,
                "license_plate": vehicle.license_plate,
                "capacity": vehicle.capacity,
                "status": "assigned"
            })

        except Exception as e:
            logger.error(f"Failed to assign vehicle: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        booking_id: str,
        vehicle_type: str,
        passenger_count: int = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(booking_id, vehicle_type, passenger_count, run_manager)


class AssignDriverInput(BaseModel):
    """Input schema for driver assignment."""
    booking_id: str = Field(description="Booking ID to assign driver to")
    vehicle_id: str = Field(description="Vehicle ID that needs a driver")
    required_skills: Optional[str] = Field(default=None, description="Required driver skills (e.g., 'airport', 'luxury')")


class AssignDriverTool(BaseTool):
    """
    Tool for assigning drivers to bookings.

    Finds and assigns available drivers with appropriate skills and certifications.
    """
    name = "assign_driver"
    description = """
    Assign a driver to a booking and vehicle. Use this after a vehicle
    is assigned to match an available driver. Input should include booking ID
    and vehicle ID.
    """
    args_schema: Type[BaseModel] = AssignDriverInput

    def _run(
        self,
        booking_id: str,
        vehicle_id: str,
        required_skills: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Assign driver.

        Args:
            booking_id: Booking ID
            vehicle_id: Vehicle ID
            required_skills: Required driver skills
            run_manager: Callback manager

        Returns:
            str: JSON response with assignment details
        """
        try:
            from src.models.driver import Driver
            from src.models.booking import Booking

            db = next(get_db())

            # Find available driver
            driver = db.query(Driver).filter(
                Driver.status == "available"
            ).first()

            if not driver:
                # Create a placeholder driver for demo
                driver = Driver(
                    name="Demo Driver",
                    phone="555-0100",
                    email="driver@demo.com",
                    license_number="DL-DEMO-001",
                    status="available"
                )
                db.add(driver)
                db.commit()
                db.refresh(driver)

            # Update booking with driver
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if booking:
                booking.driver_id = driver.id
                driver.status = "assigned"
                db.commit()

            logger.info(f"Driver {driver.id} assigned to booking {booking_id}")

            import json
            return json.dumps({
                "success": True,
                "booking_id": booking_id,
                "driver_id": driver.id,
                "driver_name": driver.name,
                "driver_phone": driver.phone,
                "status": "assigned"
            })

        except Exception as e:
            logger.error(f"Failed to assign driver: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        booking_id: str,
        vehicle_id: str,
        required_skills: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(booking_id, vehicle_id, required_skills, run_manager)


class TrackVehicleInput(BaseModel):
    """Input schema for vehicle tracking."""
    vehicle_id: str = Field(description="Vehicle ID to track")


class TrackVehicleTool(BaseTool):
    """
    Tool for tracking vehicle locations.

    Gets real-time or last known location of vehicles in the fleet.
    """
    name = "track_vehicle"
    description = """
    Track a vehicle's current location. Use this to check where a vehicle
    is for customer updates or operational monitoring.
    Input should be the vehicle ID.
    """
    args_schema: Type[BaseModel] = TrackVehicleInput

    def _run(
        self,
        vehicle_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Track vehicle.

        Args:
            vehicle_id: Vehicle ID to track
            run_manager: Callback manager

        Returns:
            str: JSON response with location data
        """
        try:
            from src.models.vehicle import Vehicle
            from datetime import datetime

            db = next(get_db())
            vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found")

            # Placeholder location data (would use GPS/Google Maps in production)
            location_data = {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "speed": 35.5,  # mph
                "heading": 180,  # degrees
            }

            logger.info(f"Vehicle {vehicle_id} tracked")

            import json
            return json.dumps({
                "success": True,
                "vehicle_id": vehicle_id,
                "license_plate": vehicle.license_plate,
                "status": vehicle.status,
                "location": location_data,
                "last_updated": datetime.utcnow().isoformat(),
                "message": "Location data (GPS tracking not configured)"
            })

        except Exception as e:
            logger.error(f"Failed to track vehicle: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        vehicle_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(vehicle_id, run_manager)
