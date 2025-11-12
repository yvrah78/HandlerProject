"""
Quote Service for Project Handler.
Generates instant transportation quotes using Google Maps and PricingService.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid

from src.core.logging import get_logger
from src.core.exceptions import ValidationError, IntegrationError
from src.models.quote import Quote, QuoteStatus
from src.models.customer import Customer
from src.services.pricing_service import PricingService
from src.integrations.google_maps_client import GoogleMapsClient

logger = get_logger(__name__)


class QuoteService:
    """
    Service for generating instant transportation quotes.

    Features:
    - Integration with Google Maps for accurate distance/time
    - Automatic price calculation using PricingService
    - Quote number generation
    - Validity period management
    - Database persistence
    """

    # Quote validity period (24 hours by default)
    QUOTE_VALIDITY_HOURS = 24

    def __init__(self, db: Session):
        """
        Initialize quote service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.pricing_service = PricingService()
        self.maps_client = GoogleMapsClient()
        self.logger = logger
        self.logger.info("QuoteService initialized")

    async def create_instant_quote(
        self,
        origin: str,
        destination: str,
        customer_id: int,
        service_type: str = "local",
        extra_passengers: int = 0,
        extra_luggage: int = 0,
        extra_stops: int = 0,
        waypoints: Optional[list] = None,
        scheduled_datetime: Optional[datetime] = None,
        cargo_description: Optional[str] = None,
        special_requirements: Optional[str] = None,
        promo_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an instant quote for transportation service.

        This method:
        1. Validates customer exists
        2. Geocodes addresses (if needed)
        3. Calculates route using Google Maps
        4. Calculates price using PricingService
        5. Creates Quote in database
        6. Returns quote details

        Args:
            origin: Starting address or coordinates
            destination: Ending address or coordinates
            customer_id: Customer ID
            service_type: Type of service (local, long_distance, airport, premium, express)
            extra_passengers: Number of extra passengers
            extra_luggage: Number of large luggage pieces
            extra_stops: Number of additional stops
            waypoints: List of waypoint addresses/coordinates (optional)
            scheduled_datetime: Scheduled pickup time (optional, defaults to now)
            cargo_description: Description of cargo (optional)
            special_requirements: Special requirements (optional)
            promo_code: Promotional code (optional)

        Returns:
            dict: Complete quote details with pricing breakdown

        Raises:
            ValidationError: If input validation fails
            IntegrationError: If Google Maps API fails
        """
        start_time = datetime.utcnow()

        # 1. Validate customer exists
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValidationError(f"Customer with ID {customer_id} not found")

        # Get customer's trip count for discount eligibility
        customer_trip_count = self._get_customer_trip_count(customer_id)

        # 2. Calculate route using Google Maps
        self.logger.info(f"Calculating route from '{origin}' to '{destination}'")

        try:
            # Get directions from Google Maps
            route_result = await self.maps_client.get_directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                optimize_waypoints=True if waypoints else False,
                departure_time=scheduled_datetime or datetime.now()
            )

            if not route_result or "error" in route_result:
                raise IntegrationError(
                    "Failed to calculate route",
                    integration_name="google_maps",
                    details=route_result
                )

            # Extract route information
            distance_km = route_result["distance_km"]
            duration_minutes = route_result["duration_minutes"]
            route_polyline = route_result.get("polyline")

        except Exception as e:
            self.logger.error(f"Google Maps API error: {str(e)}")
            raise IntegrationError(
                f"Failed to calculate route: {str(e)}",
                integration_name="google_maps"
            )

        # 3. Calculate price using PricingService
        self.logger.info(f"Calculating price for {distance_km}km, {duration_minutes}min")

        # Apply promo code discount if provided
        promo_discount = None
        if promo_code:
            promo_discount = self._validate_promo_code(promo_code)

        price_breakdown = self.pricing_service.calculate_price(
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            service_type=service_type,
            extra_passengers=extra_passengers,
            extra_luggage=extra_luggage,
            extra_stops=extra_stops,
            customer_trip_count=customer_trip_count,
            promo_discount_percent=promo_discount,
            scheduled_datetime=scheduled_datetime,
            apply_tax=True
        )

        # 4. Generate quote number
        quote_number = self._generate_quote_number()

        # 5. Create Quote in database
        valid_until = datetime.utcnow() + timedelta(hours=self.QUOTE_VALIDITY_HOURS)

        quote = Quote(
            customer_id=customer_id,
            quote_number=quote_number,
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            estimated_duration_minutes=duration_minutes,
            base_price=price_breakdown["base_price"],
            distance_price=price_breakdown["distance_price"],
            time_price=price_breakdown["time_price"],
            additional_fees=price_breakdown["additional_fees"],
            discount=price_breakdown["total_discount"],
            subtotal=price_breakdown["subtotal_after_discount"],
            tax_amount=price_breakdown["tax_amount"],
            total_amount=price_breakdown["total_amount"],
            pricing_details=price_breakdown,  # Store full breakdown as JSON
            cargo_description=cargo_description,
            special_requirements=special_requirements,
            status=QuoteStatus.DRAFT,
            valid_until=valid_until
        )

        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)

        # Calculate response time
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        self.logger.info(
            f"Quote {quote_number} created in {response_time_ms:.0f}ms: "
            f"${price_breakdown['total_amount']}"
        )

        # 6. Return complete quote details
        return {
            "quote_id": quote.id,
            "quote_number": quote_number,
            "status": quote.status.value,

            # Route information
            "origin": origin,
            "destination": destination,
            "distance_km": distance_km,
            "estimated_duration_minutes": duration_minutes,
            "route_polyline": route_polyline,

            # Pricing
            "pricing": price_breakdown,

            # Service details
            "service_type": service_type,
            "extra_passengers": extra_passengers,
            "extra_luggage": extra_luggage,
            "extra_stops": extra_stops,

            # Validity
            "valid_until": valid_until.isoformat(),
            "expires_in_hours": self.QUOTE_VALIDITY_HOURS,

            # Customer info
            "customer_id": customer_id,
            "customer_name": customer.name if customer.name else "Unknown",
            "customer_email": customer.email,

            # Metadata
            "created_at": quote.created_at.isoformat(),
            "response_time_ms": int(response_time_ms),
        }

    async def get_quote(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a quote by ID.

        Args:
            quote_id: Quote ID

        Returns:
            dict: Quote details or None if not found
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return None

        return self._quote_to_dict(quote)

    async def accept_quote(self, quote_id: int) -> Dict[str, Any]:
        """
        Accept a quote and mark it as accepted.

        Args:
            quote_id: Quote ID

        Returns:
            dict: Updated quote details

        Raises:
            ValidationError: If quote is expired or invalid status
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise ValidationError(f"Quote {quote_id} not found")

        # Check if quote is expired
        if quote.valid_until and quote.valid_until < datetime.utcnow():
            raise ValidationError("Quote has expired")

        # Check if quote is already accepted/rejected
        if quote.status in [QuoteStatus.ACCEPTED, QuoteStatus.REJECTED]:
            raise ValidationError(f"Quote is already {quote.status.value}")

        # Update status
        quote.status = QuoteStatus.ACCEPTED
        self.db.commit()
        self.db.refresh(quote)

        self.logger.info(f"Quote {quote.quote_number} accepted")

        return self._quote_to_dict(quote)

    async def reject_quote(self, quote_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a quote.

        Args:
            quote_id: Quote ID
            reason: Optional rejection reason

        Returns:
            dict: Updated quote details

        Raises:
            ValidationError: If quote not found or invalid status
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise ValidationError(f"Quote {quote_id} not found")

        if quote.status in [QuoteStatus.ACCEPTED, QuoteStatus.REJECTED]:
            raise ValidationError(f"Quote is already {quote.status.value}")

        # Update status
        quote.status = QuoteStatus.REJECTED
        if reason:
            if not quote.notes:
                quote.notes = f"Rejection reason: {reason}"
            else:
                quote.notes += f"\nRejection reason: {reason}"

        self.db.commit()
        self.db.refresh(quote)

        self.logger.info(f"Quote {quote.quote_number} rejected")

        return self._quote_to_dict(quote)

    def _generate_quote_number(self) -> str:
        """
        Generate a unique quote number.

        Format: QT-YYYYMMDD-XXXXX
        Example: QT-20251111-A1B2C
        """
        date_part = datetime.utcnow().strftime("%Y%m%d")
        unique_part = str(uuid.uuid4())[:5].upper()
        return f"QT-{date_part}-{unique_part}"

    def _get_customer_trip_count(self, customer_id: int) -> int:
        """
        Get the number of completed trips for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            int: Number of completed trips
        """
        # TODO: Implement once Booking model has completed trips tracking
        # For now, return 0
        return 0

    def _validate_promo_code(self, promo_code: str) -> Optional[float]:
        """
        Validate a promotional code and return discount percentage.

        Args:
            promo_code: Promo code to validate

        Returns:
            float: Discount percentage or None if invalid
        """
        # TODO: Implement promo code validation from database
        # For now, return some hardcoded promos for testing
        promo_codes = {
            "WELCOME10": 10.0,
            "SAVE20": 20.0,
            "VIP25": 25.0,
        }
        return promo_codes.get(promo_code.upper())

    def _quote_to_dict(self, quote: Quote) -> Dict[str, Any]:
        """
        Convert Quote model to dictionary.

        Args:
            quote: Quote model instance

        Returns:
            dict: Quote as dictionary
        """
        return {
            "quote_id": quote.id,
            "quote_number": quote.quote_number,
            "status": quote.status.value,
            "customer_id": quote.customer_id,
            "origin": quote.origin,
            "destination": quote.destination,
            "distance_km": quote.distance_km,
            "estimated_duration_minutes": quote.estimated_duration_minutes,
            "pricing": {
                "base_price": quote.base_price,
                "distance_price": quote.distance_price,
                "time_price": quote.time_price,
                "additional_fees": quote.additional_fees,
                "discount": quote.discount,
                "subtotal": quote.subtotal,
                "tax_amount": quote.tax_amount,
                "total_amount": quote.total_amount,
                "currency": "USD",
            },
            "pricing_details": quote.pricing_details,
            "cargo_description": quote.cargo_description,
            "special_requirements": quote.special_requirements,
            "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
            "created_at": quote.created_at.isoformat() if quote.created_at else None,
            "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
        }
