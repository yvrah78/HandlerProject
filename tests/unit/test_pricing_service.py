"""
Unit tests for PricingService.
"""
import pytest
from datetime import datetime, time
from src.services.pricing_service import PricingService


class TestPricingService:
    """Test cases for PricingService."""

    @pytest.fixture
    def pricing_service(self):
        """Create a PricingService instance for testing."""
        return PricingService()

    def test_basic_price_calculation(self, pricing_service):
        """Test basic price calculation without extras."""
        result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20
        )

        assert result["distance_km"] == 10.0
        assert result["duration_minutes"] == 20
        assert result["base_price"] == 15.0
        assert result["distance_price"] == 15.0  # 10 km * $1.50
        assert result["time_price"] == 7.0  # 20 min * $0.35
        assert result["total_amount"] > 0
        assert result["currency"] == "USD"

    def test_service_type_multiplier(self, pricing_service):
        """Test that service type multipliers are applied correctly."""
        # Local service (1.0x)
        local_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            service_type="local"
        )

        # Premium service (1.5x)
        premium_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            service_type="premium"
        )

        # Premium should cost more
        assert premium_result["total_amount"] > local_result["total_amount"]
        assert premium_result["service_multiplier"] == 1.5

    def test_extra_passengers_fee(self, pricing_service):
        """Test that extra passenger fees are applied."""
        base_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20
        )

        with_passengers_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            extra_passengers=2
        )

        # Should have additional fee of $10 (2 passengers * $5)
        expected_diff = 2 * 5.0  # EXTRA_PASSENGER_FEE
        # Need to account for tax
        actual_diff = with_passengers_result["total_amount"] - base_result["total_amount"]
        assert abs(actual_diff - expected_diff * 1.08) < 0.01  # 8% tax

    def test_extra_luggage_fee(self, pricing_service):
        """Test that extra luggage fees are applied."""
        base_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20
        )

        with_luggage_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            extra_luggage=3
        )

        # Should have additional fee of $9 (3 pieces * $3)
        assert with_luggage_result["fees_breakdown"]["extra_luggage"] == 9.0
        assert with_luggage_result["total_amount"] > base_result["total_amount"]

    def test_surge_pricing_peak_hours(self, pricing_service):
        """Test that surge pricing is applied during peak hours."""
        # Morning rush hour (7:00-9:30 AM)
        peak_datetime = datetime(2025, 11, 11, 8, 0)  # 8 AM

        result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            scheduled_datetime=peak_datetime
        )

        assert result["is_peak_hour"] is True
        assert result["surge_multiplier"] > 1.0

    def test_weekend_multiplier(self, pricing_service):
        """Test that weekend multiplier is applied."""
        # Saturday
        weekend_datetime = datetime(2025, 11, 15, 14, 0)  # Saturday

        result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            scheduled_datetime=weekend_datetime
        )

        assert result["is_weekend"] is True
        assert result["surge_multiplier"] >= 1.1  # Weekend multiplier

    def test_frequent_customer_discount(self, pricing_service):
        """Test that frequent customer discount is applied."""
        # Regular customer
        regular_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            customer_trip_count=5
        )

        # Frequent customer (10+ trips)
        frequent_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            customer_trip_count=15
        )

        assert "frequent_customer" in frequent_result["discounts_breakdown"]
        assert frequent_result["total_amount"] < regular_result["total_amount"]

    def test_promotional_discount(self, pricing_service):
        """Test that promotional discount is applied."""
        base_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20
        )

        promo_result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            promo_discount_percent=20.0
        )

        assert "promotional" in promo_result["discounts_breakdown"]
        assert promo_result["total_amount"] < base_result["total_amount"]

    def test_tax_calculation(self, pricing_service):
        """Test that tax is calculated correctly."""
        result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            apply_tax=True
        )

        # Tax should be 8% of subtotal
        expected_tax = result["subtotal_after_discount"] * 0.08
        assert abs(result["tax_amount"] - expected_tax) < 0.01

    def test_no_tax_option(self, pricing_service):
        """Test that tax can be disabled."""
        result = pricing_service.calculate_price(
            distance_km=10.0,
            duration_minutes=20,
            apply_tax=False
        )

        assert result["tax_amount"] == 0.0

    def test_price_range_estimation(self, pricing_service):
        """Test price range estimation."""
        result = pricing_service.estimate_price_range(
            min_distance_km=5.0,
            max_distance_km=15.0,
            service_type="local"
        )

        assert "min_price" in result
        assert "max_price" in result
        assert result["max_price"] > result["min_price"]
        assert result["currency"] == "USD"

    def test_get_pricing_info(self, pricing_service):
        """Test getting pricing configuration."""
        info = pricing_service.get_pricing_info()

        assert "base_price" in info
        assert "price_per_km" in info
        assert "price_per_minute" in info
        assert "service_multipliers" in info
        assert "surge_pricing" in info
        assert "tax_rate" in info
        assert info["currency"] == "USD"

    def test_complex_calculation(self, pricing_service):
        """Test complex calculation with multiple factors."""
        # Peak hour, weekend, with extras
        complex_datetime = datetime(2025, 11, 15, 8, 0)  # Saturday, 8 AM

        result = pricing_service.calculate_price(
            distance_km=25.5,
            duration_minutes=45,
            service_type="premium",
            extra_passengers=2,
            extra_luggage=1,
            extra_stops=1,
            customer_trip_count=12,  # Frequent customer
            promo_discount_percent=10.0,
            scheduled_datetime=complex_datetime,
            apply_tax=True
        )

        # Should have all components
        assert result["base_price"] > 0
        assert result["distance_price"] > 0
        assert result["time_price"] > 0
        assert result["additional_fees"] > 0
        assert result["total_discount"] > 0
        assert result["tax_amount"] > 0
        assert result["total_amount"] > 0

        # Should have surge pricing
        assert result["surge_multiplier"] > 1.0
        assert result["is_peak_hour"] is True
        assert result["is_weekend"] is True

        # Should have discounts
        assert "frequent_customer" in result["discounts_breakdown"]
        assert "promotional" in result["discounts_breakdown"]

    def test_zero_distance(self, pricing_service):
        """Test that base price is charged even with zero distance."""
        result = pricing_service.calculate_price(
            distance_km=0.0,
            duration_minutes=5
        )

        # Should still have base price
        assert result["total_amount"] >= result["base_price"]

    def test_long_distance_discount(self, pricing_service):
        """Test that long distance trips have lower rate."""
        local_result = pricing_service.calculate_price(
            distance_km=50.0,
            duration_minutes=60,
            service_type="local"
        )

        long_distance_result = pricing_service.calculate_price(
            distance_km=50.0,
            duration_minutes=60,
            service_type="long_distance"
        )

        # Long distance should be cheaper (0.9x multiplier)
        assert long_distance_result["total_amount"] < local_result["total_amount"]
