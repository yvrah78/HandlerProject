"""
Operations Agent for Project Handler - AI-powered version.
Handles route planning, fleet management, and logistics via Google Maps.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, AgentError
from src.core.logging import get_logger

logger = get_logger("agent.operations")


class OperationsAgent(BaseAgent):
    """
    Intelligent agent responsible for all operational logistics.

    Capabilities:
    - Route planning and optimization via Google Maps
    - Distance and duration calculations
    - Address geocoding and validation
    - Multi-stop route optimization
    - Traffic-aware routing
    - Fleet assignment recommendations

    Modes:
    - Demo mode: Simulates operations without Google Maps API calls
    - Live mode: Uses real Google Maps API
    """

    def __init__(self):
        super().__init__(
            name="operations",
            description="AI-powered operations agent handling route planning and logistics"
        )

        # Initialize integrations (lazy loading)
        self._gmaps_client = None

        # Operations history
        self.operations_history: List[Dict[str, Any]] = []

        # Fleet simulation data (for demo mode)
        self.available_drivers = [
            {"id": "DRV001", "name": "Driver A", "status": "available", "location": "Depot"},
            {"id": "DRV002", "name": "Driver B", "status": "available", "location": "Depot"},
            {"id": "DRV003", "name": "Driver C", "status": "on_route", "location": "Downtown"}
        ]

        # Check for API keys
        self.demo_mode = self._check_demo_mode()

    def _check_demo_mode(self) -> bool:
        """Check if we're in demo mode (no Google Maps API key)."""
        gmaps_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if not gmaps_key or gmaps_key.startswith("your_"):
            logger.warning("No Google Maps API key found - running in demo mode")
            return True

        return False

    @property
    def gmaps_client(self):
        """Lazy load Google Maps client."""
        if self._gmaps_client is None and not self.demo_mode:
            try:
                import googlemaps
                api_key = os.getenv("GOOGLE_MAPS_API_KEY")

                if api_key and not api_key.startswith("your_"):
                    self._gmaps_client = googlemaps.Client(key=api_key)
                    logger.info("Google Maps client initialized successfully")
                else:
                    logger.warning("Invalid Google Maps API key - enabling demo mode")
                    self.demo_mode = True
            except ImportError:
                logger.error("googlemaps library not installed - enabling demo mode")
                self.demo_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps: {e}")
                self.demo_mode = True

        return self._gmaps_client

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process operations request with intelligence.

        Args:
            input_data: Operations request data

        Returns:
            Dict[str, Any]: Operation result
        """
        operation = input_data.get("operation_type", "").lower()

        # Route to appropriate handler
        if operation == "route_planning" or operation == "route":
            return await self._handle_route_planning(input_data)
        elif operation == "distance" or operation == "calculate_distance":
            return await self._handle_distance_calculation(input_data)
        elif operation == "geocode":
            return await self._handle_geocoding(input_data)
        elif operation == "optimize_route" or operation == "optimization":
            return await self._handle_route_optimization(input_data)
        elif operation == "fleet_assignment" or operation == "assign_driver":
            return await self._handle_fleet_assignment(input_data)
        else:
            return await self._handle_generic(input_data)

    async def _handle_route_planning(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route planning between origin and destination."""
        origin = input_data.get("origin")
        destination = input_data.get("destination")
        mode = input_data.get("mode", "driving")  # driving, walking, bicycling, transit
        optimize_waypoints = input_data.get("optimize_waypoints", False)
        waypoints = input_data.get("waypoints", [])

        self.logger.info(f"Planning route from {origin} to {destination}")

        if self.demo_mode or not self.gmaps_client:
            # Demo mode response with realistic data
            estimated_distance = 25.5  # miles
            estimated_duration = 35  # minutes

            result = {
                "status": "demo_planned",
                "origin": origin,
                "destination": destination,
                "waypoints": waypoints,
                "mode": mode,
                "distance": {
                    "miles": estimated_distance,
                    "kilometers": round(estimated_distance * 1.60934, 2)
                },
                "duration": {
                    "minutes": estimated_duration,
                    "hours": round(estimated_duration / 60, 2),
                    "text": f"{estimated_duration} mins"
                },
                "estimated_arrival": datetime.utcnow().isoformat(),
                "note": "Demo mode - no actual routing done. Configure GOOGLE_MAPS_API_KEY to enable.",
                "channel": "route_planning"
            }
        else:
            try:
                # Real Google Maps directions
                directions_params = {
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "departure_time": "now"
                }

                if waypoints:
                    directions_params["waypoints"] = waypoints
                    directions_params["optimize_waypoints"] = optimize_waypoints

                directions_result = self.gmaps_client.directions(**directions_params)

                if directions_result:
                    leg = directions_result[0]['legs'][0]

                    result = {
                        "status": "planned",
                        "origin": leg['start_address'],
                        "destination": leg['end_address'],
                        "distance": {
                            "meters": leg['distance']['value'],
                            "kilometers": round(leg['distance']['value'] / 1000, 2),
                            "miles": round(leg['distance']['value'] / 1609.34, 2),
                            "text": leg['distance']['text']
                        },
                        "duration": {
                            "seconds": leg['duration']['value'],
                            "minutes": round(leg['duration']['value'] / 60, 1),
                            "hours": round(leg['duration']['value'] / 3600, 2),
                            "text": leg['duration']['text']
                        },
                        "mode": mode,
                        "steps": len(leg['steps']),
                        "channel": "route_planning"
                    }

                    logger.info(f"Route planned: {result['distance']['miles']} miles, {result['duration']['minutes']} mins")
                else:
                    result = {
                        "status": "failed",
                        "error": "No route found",
                        "origin": origin,
                        "destination": destination,
                        "channel": "route_planning"
                    }

            except Exception as e:
                logger.error(f"Failed to plan route: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "origin": origin,
                    "destination": destination,
                    "channel": "route_planning"
                }

        # Save to history
        self._add_to_history("route_planning", result)

        return result

    async def _handle_distance_calculation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle distance calculation between locations."""
        origins = input_data.get("origins", [])
        destinations = input_data.get("destinations", [])
        mode = input_data.get("mode", "driving")

        # Handle single origin/destination
        if "origin" in input_data and "destination" in input_data:
            origins = [input_data["origin"]]
            destinations = [input_data["destination"]]

        self.logger.info(f"Calculating distances for {len(origins)} origins to {len(destinations)} destinations")

        if self.demo_mode or not self.gmaps_client:
            # Demo mode response
            result = {
                "status": "demo_calculated",
                "origins": origins,
                "destinations": destinations,
                "mode": mode,
                "distances": [
                    {
                        "origin": origins[0] if origins else "N/A",
                        "destination": destinations[0] if destinations else "N/A",
                        "distance_miles": 25.5,
                        "distance_km": 41.0,
                        "duration_minutes": 35
                    }
                ],
                "note": "Demo mode - Configure GOOGLE_MAPS_API_KEY to enable.",
                "channel": "distance"
            }
        else:
            try:
                # Real Google Maps Distance Matrix
                matrix_result = self.gmaps_client.distance_matrix(
                    origins=origins,
                    destinations=destinations,
                    mode=mode
                )

                distances = []
                for i, origin_row in enumerate(matrix_result['rows']):
                    for j, element in enumerate(origin_row['elements']):
                        if element['status'] == 'OK':
                            distances.append({
                                "origin": matrix_result['origin_addresses'][i],
                                "destination": matrix_result['destination_addresses'][j],
                                "distance_meters": element['distance']['value'],
                                "distance_km": round(element['distance']['value'] / 1000, 2),
                                "distance_miles": round(element['distance']['value'] / 1609.34, 2),
                                "distance_text": element['distance']['text'],
                                "duration_seconds": element['duration']['value'],
                                "duration_minutes": round(element['duration']['value'] / 60, 1),
                                "duration_text": element['duration']['text']
                            })

                result = {
                    "status": "calculated",
                    "origins": matrix_result['origin_addresses'],
                    "destinations": matrix_result['destination_addresses'],
                    "mode": mode,
                    "distances": distances,
                    "total_combinations": len(distances),
                    "channel": "distance"
                }

                logger.info(f"Calculated {len(distances)} distance combinations")

            except Exception as e:
                logger.error(f"Failed to calculate distances: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "origins": origins,
                    "destinations": destinations,
                    "channel": "distance"
                }

        # Save to history
        self._add_to_history("distance", result)

        return result

    async def _handle_geocoding(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle address geocoding to coordinates."""
        address = input_data.get("address")
        reverse = input_data.get("reverse", False)
        lat = input_data.get("lat")
        lng = input_data.get("lng")

        if reverse and lat is not None and lng is not None:
            self.logger.info(f"Reverse geocoding coordinates: ({lat}, {lng})")
        else:
            self.logger.info(f"Geocoding address: {address}")

        if self.demo_mode or not self.gmaps_client:
            # Demo mode response
            if reverse:
                result = {
                    "status": "demo_geocoded",
                    "lat": lat,
                    "lng": lng,
                    "formatted_address": "123 Demo Street, Demo City, DC 12345",
                    "note": "Demo mode - Configure GOOGLE_MAPS_API_KEY to enable.",
                    "channel": "geocode"
                }
            else:
                result = {
                    "status": "demo_geocoded",
                    "address": address,
                    "lat": 40.7128,
                    "lng": -74.0060,
                    "formatted_address": address,
                    "note": "Demo mode - Configure GOOGLE_MAPS_API_KEY to enable.",
                    "channel": "geocode"
                }
        else:
            try:
                if reverse:
                    # Reverse geocoding
                    geocode_result = self.gmaps_client.reverse_geocode((lat, lng))
                else:
                    # Forward geocoding
                    geocode_result = self.gmaps_client.geocode(address)

                if geocode_result:
                    location = geocode_result[0]

                    result = {
                        "status": "geocoded",
                        "formatted_address": location['formatted_address'],
                        "lat": location['geometry']['location']['lat'],
                        "lng": location['geometry']['location']['lng'],
                        "place_id": location.get('place_id'),
                        "types": location.get('types', []),
                        "channel": "geocode"
                    }

                    if not reverse:
                        result["input_address"] = address

                    logger.info(f"Geocoded successfully: {result['formatted_address']}")
                else:
                    result = {
                        "status": "failed",
                        "error": "No results found",
                        "address": address if not reverse else f"({lat}, {lng})",
                        "channel": "geocode"
                    }

            except Exception as e:
                logger.error(f"Failed to geocode: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "address": address if not reverse else f"({lat}, {lng})",
                    "channel": "geocode"
                }

        # Save to history
        self._add_to_history("geocode", result)

        return result

    async def _handle_route_optimization(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-stop route optimization."""
        waypoints = input_data.get("waypoints", [])
        origin = input_data.get("origin")
        destination = input_data.get("destination")
        mode = input_data.get("mode", "driving")

        self.logger.info(f"Optimizing route with {len(waypoints)} waypoints")

        if self.demo_mode or not self.gmaps_client:
            # Demo mode response with simulated optimization
            optimized_order = list(range(len(waypoints)))

            result = {
                "status": "demo_optimized",
                "origin": origin,
                "destination": destination,
                "waypoints": waypoints,
                "optimized_order": optimized_order,
                "optimized_waypoints": [waypoints[i] for i in optimized_order] if waypoints else [],
                "total_distance_miles": 45.5,
                "total_duration_minutes": 65,
                "savings": {
                    "distance_miles": 5.2,
                    "duration_minutes": 12
                },
                "note": "Demo mode - Configure GOOGLE_MAPS_API_KEY to enable.",
                "channel": "route_optimization"
            }
        else:
            try:
                # Real Google Maps route optimization
                directions_result = self.gmaps_client.directions(
                    origin=origin or waypoints[0],
                    destination=destination or waypoints[-1],
                    waypoints=waypoints,
                    optimize_waypoints=True,
                    mode=mode
                )

                if directions_result:
                    route = directions_result[0]

                    # Extract optimized waypoint order
                    optimized_order = route.get('waypoint_order', list(range(len(waypoints))))

                    # Calculate totals
                    total_distance = sum(leg['distance']['value'] for leg in route['legs'])
                    total_duration = sum(leg['duration']['value'] for leg in route['legs'])

                    result = {
                        "status": "optimized",
                        "origin": route['legs'][0]['start_address'],
                        "destination": route['legs'][-1]['end_address'],
                        "waypoints": waypoints,
                        "optimized_order": optimized_order,
                        "optimized_waypoints": [waypoints[i] for i in optimized_order],
                        "total_distance": {
                            "meters": total_distance,
                            "kilometers": round(total_distance / 1000, 2),
                            "miles": round(total_distance / 1609.34, 2)
                        },
                        "total_duration": {
                            "seconds": total_duration,
                            "minutes": round(total_duration / 60, 1),
                            "hours": round(total_duration / 3600, 2)
                        },
                        "legs": len(route['legs']),
                        "mode": mode,
                        "channel": "route_optimization"
                    }

                    logger.info(f"Route optimized: {result['total_distance']['miles']} miles, {result['total_duration']['minutes']} mins")
                else:
                    result = {
                        "status": "failed",
                        "error": "No route found",
                        "waypoints": waypoints,
                        "channel": "route_optimization"
                    }

            except Exception as e:
                logger.error(f"Failed to optimize route: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "waypoints": waypoints,
                    "channel": "route_optimization"
                }

        # Save to history
        self._add_to_history("route_optimization", result)

        return result

    async def _handle_fleet_assignment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle intelligent fleet/driver assignment."""
        pickup_location = input_data.get("pickup_location")
        delivery_location = input_data.get("delivery_location")
        requirements = input_data.get("requirements", [])

        self.logger.info(f"Assigning driver for pickup at {pickup_location}")

        # Simulate intelligent assignment based on proximity and availability
        available = [d for d in self.available_drivers if d["status"] == "available"]

        if available:
            # In real implementation, would calculate distances to pickup
            assigned_driver = available[0]

            result = {
                "status": "assigned",
                "driver": {
                    "id": assigned_driver["id"],
                    "name": assigned_driver["name"],
                    "current_location": assigned_driver["location"]
                },
                "pickup_location": pickup_location,
                "delivery_location": delivery_location,
                "estimated_arrival_to_pickup_minutes": 15,
                "requirements_met": requirements,
                "channel": "fleet_assignment"
            }

            # Update driver status (in-memory simulation)
            assigned_driver["status"] = "assigned"

            logger.info(f"Driver {assigned_driver['id']} assigned")
        else:
            result = {
                "status": "no_drivers_available",
                "pickup_location": pickup_location,
                "message": "No available drivers at this time",
                "channel": "fleet_assignment"
            }

        # Save to history
        self._add_to_history("fleet_assignment", result)

        return result

    async def _handle_generic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic operations request."""
        return {
            "status": "processed",
            "message": "Generic operations handler",
            "data": input_data
        }

    def _add_to_history(self, operation_type: str, result: Dict[str, Any]):
        """Add operation to history."""
        self.operations_history.append({
            "operation_type": operation_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 100 operations
        if len(self.operations_history) > 100:
            self.operations_history = self.operations_history[-100:]

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
        if not isinstance(input_data, dict):
            raise ValidationError(
                "Input must be a dictionary",
                details={"received_type": type(input_data).__name__}
            )

        # Must have operation type
        operation = input_data.get("operation_type")
        if not operation:
            raise ValidationError(
                "Missing required field: operation_type",
                details={"received_keys": list(input_data.keys())}
            )

        valid_operations = [
            "route_planning", "route", "distance", "calculate_distance",
            "geocode", "optimize_route", "optimization", "fleet_assignment", "assign_driver"
        ]
        if operation.lower() not in valid_operations:
            raise ValidationError(
                f"Invalid operation type. Must be one of: {valid_operations}",
                details={"received": operation}
            )

        # Validate operation-specific requirements
        if operation.lower() in ["route_planning", "route"]:
            if "origin" not in input_data or "destination" not in input_data:
                raise ValidationError(
                    "Route planning requires 'origin' and 'destination' fields",
                    details={"operation": operation}
                )

        elif operation.lower() in ["distance", "calculate_distance"]:
            if "origin" not in input_data and "origins" not in input_data:
                raise ValidationError(
                    "Distance calculation requires 'origin' or 'origins' field",
                    details={"operation": operation}
                )

        elif operation.lower() == "geocode":
            if "address" not in input_data and ("lat" not in input_data or "lng" not in input_data):
                raise ValidationError(
                    "Geocoding requires 'address' or 'lat'/'lng' fields",
                    details={"operation": operation}
                )

        return True

    def get_operations_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get operations history."""
        if limit:
            return self.operations_history[-limit:]
        return self.operations_history

    def clear_history(self):
        """Clear operations history."""
        self.operations_history = []
        logger.info("Operations history cleared")

    def get_fleet_status(self) -> Dict[str, Any]:
        """Get current fleet status."""
        return {
            "total_drivers": len(self.available_drivers),
            "available": len([d for d in self.available_drivers if d["status"] == "available"]),
            "assigned": len([d for d in self.available_drivers if d["status"] == "assigned"]),
            "on_route": len([d for d in self.available_drivers if d["status"] == "on_route"]),
            "drivers": self.available_drivers
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced agent status."""
        base_status = super().get_status()
        base_status.update({
            "demo_mode": self.demo_mode,
            "google_maps_enabled": self.gmaps_client is not None,
            "total_operations": len(self.operations_history),
            "supported_operations": [
                "route_planning", "distance", "geocode",
                "optimize_route", "fleet_assignment"
            ],
            "fleet_status": self.get_fleet_status()
        })
        return base_status
