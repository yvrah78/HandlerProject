"""
Integration tests for Google Maps client.

These tests use mocking to avoid actual API calls during testing.
For real integration testing with Google Maps credentials, set:
- GOOGLE_MAPS_API_KEY to your API key
"""
import pytest
from unittest.mock import Mock, patch

from src.integrations.google_maps_client import GoogleMapsClient
from src.core.exceptions import IntegrationError, ConfigurationError


class TestGoogleMapsClient:
    """Test suite for Google Maps client."""

    @pytest.fixture
    def mock_gmaps_settings(self):
        """Mock settings with Google Maps credentials."""
        with patch('src.integrations.google_maps_client.settings') as mock_settings:
            mock_settings.google_maps_api_key = "AIza_test_key_123"
            yield mock_settings

    @pytest.fixture
    def mock_gmaps_client(self):
        """Mock Google Maps Client."""
        with patch('src.integrations.google_maps_client.googlemaps.Client') as mock_client:
            yield mock_client

    @pytest.mark.asyncio
    async def test_init_success(self, mock_gmaps_settings, mock_gmaps_client):
        """Test successful Google Maps client initialization."""
        client = GoogleMapsClient()

        assert client.api_key == "AIza_test_key_123"
        mock_gmaps_client.assert_called_once_with(key="AIza_test_key_123")

    @pytest.mark.asyncio
    async def test_init_missing_credentials(self):
        """Test initialization fails with missing credentials."""
        with patch('src.integrations.google_maps_client.settings') as mock_settings:
            mock_settings.google_maps_api_key = ""

            with pytest.raises(ConfigurationError) as exc_info:
                GoogleMapsClient()

            assert "GOOGLE_MAPS_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_geocode_success(self, mock_gmaps_settings, mock_gmaps_client):
        """Test successful geocoding."""
        # Setup mock geocode response
        mock_result = [{
            "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
            "geometry": {
                "location": {
                    "lat": 37.4224428,
                    "lng": -122.0842467
                }
            },
            "place_id": "ChIJtYuu0V25j4ARwu5e4wwRYgE",
            "types": ["street_address"],
            "address_components": []
        }]

        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = mock_result
        mock_gmaps_client.return_value = mock_client_instance

        # Create client and geocode
        client = GoogleMapsClient()
        result = await client.geocode("1600 Amphitheatre Parkway, Mountain View, CA")

        # Assertions
        assert result["formatted_address"] == "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"
        assert result["location"]["lat"] == 37.4224428
        assert result["location"]["lng"] == -122.0842467
        assert result["place_id"] == "ChIJtYuu0V25j4ARwu5e4wwRYgE"

    @pytest.mark.asyncio
    async def test_geocode_no_results(self, mock_gmaps_settings, mock_gmaps_client):
        """Test geocoding with no results."""
        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = []
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.geocode("invalid address xyz123")

        assert "No results found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reverse_geocode_success(self, mock_gmaps_settings, mock_gmaps_client):
        """Test successful reverse geocoding."""
        mock_result = [{
            "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
            "place_id": "ChIJtYuu0V25j4ARwu5e4wwRYgE",
            "types": ["street_address"],
            "address_components": []
        }]

        mock_client_instance = Mock()
        mock_client_instance.reverse_geocode.return_value = mock_result
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()
        result = await client.reverse_geocode(37.4224428, -122.0842467)

        assert result["formatted_address"] == "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"
        assert result["place_id"] == "ChIJtYuu0V25j4ARwu5e4wwRYgE"

    @pytest.mark.asyncio
    async def test_calculate_distance_matrix_success(self, mock_gmaps_settings, mock_gmaps_client):
        """Test successful distance matrix calculation."""
        mock_result = {
            "origin_addresses": ["New York, NY, USA"],
            "destination_addresses": ["Los Angeles, CA, USA"],
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {
                        "text": "2,789 mi",
                        "value": 4487363
                    },
                    "duration": {
                        "text": "1 day 17 hours",
                        "value": 148038
                    }
                }]
            }]
        }

        mock_client_instance = Mock()
        mock_client_instance.distance_matrix.return_value = mock_result
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()
        result = await client.calculate_distance_matrix(
            origins=["New York, NY"],
            destinations=["Los Angeles, CA"]
        )

        assert result["origin_addresses"][0] == "New York, NY, USA"
        assert result["destination_addresses"][0] == "Los Angeles, CA, USA"
        assert result["rows"][0]["elements"][0]["status"] == "OK"
        assert result["rows"][0]["elements"][0]["distance"]["value"] == 4487363
        assert result["rows"][0]["elements"][0]["duration"]["value"] == 148038

    @pytest.mark.asyncio
    async def test_get_directions_success(self, mock_gmaps_settings, mock_gmaps_client):
        """Test successful directions retrieval."""
        mock_result = [{
            "summary": "I-95 N",
            "legs": [{
                "distance": {
                    "text": "215 mi",
                    "value": 346076
                },
                "duration": {
                    "text": "3 hours 30 mins",
                    "value": 12600
                },
                "start_address": "New York, NY, USA",
                "end_address": "Boston, MA, USA",
                "steps": [
                    {
                        "html_instructions": "Head <b>northeast</b> on <b>Broadway</b>",
                        "distance": {"text": "0.2 mi", "value": 322},
                        "duration": {"text": "1 min", "value": 60}
                    }
                ]
            }],
            "waypoint_order": []
        }]

        mock_client_instance = Mock()
        mock_client_instance.directions.return_value = mock_result
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()
        result = await client.get_directions(
            origin="New York, NY",
            destination="Boston, MA"
        )

        assert result["origin"] == "New York, NY"
        assert result["destination"] == "Boston, MA"
        assert len(result["routes"]) == 1
        assert result["routes"][0]["summary"] == "I-95 N"
        assert result["routes"][0]["distance"]["value"] == 346076
        assert result["routes"][0]["duration"]["value"] == 12600

    @pytest.mark.asyncio
    async def test_get_directions_with_waypoints(self, mock_gmaps_settings, mock_gmaps_client):
        """Test directions with waypoints."""
        mock_result = [{
            "summary": "I-95 N",
            "legs": [{
                "distance": {"text": "215 mi", "value": 346076},
                "duration": {"text": "3 hours 30 mins", "value": 12600},
                "start_address": "New York, NY, USA",
                "end_address": "Boston, MA, USA",
                "steps": []
            }],
            "waypoint_order": [0]
        }]

        mock_client_instance = Mock()
        mock_client_instance.directions.return_value = mock_result
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()
        result = await client.get_directions(
            origin="New York, NY",
            destination="Boston, MA",
            waypoints=["Philadelphia, PA"],
            optimize_waypoints=True
        )

        assert len(result["routes"]) == 1
        assert result["routes"][0]["waypoint_order"] == [0]

    @pytest.mark.asyncio
    async def test_search_places_success(self, mock_gmaps_settings, mock_gmaps_client):
        """Test successful places search."""
        mock_result = {
            "results": [
                {
                    "name": "Starbucks",
                    "formatted_address": "123 Main St, City, State 12345",
                    "place_id": "ChIJtest123",
                    "geometry": {
                        "location": {
                            "lat": 37.4224428,
                            "lng": -122.0842467
                        }
                    },
                    "rating": 4.5,
                    "types": ["cafe", "food"],
                    "price_level": 2
                },
                {
                    "name": "Peet's Coffee",
                    "formatted_address": "456 Oak Ave, City, State 12345",
                    "place_id": "ChIJtest456",
                    "geometry": {
                        "location": {
                            "lat": 37.4234428,
                            "lng": -122.0852467
                        }
                    },
                    "rating": 4.3,
                    "types": ["cafe", "food"],
                    "price_level": 2
                }
            ]
        }

        mock_client_instance = Mock()
        mock_client_instance.places.return_value = mock_result
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()
        result = await client.search_places(
            query="coffee shops",
            location=(37.4224428, -122.0842467),
            radius=5000
        )

        assert len(result) == 2
        assert result[0]["name"] == "Starbucks"
        assert result[0]["rating"] == 4.5
        assert result[0]["location"]["lat"] == 37.4224428
        assert result[1]["name"] == "Peet's Coffee"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_gmaps_settings, mock_gmaps_client):
        """Test handling of Google Maps API errors."""
        from googlemaps.exceptions import ApiError

        mock_client_instance = Mock()
        mock_client_instance.geocode.side_effect = ApiError("API_KEY_INVALID")
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.geocode("123 Main St")

        assert "Google Maps API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_gmaps_settings, mock_gmaps_client):
        """Test retry logic on transient failures."""
        from googlemaps.exceptions import TransportError

        # Setup mock to fail twice then succeed
        mock_result = [{
            "formatted_address": "123 Main St",
            "geometry": {"location": {"lat": 37.4224428, "lng": -122.0842467}},
            "place_id": "ChIJtest123",
            "types": ["street_address"],
            "address_components": []
        }]

        mock_client_instance = Mock()
        mock_client_instance.geocode.side_effect = [
            TransportError("Connection timeout"),
            TransportError("Connection timeout"),
            mock_result
        ]
        mock_gmaps_client.return_value = mock_client_instance

        client = GoogleMapsClient()

        # Should succeed after retries
        result = await client.geocode("123 Main St")

        assert result["formatted_address"] == "123 Main St"
        # Should have been called 3 times (initial + 2 retries)
        assert mock_client_instance.geocode.call_count == 3
