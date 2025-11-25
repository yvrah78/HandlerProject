"""
Operations Agent for Project Handler.
Handles route planning, fleet management, and logistics operations via Google Maps.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, IntegrationError
from src.integrations.googlemaps_client import GoogleMapsClient


class OperationsAgent(BaseAgent):
    """
    Agent responsible for operational logistics.

    Integration:
    - Google Maps: Geocoding, routing, distance calculations

    Capabilities:
    - Route planning and optimization
    - Distance and duration calculations
    - Multi-stop route optimization
    - Address validation and geocoding
    - Fleet management and assignment
    - Real-time tracking support
    """

    def __init__(self):
        """Initialize Operations Agent with Google Maps client."""
        super().__init__(
            name="operations",
            description="Handles route planning, fleet management, and logistics via Google Maps"
        )

        # Initialize Google Maps integration
        self.maps = GoogleMapsClient()

        # Track operational statistics
        self.stats = {
            "total_routes": 0,
            "routes_optimized": 0,
            "total_distance_km": 0.0,
            "total_duration_min": 0.0,
            "addresses_validated": 0,
            "failed_operations": 0
        }

        self.logger.info(f"Operations Agent initialized - Google Maps: {self.maps.enabled}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process operations request.

        Args:
            input_data: Must contain 'operation_type' and relevant data

        Returns:
            Dict[str, Any]: Operations result

        Raises:
            ValidationError: If input is invalid
            IntegrationError: If operation fails
        """
        await self.validate_input(input_data)

        operation = input_data.get("operation_type")
        self.logger.info(f"Processing {operation} operation")

        # Route to appropriate handler
        if operation == "route_planning":
            result = await self.plan_route(input_data)
        elif operation == "route_optimization":
            result = await self.optimize_route(input_data)
        elif operation == "distance_calculation":
            result = await self.calculate_distance(input_data)
        elif operation == "address_validation":
            result = await self.validate_address(input_data)
        elif operation == "geocoding":
            result = await self.geocode_address(input_data)
        else:
            raise ValidationError(
                f"Unknown operation type: {operation}",
                details={"received": operation}
            )

        # Update statistics
        self.stats["total_routes"] += 1

        return result

    async def plan_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan route from origin to destination.

        Args:
            data: Must contain 'origin' and 'destination'

        Returns:
            dict: Route planning result with directions
        """
        origin = data.get("origin")
        destination = data.get("destination")
        mode = data.get("mode", "driving")
        waypoints = data.get("waypoints", [])

        self.logger.info(f"Planning route from {origin} to {destination}")

        try:
            result = await self.maps.get_directions(
                origin=origin,
                destination=destination,
                mode=mode,
                waypoints=waypoints if waypoints else None
            )

            # Update stats
            self.stats["total_distance_km"] += result["distance"]["value"] / 1000
            self.stats["total_duration_min"] += result["duration"]["value"] / 60

            return {
                "operation_type": "route_planning",
                "status": "success",
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "distance": result["distance"],
                "duration": result["duration"],
                "steps": result["steps"],
                "polyline": result["polyline"],
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to plan route: {str(e)}")
            self.stats["failed_operations"] += 1
            return {
                "operation_type": "route_planning",
                "status": "failed",
                "origin": origin,
                "destination": destination,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def optimize_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize route with multiple waypoints.

        Args:
            data: Must contain 'origin', 'destination', and 'waypoints'

        Returns:
            dict: Optimized route with waypoint order
        """
        origin = data.get("origin")
        destination = data.get("destination")
        waypoints = data.get("waypoints", [])

        self.logger.info(f"Optimizing route with {len(waypoints)} waypoints")

        try:
            result = await self.maps.optimize_route(
                origin=origin,
                destination=destination,
                waypoints=waypoints
            )

            self.stats["routes_optimized"] += 1

            return {
                "operation_type": "route_optimization",
                "status": "success",
                "origin": origin,
                "destination": destination,
                "waypoints_count": len(waypoints),
                "optimized_order": result["optimized_order"],
                "total_distance": result["total_distance"],
                "total_duration": result["total_duration"],
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to optimize route: {str(e)}")
            self.stats["failed_operations"] += 1
            return {
                "operation_type": "route_optimization",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def calculate_distance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate distance and duration between locations.

        Args:
            data: Must contain 'origin' and 'destination'

        Returns:
            dict: Distance calculation result
        """
        origin = data.get("origin")
        destination = data.get("destination")
        mode = data.get("mode", "driving")

        self.logger.info(f"Calculating distance from {origin} to {destination}")

        try:
            result = await self.maps.calculate_distance(
                origin=origin,
                destination=destination,
                mode=mode
            )

            return {
                "operation_type": "distance_calculation",
                "status": "success",
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "distance": result["distance"],
                "duration": result["duration"],
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to calculate distance: {str(e)}")
            self.stats["failed_operations"] += 1
            return {
                "operation_type": "distance_calculation",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def validate_address(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate address and get standardized format.

        Args:
            data: Must contain 'address'

        Returns:
            dict: Address validation result
        """
        address = data.get("address")

        self.logger.info(f"Validating address: {address}")

        try:
            result = await self.maps.validate_address(address)

            if result["valid"]:
                self.stats["addresses_validated"] += 1

            return {
                "operation_type": "address_validation",
                "status": "success",
                "address": address,
                "valid": result["valid"],
                "formatted_address": result.get("formatted_address"),
                "coordinates": {
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude")
                } if result["valid"] else None,
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to validate address: {str(e)}")
            return {
                "operation_type": "address_validation",
                "status": "failed",
                "address": address,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def geocode_address(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert address to geographic coordinates.

        Args:
            data: Must contain 'address'

        Returns:
            dict: Geocoding result
        """
        address = data.get("address")

        self.logger.info(f"Geocoding address: {address}")

        try:
            result = await self.maps.geocode(address)

            return {
                "operation_type": "geocoding",
                "status": "success",
                "address": address,
                "formatted_address": result["formatted_address"],
                "coordinates": {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"]
                },
                "place_id": result["place_id"],
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to geocode address: {str(e)}")
            self.stats["failed_operations"] += 1
            return {
                "operation_type": "geocoding",
                "status": "failed",
                "address": address,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate operations input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ["operation_type"]

        for field in required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"received_keys": list(input_data.keys())}
                )

        valid_operations = [
            "route_planning",
            "route_optimization",
            "distance_calculation",
            "address_validation",
            "geocoding"
        ]
        if input_data["operation_type"] not in valid_operations:
            raise ValidationError(
                f"Invalid operation type. Must be one of: {valid_operations}",
                details={"received": input_data["operation_type"]}
            )

        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status including Google Maps integration status.

        Returns:
            dict: Agent and integration status
        """
        return {
            "agent_name": self.name,
            "enabled": True,
            "integrations": {
                "google_maps": self.maps.get_status()
            },
            "statistics": self.stats,
            "capabilities": {
                "route_planning": self.maps.enabled,
                "route_optimization": self.maps.enabled,
                "distance_calculation": self.maps.enabled,
                "geocoding": self.maps.enabled,
                "address_validation": self.maps.enabled
            }
        }
