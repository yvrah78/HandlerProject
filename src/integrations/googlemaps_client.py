"""
Google Maps integration client for Project Handler.
Handles geocoding, routing, and distance calculations via Google Maps API.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import asyncio

import googlemaps
from googlemaps.exceptions import ApiError, TransportError, Timeout

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.exceptions import IntegrationError

logger = get_logger(__name__)
settings = get_settings()


class GoogleMapsClient:
    """Client for Google Maps API integration."""

    def __init__(self):
        """Initialize Google Maps client with API key."""
        self.api_key = settings.google_maps_api_key
        self.logger = logger
        self.enabled = False
        self.client = None

        # Initialize Google Maps client if API key is available
        if self.api_key:
            try:
                self.client = googlemaps.Client(key=self.api_key)
                self.enabled = True
                self.logger.info("Google Maps client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Google Maps client: {str(e)}")
                self.enabled = False
        else:
            self.logger.info("Google Maps API key not provided - running in disabled mode")

    def _check_enabled(self):
        """Check if Google Maps is enabled and raise error if not."""
        if not self.enabled:
            raise IntegrationError(
                "Google Maps integration is not configured. Please set GOOGLE_MAPS_API_KEY.",
                integration_name="googlemaps"
            )

    async def geocode(self, address: str) -> Dict[str, Any]:
        """
        Convert address to geographic coordinates.

        Args:
            address: Address string to geocode

        Returns:
            dict: Geocoding result with lat/lng and formatted address

        Raises:
            IntegrationError: If geocoding fails
        """
        self._check_enabled()
        self.logger.info(f"Geocoding address: {address}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.geocode(address)
            )

            if not result:
                raise IntegrationError(
                    f"No geocoding results found for address: {address}",
                    integration_name="googlemaps"
                )

            location = result[0]
            geometry = location['geometry']['location']

            return {
                "formatted_address": location['formatted_address'],
                "latitude": geometry['lat'],
                "longitude": geometry['lng'],
                "place_id": location.get('place_id'),
                "address_components": location.get('address_components', []),
                "location_type": location['geometry'].get('location_type')
            }

        except (ApiError, TransportError, Timeout) as e:
            self.logger.error(f"Google Maps geocoding error: {str(e)}")
            raise IntegrationError(
                f"Failed to geocode address: {str(e)}",
                integration_name="googlemaps"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error geocoding: {str(e)}")
            raise IntegrationError(
                f"Failed to geocode address: {str(e)}",
                integration_name="googlemaps"
            )

    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Convert geographic coordinates to address.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            dict: Reverse geocoding result with address

        Raises:
            IntegrationError: If reverse geocoding fails
        """
        self._check_enabled()
        self.logger.info(f"Reverse geocoding: {latitude}, {longitude}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.reverse_geocode((latitude, longitude))
            )

            if not result:
                raise IntegrationError(
                    f"No reverse geocoding results found for coordinates: {latitude}, {longitude}",
                    integration_name="googlemaps"
                )

            location = result[0]

            return {
                "formatted_address": location['formatted_address'],
                "latitude": latitude,
                "longitude": longitude,
                "place_id": location.get('place_id'),
                "address_components": location.get('address_components', [])
            }

        except (ApiError, TransportError, Timeout) as e:
            self.logger.error(f"Google Maps reverse geocoding error: {str(e)}")
            raise IntegrationError(
                f"Failed to reverse geocode: {str(e)}",
                integration_name="googlemaps"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to reverse geocode: {str(e)}",
                integration_name="googlemaps"
            )

    async def calculate_distance(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Calculate distance and duration between two locations.

        Args:
            origin: Starting location (address or coordinates)
            destination: Ending location (address or coordinates)
            mode: Travel mode (driving, walking, bicycling, transit)
            units: Unit system (metric or imperial)

        Returns:
            dict: Distance and duration information

        Raises:
            IntegrationError: If calculation fails
        """
        self._check_enabled()
        self.logger.info(f"Calculating distance from {origin} to {destination}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.distance_matrix(
                    origins=[origin],
                    destinations=[destination],
                    mode=mode,
                    units=units
                )
            )

            if result['rows'][0]['elements'][0]['status'] != 'OK':
                raise IntegrationError(
                    f"Could not calculate distance: {result['rows'][0]['elements'][0]['status']}",
                    integration_name="googlemaps"
                )

            element = result['rows'][0]['elements'][0]

            return {
                "origin": origin,
                "destination": destination,
                "distance": {
                    "value": element['distance']['value'],  # meters
                    "text": element['distance']['text']
                },
                "duration": {
                    "value": element['duration']['value'],  # seconds
                    "text": element['duration']['text']
                },
                "mode": mode,
                "units": units
            }

        except (ApiError, TransportError, Timeout) as e:
            self.logger.error(f"Google Maps distance error: {str(e)}")
            raise IntegrationError(
                f"Failed to calculate distance: {str(e)}",
                integration_name="googlemaps"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to calculate distance: {str(e)}",
                integration_name="googlemaps"
            )

    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        waypoints: Optional[List[str]] = None,
        optimize_waypoints: bool = False,
        alternatives: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed directions between locations.

        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode (driving, walking, bicycling, transit)
            waypoints: Optional intermediate stops
            optimize_waypoints: Optimize waypoint order
            alternatives: Return alternative routes

        Returns:
            dict: Detailed route information with steps

        Raises:
            IntegrationError: If directions request fails
        """
        self._check_enabled()
        self.logger.info(f"Getting directions from {origin} to {destination}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.directions(
                    origin=origin,
                    destination=destination,
                    mode=mode,
                    waypoints=waypoints,
                    optimize_waypoints=optimize_waypoints,
                    alternatives=alternatives
                )
            )

            if not result:
                raise IntegrationError(
                    f"No directions found from {origin} to {destination}",
                    integration_name="googlemaps"
                )

            route = result[0]
            leg = route['legs'][0]

            return {
                "origin": origin,
                "destination": destination,
                "distance": {
                    "value": leg['distance']['value'],
                    "text": leg['distance']['text']
                },
                "duration": {
                    "value": leg['duration']['value'],
                    "text": leg['duration']['text']
                },
                "start_address": leg['start_address'],
                "end_address": leg['end_address'],
                "steps": [
                    {
                        "instruction": step['html_instructions'],
                        "distance": step['distance']['text'],
                        "duration": step['duration']['text']
                    }
                    for step in leg['steps']
                ],
                "polyline": route['overview_polyline']['points'],
                "waypoint_order": route.get('waypoint_order', []),
                "alternatives_count": len(result) if alternatives else 0
            }

        except (ApiError, TransportError, Timeout) as e:
            self.logger.error(f"Google Maps directions error: {str(e)}")
            raise IntegrationError(
                f"Failed to get directions: {str(e)}",
                integration_name="googlemaps"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to get directions: {str(e)}",
                integration_name="googlemaps"
            )

    async def optimize_route(
        self,
        origin: str,
        destination: str,
        waypoints: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize route with multiple waypoints.

        Args:
            origin: Starting location
            destination: Ending location
            waypoints: List of waypoints to optimize

        Returns:
            dict: Optimized route with waypoint order

        Raises:
            IntegrationError: If route optimization fails
        """
        self._check_enabled()
        self.logger.info(f"Optimizing route with {len(waypoints)} waypoints")

        try:
            result = await self.get_directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                optimize_waypoints=True
            )

            return {
                "origin": origin,
                "destination": destination,
                "optimized_order": result['waypoint_order'],
                "total_distance": result['distance'],
                "total_duration": result['duration'],
                "waypoints_count": len(waypoints)
            }

        except Exception as e:
            raise IntegrationError(
                f"Failed to optimize route: {str(e)}",
                integration_name="googlemaps"
            )

    async def validate_address(self, address: str) -> Dict[str, Any]:
        """
        Validate if an address is valid and get standardized format.

        Args:
            address: Address to validate

        Returns:
            dict: Validation result with standardized address

        Raises:
            IntegrationError: If validation fails
        """
        self._check_enabled()
        self.logger.info(f"Validating address: {address}")

        try:
            geocode_result = await self.geocode(address)

            return {
                "valid": True,
                "original_address": address,
                "formatted_address": geocode_result['formatted_address'],
                "latitude": geocode_result['latitude'],
                "longitude": geocode_result['longitude'],
                "location_type": geocode_result['location_type']
            }

        except IntegrationError:
            return {
                "valid": False,
                "original_address": address,
                "error": "Could not validate address"
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get Google Maps client status.

        Returns:
            dict: Client configuration and status
        """
        return {
            "enabled": self.enabled,
            "configured": bool(self.api_key),
            "api_key": self.api_key[:12] + "..." if self.api_key else None,
            "capabilities": {
                "geocoding": self.enabled,
                "reverse_geocoding": self.enabled,
                "distance_matrix": self.enabled,
                "directions": self.enabled,
                "route_optimization": self.enabled
            }
        }
