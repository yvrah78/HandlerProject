"""
Pricing Service for Project Handler.
Calculates transportation prices based on multiple factors.
"""
from typing import Dict, Any, Optional
from datetime import datetime, time
from decimal import Decimal

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class PricingService:
    """
    Service for calculating transportation pricing.

    Pricing factors:
    - Base price (minimum charge)
    - Distance-based pricing
    - Time-based pricing
    - Service type multipliers
    - Surge pricing (peak hours)
    - Additional fees (extra passengers, luggage, stops)
    - Discounts (frequent customers, promotions)
    - Taxes (configurable by region)
    """

    # Base pricing configuration (USD)
    BASE_PRICE = Decimal("15.00")  # Minimum charge
    PRICE_PER_KM = Decimal("1.50")  # Price per kilometer
    PRICE_PER_MINUTE = Decimal("0.35")  # Price per minute of travel

    # Service type multipliers
    SERVICE_MULTIPLIERS = {
        "local": Decimal("1.0"),
        "long_distance": Decimal("0.9"),  # Slight discount for long trips
        "airport": Decimal("1.2"),  # Premium for airport service
        "premium": Decimal("1.5"),  # Premium vehicles
        "express": Decimal("1.3"),  # Express service
    }

    # Additional fees
    EXTRA_PASSENGER_FEE = Decimal("5.00")  # Per passenger above standard
    EXTRA_LUGGAGE_FEE = Decimal("3.00")  # Per large luggage piece
    EXTRA_STOP_FEE = Decimal("8.00")  # Per additional stop
    WAITING_TIME_FEE = Decimal("0.50")  # Per minute of waiting

    # Peak hours configuration
    PEAK_HOURS = [
        (time(7, 0), time(9, 30)),   # Morning rush
        (time(17, 0), time(19, 30)), # Evening rush
    ]
    SURGE_MULTIPLIER = Decimal("1.3")  # 30% surge during peak hours

    # Weekend multiplier
    WEEKEND_MULTIPLIER = Decimal("1.1")  # 10% extra on weekends

    # Tax rate (configurable by region)
    TAX_RATE = Decimal("0.08")  # 8% tax

    # Discount thresholds
    FREQUENT_CUSTOMER_DISCOUNT = Decimal("0.10")  # 10% off
    FREQUENT_CUSTOMER_MIN_TRIPS = 10

    def __init__(self):
        """Initialize pricing service."""
        self.logger = logger
        self.logger.info("PricingService initialized")

    def calculate_price(
        self,
        distance_km: float,
        duration_minutes: int,
        service_type: str = "local",
        extra_passengers: int = 0,
        extra_luggage: int = 0,
        extra_stops: int = 0,
        waiting_minutes: int = 0,
        customer_trip_count: int = 0,
        promo_discount_percent: Optional[float] = None,
        scheduled_datetime: Optional[datetime] = None,
        apply_tax: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate the total price for a transportation service.

        Args:
            distance_km: Distance in kilometers
            duration_minutes: Estimated duration in minutes
            service_type: Type of service (local, long_distance, airport, premium, express)
            extra_passengers: Number of passengers beyond standard capacity
            extra_luggage: Number of large luggage pieces
            extra_stops: Number of additional stops
            waiting_minutes: Expected waiting time in minutes
            customer_trip_count: Number of previous trips by customer
            promo_discount_percent: Promotional discount percentage (0-100)
            scheduled_datetime: Scheduled date/time for the trip (for surge pricing)
            apply_tax: Whether to apply tax

        Returns:
            dict: Detailed price breakdown

        Example:
            >>> service = PricingService()
            >>> result = service.calculate_price(
            ...     distance_km=15.5,
            ...     duration_minutes=25,
            ...     service_type="local",
            ...     extra_passengers=1
            ... )
            >>> print(result['total_amount'])
        """
        # Convert to Decimal for precise calculations
        distance = Decimal(str(distance_km))
        duration = Decimal(str(duration_minutes))

        # 1. Calculate base components
        base_price = self.BASE_PRICE
        distance_price = distance * self.PRICE_PER_KM
        time_price = duration * self.PRICE_PER_MINUTE

        # 2. Apply service type multiplier
        service_multiplier = self.SERVICE_MULTIPLIERS.get(
            service_type.lower(),
            Decimal("1.0")
        )

        # Subtotal before multipliers
        subtotal = base_price + distance_price + time_price

        # Apply service type multiplier
        subtotal_with_service = subtotal * service_multiplier

        # 3. Calculate additional fees
        additional_fees = Decimal("0")
        fees_breakdown = {}

        if extra_passengers > 0:
            passenger_fee = Decimal(str(extra_passengers)) * self.EXTRA_PASSENGER_FEE
            additional_fees += passenger_fee
            fees_breakdown["extra_passengers"] = float(passenger_fee)

        if extra_luggage > 0:
            luggage_fee = Decimal(str(extra_luggage)) * self.EXTRA_LUGGAGE_FEE
            additional_fees += luggage_fee
            fees_breakdown["extra_luggage"] = float(luggage_fee)

        if extra_stops > 0:
            stops_fee = Decimal(str(extra_stops)) * self.EXTRA_STOP_FEE
            additional_fees += stops_fee
            fees_breakdown["extra_stops"] = float(stops_fee)

        if waiting_minutes > 0:
            waiting_fee = Decimal(str(waiting_minutes)) * self.WAITING_TIME_FEE
            additional_fees += waiting_fee
            fees_breakdown["waiting_time"] = float(waiting_fee)

        # 4. Calculate surge pricing (if scheduled datetime provided)
        surge_multiplier = Decimal("1.0")
        is_peak_hour = False
        is_weekend = False

        if scheduled_datetime:
            # Check for peak hours
            scheduled_time = scheduled_datetime.time()
            for start_time, end_time in self.PEAK_HOURS:
                if start_time <= scheduled_time <= end_time:
                    is_peak_hour = True
                    surge_multiplier *= self.SURGE_MULTIPLIER
                    break

            # Check for weekend
            if scheduled_datetime.weekday() >= 5:  # Saturday = 5, Sunday = 6
                is_weekend = True
                surge_multiplier *= self.WEEKEND_MULTIPLIER

        # Apply surge to subtotal
        subtotal_with_surge = subtotal_with_service * surge_multiplier

        # 5. Add additional fees
        subtotal_before_discount = subtotal_with_surge + additional_fees

        # 6. Calculate discounts
        total_discount = Decimal("0")
        discounts_breakdown = {}

        # Frequent customer discount
        if customer_trip_count >= self.FREQUENT_CUSTOMER_MIN_TRIPS:
            frequent_discount = subtotal_before_discount * self.FREQUENT_CUSTOMER_DISCOUNT
            total_discount += frequent_discount
            discounts_breakdown["frequent_customer"] = float(frequent_discount)

        # Promotional discount
        if promo_discount_percent and promo_discount_percent > 0:
            promo_discount = subtotal_before_discount * (Decimal(str(promo_discount_percent)) / Decimal("100"))
            total_discount += promo_discount
            discounts_breakdown["promotional"] = float(promo_discount)

        # 7. Calculate subtotal after discounts
        subtotal_after_discount = subtotal_before_discount - total_discount

        # 8. Calculate tax
        tax_amount = Decimal("0")
        if apply_tax:
            tax_amount = subtotal_after_discount * self.TAX_RATE

        # 9. Calculate final total
        total_amount = subtotal_after_discount + tax_amount

        # Round to 2 decimal places
        total_amount = total_amount.quantize(Decimal("0.01"))

        # Log the calculation
        self.logger.info(
            f"Price calculated: {distance_km}km, {duration_minutes}min, "
            f"{service_type}, total=${float(total_amount)}"
        )

        # Return detailed breakdown
        return {
            # Base components
            "base_price": float(base_price),
            "distance_price": float(distance_price),
            "time_price": float(time_price),
            "distance_km": float(distance),
            "duration_minutes": float(duration),

            # Service details
            "service_type": service_type,
            "service_multiplier": float(service_multiplier),

            # Surge pricing
            "surge_multiplier": float(surge_multiplier),
            "is_peak_hour": is_peak_hour,
            "is_weekend": is_weekend,

            # Additional fees
            "additional_fees": float(additional_fees),
            "fees_breakdown": fees_breakdown,

            # Discounts
            "total_discount": float(total_discount),
            "discounts_breakdown": discounts_breakdown,

            # Subtotals
            "subtotal_before_fees": float(subtotal_with_service * surge_multiplier),
            "subtotal_before_discount": float(subtotal_before_discount),
            "subtotal_after_discount": float(subtotal_after_discount),

            # Tax and total
            "tax_rate": float(self.TAX_RATE),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),

            # Metadata
            "currency": "USD",
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def estimate_price_range(
        self,
        min_distance_km: float,
        max_distance_km: float,
        service_type: str = "local"
    ) -> Dict[str, float]:
        """
        Estimate a price range for a service.

        Useful for providing quick estimates before exact route calculation.

        Args:
            min_distance_km: Minimum distance estimate
            max_distance_km: Maximum distance estimate
            service_type: Type of service

        Returns:
            dict: Price range with min and max
        """
        # Estimate duration based on average speed (40 km/h in city)
        avg_speed_kmh = 40
        min_duration_minutes = int((min_distance_km / avg_speed_kmh) * 60)
        max_duration_minutes = int((max_distance_km / avg_speed_kmh) * 60)

        # Calculate minimum price
        min_price_result = self.calculate_price(
            distance_km=min_distance_km,
            duration_minutes=min_duration_minutes,
            service_type=service_type,
            apply_tax=True
        )

        # Calculate maximum price (with potential surge)
        max_price_result = self.calculate_price(
            distance_km=max_distance_km,
            duration_minutes=max_duration_minutes,
            service_type=service_type,
            scheduled_datetime=datetime.now().replace(hour=18, minute=0),  # Peak hour
            apply_tax=True
        )

        return {
            "min_price": min_price_result["total_amount"],
            "max_price": max_price_result["total_amount"],
            "currency": "USD",
            "service_type": service_type
        }

    def get_pricing_info(self) -> Dict[str, Any]:
        """
        Get current pricing configuration.

        Returns:
            dict: Current pricing rules and rates
        """
        return {
            "base_price": float(self.BASE_PRICE),
            "price_per_km": float(self.PRICE_PER_KM),
            "price_per_minute": float(self.PRICE_PER_MINUTE),
            "service_multipliers": {k: float(v) for k, v in self.SERVICE_MULTIPLIERS.items()},
            "additional_fees": {
                "extra_passenger": float(self.EXTRA_PASSENGER_FEE),
                "extra_luggage": float(self.EXTRA_LUGGAGE_FEE),
                "extra_stop": float(self.EXTRA_STOP_FEE),
                "waiting_time_per_minute": float(self.WAITING_TIME_FEE),
            },
            "surge_pricing": {
                "peak_hours": [(s.isoformat(), e.isoformat()) for s, e in self.PEAK_HOURS],
                "surge_multiplier": float(self.SURGE_MULTIPLIER),
                "weekend_multiplier": float(self.WEEKEND_MULTIPLIER),
            },
            "discounts": {
                "frequent_customer_discount": float(self.FREQUENT_CUSTOMER_DISCOUNT),
                "frequent_customer_min_trips": self.FREQUENT_CUSTOMER_MIN_TRIPS,
            },
            "tax_rate": float(self.TAX_RATE),
            "currency": "USD",
        }
