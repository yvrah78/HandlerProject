"""
CRUD API endpoints for Booking management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import secrets

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.booking import Booking, BookingStatus
from src.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    Booking as BookingSchema,
    BookingListResponse
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def generate_booking_number() -> str:
    """Generate a unique booking number."""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"BK-{timestamp}-{random_part}"


@router.post("/", response_model=BookingSchema, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new booking.

    Args:
        booking_data: Booking creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Booking: Created booking
    """
    # Generate unique booking number
    booking_number = generate_booking_number()

    # Create booking
    new_booking = Booking(
        **booking_data.model_dump(),
        booking_number=booking_number,
        status=BookingStatus.PENDING
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking


@router.get("/", response_model=BookingListResponse)
def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    status: Optional[BookingStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List bookings with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        customer_id: Filter by customer ID
        status: Filter by booking status
        db: Database session
        current_user: Current authenticated user

    Returns:
        BookingListResponse: Paginated list of bookings
    """
    query = db.query(Booking)

    # Apply filters
    if customer_id:
        query = query.filter(Booking.customer_id == customer_id)

    if status:
        query = query.filter(Booking.status == status)

    # Order by created_at desc
    query = query.order_by(Booking.created_at.desc())

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    bookings = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": bookings,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{booking_id}", response_model=BookingSchema)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get booking by ID.

    Args:
        booking_id: Booking ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Booking: Booking data

    Raises:
        HTTPException: If booking not found
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    return booking


@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update booking by ID.

    Args:
        booking_id: Booking ID
        booking_data: Booking update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Booking: Updated booking

    Raises:
        HTTPException: If booking not found
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Update fields
    update_data = booking_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)

    # Update timestamps based on status
    if "status" in update_data:
        if update_data["status"] == BookingStatus.CONFIRMED and not booking.confirmed_at:
            booking.confirmed_at = datetime.utcnow()
        elif update_data["status"] == BookingStatus.COMPLETED and not booking.completed_at:
            booking.completed_at = datetime.utcnow()
        elif update_data["status"] == BookingStatus.CANCELLED and not booking.cancelled_at:
            booking.cancelled_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)

    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel booking by ID.

    Args:
        booking_id: Booking ID
        reason: Cancellation reason
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If booking not found or already cancelled
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled"
        )

    # Cancel booking
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    if reason:
        booking.cancellation_reason = reason

    db.commit()

    return None
