"""
Quote API endpoints for Project Handler.
Handles instant quote generation and management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from src.core.database import get_db
from src.core.logging import get_logger
from src.core.exceptions import ValidationError, IntegrationError
from src.services.quote_service import QuoteService
from src.services.pricing_service import PricingService

logger = get_logger(__name__)
router = APIRouter(prefix="/quotes", tags=["quotes"])


# Request/Response Schemas

class InstantQuoteRequest(BaseModel):
    """Request schema for instant quote generation."""
    origin: str = Field(..., description="Starting address or coordinates")
    destination: str = Field(..., description="Ending address or coordinates")
    customer_id: int = Field(..., description="Customer ID", gt=0)
    service_type: str = Field(
        default="local",
        description="Type of service: local, long_distance, airport, premium, express"
    )
    extra_passengers: int = Field(default=0, ge=0, description="Number of extra passengers")
    extra_luggage: int = Field(default=0, ge=0, description="Number of large luggage pieces")
    extra_stops: int = Field(default=0, ge=0, description="Number of additional stops")
    waypoints: Optional[List[str]] = Field(default=None, description="List of waypoint addresses")
    scheduled_datetime: Optional[datetime] = Field(
        default=None,
        description="Scheduled pickup time (ISO format)"
    )
    cargo_description: Optional[str] = Field(default=None, max_length=1000)
    special_requirements: Optional[str] = Field(default=None, max_length=500)
    promo_code: Optional[str] = Field(default=None, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "origin": "123 Main St, New York, NY",
                "destination": "456 Park Ave, New York, NY",
                "customer_id": 1,
                "service_type": "local",
                "extra_passengers": 1,
                "scheduled_datetime": "2025-11-12T14:30:00Z"
            }
        }


class QuoteResponse(BaseModel):
    """Response schema for quote details."""
    quote_id: int
    quote_number: str
    status: str
    origin: str
    destination: str
    distance_km: float
    estimated_duration_minutes: int
    pricing: dict
    service_type: str
    valid_until: str
    customer_id: int
    created_at: str
    response_time_ms: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": 123,
                "quote_number": "QT-20251111-A1B2C",
                "status": "draft",
                "origin": "123 Main St, New York, NY",
                "destination": "456 Park Ave, New York, NY",
                "distance_km": 5.2,
                "estimated_duration_minutes": 18,
                "pricing": {
                    "base_price": 15.00,
                    "distance_price": 7.80,
                    "time_price": 6.30,
                    "total_amount": 31.39,
                    "currency": "USD"
                },
                "service_type": "local",
                "valid_until": "2025-11-12T14:30:00Z",
                "customer_id": 1,
                "created_at": "2025-11-11T14:30:00Z",
                "response_time_ms": 850
            }
        }


class AcceptQuoteRequest(BaseModel):
    """Request schema for accepting a quote."""
    quote_id: int = Field(..., description="Quote ID to accept")


class RejectQuoteRequest(BaseModel):
    """Request schema for rejecting a quote."""
    quote_id: int = Field(..., description="Quote ID to reject")
    reason: Optional[str] = Field(default=None, max_length=500, description="Rejection reason")


class PricingInfoResponse(BaseModel):
    """Response schema for pricing information."""
    base_price: float
    price_per_km: float
    price_per_minute: float
    service_multipliers: dict
    additional_fees: dict
    surge_pricing: dict
    discounts: dict
    tax_rate: float
    currency: str


# Endpoints

@router.post("/instant", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_instant_quote(
    request: InstantQuoteRequest,
    db: Session = Depends(get_db)
):
    """
    Generate an instant transportation quote.

    This endpoint:
    - Calculates route using Google Maps
    - Computes price based on distance, time, and other factors
    - Creates quote in database
    - Returns complete quote details

    **Response time target: < 2 seconds**
    """
    try:
        quote_service = QuoteService(db)

        quote = await quote_service.create_instant_quote(
            origin=request.origin,
            destination=request.destination,
            customer_id=request.customer_id,
            service_type=request.service_type,
            extra_passengers=request.extra_passengers,
            extra_luggage=request.extra_luggage,
            extra_stops=request.extra_stops,
            waypoints=request.waypoints,
            scheduled_datetime=request.scheduled_datetime,
            cargo_description=request.cargo_description,
            special_requirements=request.special_requirements,
            promo_code=request.promo_code
        )

        logger.info(
            f"Instant quote created: {quote['quote_number']} in {quote['response_time_ms']}ms"
        )

        return quote

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrationError as e:
        logger.error(f"Integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating quote: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quote"
        )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a quote by ID.
    """
    try:
        quote_service = QuoteService(db)
        quote = await quote_service.get_quote(quote_id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote {quote_id} not found"
            )

        return quote

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quote"
        )


@router.put("/{quote_id}/accept", response_model=QuoteResponse)
async def accept_quote(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    Accept a quote.

    This marks the quote as accepted and makes it ready for booking conversion.
    """
    try:
        quote_service = QuoteService(db)
        quote = await quote_service.accept_quote(quote_id)

        logger.info(f"Quote {quote_id} accepted")
        return quote

    except ValidationError as e:
        logger.warning(f"Validation error accepting quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error accepting quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept quote"
        )


@router.put("/{quote_id}/reject", response_model=QuoteResponse)
async def reject_quote(
    quote_id: int,
    request: RejectQuoteRequest,
    db: Session = Depends(get_db)
):
    """
    Reject a quote.

    Optionally provide a reason for rejection.
    """
    try:
        quote_service = QuoteService(db)
        quote = await quote_service.reject_quote(quote_id, reason=request.reason)

        logger.info(f"Quote {quote_id} rejected")
        return quote

    except ValidationError as e:
        logger.warning(f"Validation error rejecting quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject quote"
        )


@router.get("/customer/{customer_id}", response_model=List[QuoteResponse])
async def get_customer_quotes(
    customer_id: int,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all quotes for a customer.

    Optionally filter by status (draft, sent, accepted, rejected, expired).
    """
    try:
        from src.models.quote import Quote, QuoteStatus

        query = db.query(Quote).filter(Quote.customer_id == customer_id)

        # Filter by status if provided
        if status:
            try:
                status_enum = QuoteStatus(status.lower())
                query = query.filter(Quote.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )

        # Apply pagination
        quotes = query.order_by(Quote.created_at.desc()).offset(offset).limit(limit).all()

        quote_service = QuoteService(db)
        return [quote_service._quote_to_dict(q) for q in quotes]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving customer quotes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quotes"
        )


@router.get("/pricing/info", response_model=PricingInfoResponse)
async def get_pricing_info():
    """
    Get current pricing information and rules.

    Returns the current pricing configuration including:
    - Base prices
    - Distance and time rates
    - Service type multipliers
    - Additional fees
    - Surge pricing rules
    - Discount information
    - Tax rate
    """
    try:
        pricing_service = PricingService()
        pricing_info = pricing_service.get_pricing_info()
        return pricing_info

    except Exception as e:
        logger.error(f"Error retrieving pricing info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pricing information"
        )


# ==================================================================================
# INTERNAL/ADMIN ENDPOINTS - NOT FOR PUBLIC USE
# These endpoints expose internal operating costs and profit margins
# ==================================================================================

@router.get("/{quote_id}/internal", tags=["quotes-internal"])
async def get_quote_internal_costs(
    quote_id: int,
    db: Session = Depends(get_db)
    # TODO: Add admin authentication dependency when RBAC is implemented
    # current_user: User = Depends(get_current_admin_user)
):
    """
    **[INTERNAL USE ONLY]** Get internal operating costs and profit analysis for a quote.

    This endpoint exposes:
    - Vehicle operating costs (fuel, maintenance, depreciation, etc.)
    - Profit margins
    - Cost breakdown

    **This information should NEVER be shown to customers.**

    **Authentication:** Requires admin role (TODO: implement)
    """
    try:
        from src.models.quote import Quote

        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote {quote_id} not found"
            )

        # Build internal cost response
        response = {
            "quote_id": quote.id,
            "quote_number": quote.quote_number,
            "customer_id": quote.customer_id,

            # Customer pricing (what they pay)
            "customer_price": {
                "subtotal": quote.subtotal,
                "tax": quote.tax_amount,
                "total": quote.total_amount,
                "currency": "USD"
            },

            # Internal operating costs
            "has_internal_costs": quote.internal_operating_costs is not None,
            "vehicle_id": quote.vehicle_id,
            "internal_operating_costs": quote.internal_operating_costs,

            # Profit analysis
            "profit_margin": quote.profit_margin,
            "profit_margin_percent": quote.profit_margin_percent,

            # Service details
            "distance_km": quote.distance_km,
            "duration_minutes": quote.estimated_duration_minutes,

            "created_at": quote.created_at.isoformat() if quote.created_at else None
        }

        logger.info(f"Internal costs retrieved for quote {quote_id} (ADMIN ACCESS)")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving internal costs for quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve internal costs"
        )


@router.get("/analytics/profitability", tags=["quotes-internal"])
async def get_profitability_analytics(
    days: int = 30,
    min_profit_margin_percent: Optional[float] = None,
    db: Session = Depends(get_db)
    # TODO: Add admin authentication dependency
    # current_user: User = Depends(get_current_admin_user)
):
    """
    **[INTERNAL USE ONLY]** Get profitability analytics for quotes.

    Analyzes profit margins across all quotes with internal cost data.

    Args:
        days: Number of days to analyze (default: 30)
        min_profit_margin_percent: Filter quotes with margin below this (optional)

    Returns:
        Profitability statistics and breakdown

    **Authentication:** Requires admin role (TODO: implement)
    """
    try:
        from src.models.quote import Quote
        from datetime import datetime, timedelta
        from sqlalchemy import func

        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)

        # Query quotes with internal costs
        query = db.query(Quote).filter(
            Quote.internal_operating_costs.isnot(None),
            Quote.created_at >= start_date
        )

        if min_profit_margin_percent is not None:
            query = query.filter(Quote.profit_margin_percent >= min_profit_margin_percent)

        quotes = query.all()

        if not quotes:
            return {
                "message": "No quotes with internal cost data found in this period",
                "days_analyzed": days,
                "total_quotes": 0
            }

        # Calculate statistics
        total_revenue = sum(q.total_amount for q in quotes)
        total_operating_costs = sum(
            q.internal_operating_costs.get("total_operating_cost", 0)
            for q in quotes if q.internal_operating_costs
        )
        total_profit = sum(q.profit_margin or 0 for q in quotes)
        avg_profit_margin_percent = sum(q.profit_margin_percent or 0 for q in quotes) / len(quotes)

        # Find best and worst performing quotes
        best_quote = max(quotes, key=lambda q: q.profit_margin or 0)
        worst_quote = min(quotes, key=lambda q: q.profit_margin or 0)

        # Breakdown by vehicle
        vehicle_stats = {}
        for quote in quotes:
            if quote.vehicle_id:
                if quote.vehicle_id not in vehicle_stats:
                    vehicle_stats[quote.vehicle_id] = {
                        "vehicle_id": quote.vehicle_id,
                        "quotes_count": 0,
                        "total_revenue": 0,
                        "total_profit": 0,
                        "total_distance_km": 0
                    }
                vehicle_stats[quote.vehicle_id]["quotes_count"] += 1
                vehicle_stats[quote.vehicle_id]["total_revenue"] += quote.total_amount
                vehicle_stats[quote.vehicle_id]["total_profit"] += (quote.profit_margin or 0)
                vehicle_stats[quote.vehicle_id]["total_distance_km"] += (quote.distance_km or 0)

        logger.info(f"Profitability analytics generated for {len(quotes)} quotes (ADMIN ACCESS)")

        return {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_quotes": len(quotes),
                "total_revenue": round(total_revenue, 2),
                "total_operating_costs": round(total_operating_costs, 2),
                "total_profit": round(total_profit, 2),
                "avg_profit_margin_percent": round(avg_profit_margin_percent, 2),
                "overall_profit_margin_percent": round((total_profit / total_revenue * 100), 2) if total_revenue > 0 else 0
            },
            "best_quote": {
                "quote_id": best_quote.id,
                "quote_number": best_quote.quote_number,
                "profit": round(best_quote.profit_margin or 0, 2),
                "profit_percent": round(best_quote.profit_margin_percent or 0, 2)
            },
            "worst_quote": {
                "quote_id": worst_quote.id,
                "quote_number": worst_quote.quote_number,
                "profit": round(worst_quote.profit_margin or 0, 2),
                "profit_percent": round(worst_quote.profit_margin_percent or 0, 2)
            },
            "by_vehicle": list(vehicle_stats.values()),
            "currency": "USD"
        }

    except Exception as e:
        logger.error(f"Error generating profitability analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics"
        )
