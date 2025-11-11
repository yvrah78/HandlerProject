"""
Google Maps integration client for Project Handler.
Handles geocoding, distance calculations, and routing via Google Maps API.

Rate Limits:
- Standard: 50 requests per second
- Daily quotas vary by API (Geocoding, Directions, etc.)
- Best practice: Use batch requests when possible

Documentation: https://developers.google.com/maps/documentation
"""
from typing import Optional, Dict, Any, List, Tuple
import googlemaps
from googlemaps.exceptions import ApiError, TransportError, Timeout

from src.core.config import get_settings
from src.core.exceptions import IntegrationError
from src.integrations.base import BaseIntegration

settings = get_settings()


class GoogleMapsClient(BaseIntegration):
    """
    Client for Google Maps API integration.

    Provides functionality for:
    - Geocoding (address to coordinates)
    - Reverse geocoding (coordinates to address)
    - Distance matrix calculations
    - Route optimization
    - Places search
    """

    def __init__(self):
        """Initialize Google Maps client with API key from settings."""
        super().__init__("google_maps")

        self.api_key = settings.google_maps_api_key

        # Validate configuration
        self._validate_config()

        # Initialize Google Maps client
        try:
            self.client = googlemaps.Client(key=self.api_key)
            self.logger.info("Google Maps client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Maps client: {str(e)}")
            raise IntegrationError(
                f"Failed to initialize Google Maps client: {str(e)}",
                integration_name=self.integration_name,
                details={"error": str(e)}
            )

    def _validate_config(self) -> None:
        """Validate that all required Google Maps configuration is present."""
        self._check_config_value(self.api_key, "GOOGLE_MAPS_API_KEY")

    async def geocode(self, address: str) -> Dict[str, Any]:
        """
        Convert address to geographic coordinates.

        Args:
            address: Street address to geocode

        Returns:
            dict: Location information including lat/lng and formatted address

        Raises:
            IntegrationError: If geocoding fails

        Example:
            >>> client = GoogleMapsClient()
            >>> result = await client.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
            >>> print(result["location"])  # {"lat": 37.4224428, "lng": -122.0842467}
        """
        self.logger.info(f"Geocoding address: {address}")

        async def _geocode():
            try:
                result = self.client.geocode(address)

                if not result:
                    raise IntegrationError(
                        f"No results found for address: {address}",
                        integration_name=self.integration_name,
                        details={"address": address}
                    )

                # Get first result
                location_data = result[0]
                geometry = location_data.get("geometry", {})
                location = geometry.get("location", {})

                response = {
                    "formatted_address": location_data.get("formatted_address"),
                    "location": {
                        "lat": location.get("lat"),
                        "lng": location.get("lng")
                    },
                    "place_id": location_data.get("place_id"),
                    "types": location_data.get("types", []),
                    "address_components": location_data.get("address_components", [])
                }

                self._log_api_call("geocode", {"address": address})
                return response

            except (ApiError, TransportError, Timeout) as e:
                self._log_api_call("geocode", {"address": address, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"Google Maps API error: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e), "address": address}
                )

        return await self._retry_on_failure(_geocode, max_retries=3)

    async def reverse_geocode(
        self,
        lat: float,
        lng: float
    ) -> Dict[str, Any]:
        """
        Convert geographic coordinates to address.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            dict: Address information

        Raises:
            IntegrationError: If reverse geocoding fails

        Example:
            >>> client = GoogleMapsClient()
            >>> result = await client.reverse_geocode(37.4224428, -122.0842467)
            >>> print(result["formatted_address"])
        """
        self.logger.info(f"Reverse geocoding coordinates: ({lat}, {lng})")

        async def _reverse_geocode():
            try:
                result = self.client.reverse_geocode((lat, lng))

                if not result:
                    raise IntegrationError(
                        f"No results found for coordinates: ({lat}, {lng})",
                        integration_name=self.integration_name,
                        details={"lat": lat, "lng": lng}
                    )

                # Get first result
                location_data = result[0]

                response = {
                    "formatted_address": location_data.get("formatted_address"),
                    "place_id": location_data.get("place_id"),
                    "types": location_data.get("types", []),
                    "address_components": location_data.get("address_components", [])
                }

                self._log_api_call("reverse_geocode", {"lat": lat, "lng": lng})
                return response

            except (ApiError, TransportError, Timeout) as e:
                self._log_api_call(
                    "reverse_geocode",
                    {"lat": lat, "lng": lng, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Google Maps API error: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e), "lat": lat, "lng": lng}
                )

        return await self._retry_on_failure(_reverse_geocode, max_retries=3)

    async def calculate_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving",
        units: str = "imperial"
    ) -> Dict[str, Any]:
        """
        Calculate distance and duration between multiple origins and destinations.

        Args:
            origins: List of origin addresses or coordinates
            destinations: List of destination addresses or coordinates
            mode: Travel mode ("driving", "walking", "bicycling", "transit")
            units: Unit system ("metric" or "imperial")

        Returns:
            dict: Distance matrix with distances and durations

        Raises:
            IntegrationError: If distance calculation fails

        Example:
            >>> client = GoogleMapsClient()
            >>> result = await client.calculate_distance_matrix(
            ...     origins=["New York, NY"],
            ...     destinations=["Los Angeles, CA"],
            ...     mode="driving"
            ... )
        """
        self.logger.info(f"Calculating distance matrix: {len(origins)} origins to {len(destinations)} destinations")

        async def _calculate():
            try:
                result = self.client.distance_matrix(
                    origins=origins,
                    destinations=destinations,
                    mode=mode,
                    units=units
                )

                response = {
                    "origin_addresses": result.get("origin_addresses", []),
                    "destination_addresses": result.get("destination_addresses", []),
                    "rows": []
                }

                # Parse rows
                for row in result.get("rows", []):
                    elements = []
                    for element in row.get("elements", []):
                        elements.append({
                            "status": element.get("status"),
                            "distance": {
                                "text": element.get("distance", {}).get("text"),
                                "value": element.get("distance", {}).get("value")  # in meters
                            } if "distance" in element else None,
                            "duration": {
                                "text": element.get("duration", {}).get("text"),
                                "value": element.get("duration", {}).get("value")  # in seconds
                            } if "duration" in element else None
                        })
                    response["rows"].append({"elements": elements})

                self._log_api_call(
                    "calculate_distance_matrix",
                    {"origins_count": len(origins), "destinations_count": len(destinations)}
                )
                return response

            except (ApiError, TransportError, Timeout) as e:
                self._log_api_call(
                    "calculate_distance_matrix",
                    {"error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Google Maps API error: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_calculate, max_retries=3)

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
        Get directions between two points.

        Args:
            origin: Starting point address or coordinates
            destination: Ending point address or coordinates
            mode: Travel mode ("driving", "walking", "bicycling", "transit")
            waypoints: Optional list of waypoint addresses
            optimize_waypoints: Optimize waypoint order
            alternatives: Return alternative routes

        Returns:
            dict: Route information with steps and distance

        Raises:
            IntegrationError: If directions request fails

        Example:
            >>> client = GoogleMapsClient()
            >>> result = await client.get_directions(
            ...     origin="New York, NY",
            ...     destination="Boston, MA",
            ...     mode="driving"
            ... )
        """
        self.logger.info(f"Getting directions from {origin} to {destination}")

        async def _get_directions():
            try:
                params = {
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "alternatives": alternatives
                }

                if waypoints:
                    params["waypoints"] = waypoints
                    params["optimize_waypoints"] = optimize_waypoints

                result = self.client.directions(**params)

                if not result:
                    raise IntegrationError(
                        f"No routes found from {origin} to {destination}",
                        integration_name=self.integration_name,
                        details={"origin": origin, "destination": destination}
                    )

                routes = []
                for route in result:
                    leg = route["legs"][0]  # Get first leg
                    routes.append({
                        "summary": route.get("summary"),
                        "distance": {
                            "text": leg.get("distance", {}).get("text"),
                            "value": leg.get("distance", {}).get("value")
                        },
                        "duration": {
                            "text": leg.get("duration", {}).get("text"),
                            "value": leg.get("duration", {}).get("value")
                        },
                        "start_address": leg.get("start_address"),
                        "end_address": leg.get("end_address"),
                        "steps": [
                            {
                                "instruction": step.get("html_instructions"),
                                "distance": step.get("distance"),
                                "duration": step.get("duration")
                            }
                            for step in leg.get("steps", [])
                        ],
                        "waypoint_order": route.get("waypoint_order", [])
                    })

                response = {
                    "routes": routes,
                    "origin": origin,
                    "destination": destination
                }

                self._log_api_call("get_directions", {"origin": origin, "destination": destination})
                return response

            except (ApiError, TransportError, Timeout) as e:
                self._log_api_call(
                    "get_directions",
                    {"origin": origin, "destination": destination, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Google Maps API error: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_get_directions, max_retries=3)

    async def search_places(
        self,
        query: str,
        location: Optional[Tuple[float, float]] = None,
        radius: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for places by text query.

        Args:
            query: Search query (e.g., "restaurants near me")
            location: Optional (lat, lng) tuple to bias results
            radius: Optional radius in meters

        Returns:
            list: List of place results

        Raises:
            IntegrationError: If search fails

        Example:
            >>> client = GoogleMapsClient()
            >>> result = await client.search_places(
            ...     query="coffee shops",
            ...     location=(37.4224428, -122.0842467),
            ...     radius=5000
            ... )
        """
        self.logger.info(f"Searching places: {query}")

        async def _search():
            try:
                params = {"query": query}

                if location:
                    params["location"] = location

                if radius:
                    params["radius"] = radius

                result = self.client.places(**params)

                places = []
                for place in result.get("results", []):
                    geometry = place.get("geometry", {})
                    location_data = geometry.get("location", {})

                    places.append({
                        "name": place.get("name"),
                        "formatted_address": place.get("formatted_address"),
                        "place_id": place.get("place_id"),
                        "location": {
                            "lat": location_data.get("lat"),
                            "lng": location_data.get("lng")
                        },
                        "rating": place.get("rating"),
                        "types": place.get("types", []),
                        "price_level": place.get("price_level")
                    })

                self._log_api_call("search_places", {"query": query, "results_count": len(places)})
                return places

            except (ApiError, TransportError, Timeout) as e:
                self._log_api_call("search_places", {"query": query, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"Google Maps API error: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e), "query": query}
                )

        return await self._retry_on_failure(_search, max_retries=3)
