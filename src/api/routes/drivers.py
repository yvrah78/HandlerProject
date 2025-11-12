"""
CRUD API endpoints for Driver management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.driver import Driver, DriverStatus
from src.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    Driver as DriverSchema,
    DriverListResponse
)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("/", response_model=DriverSchema, status_code=status.HTTP_201_CREATED)
def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new driver.

    Args:
        driver_data: Driver creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Driver: Created driver
    """
    # Check if email already exists
    existing_driver = db.query(Driver).filter(Driver.email == driver_data.email).first()
    if existing_driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver with this email already exists"
        )

    # Check if license number already exists
    existing_license = db.query(Driver).filter(
        Driver.license_number == driver_data.license_number
    ).first()
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver with this license number already exists"
        )

    # Create driver
    new_driver = Driver(**driver_data.model_dump())
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver


@router.get("/", response_model=DriverListResponse)
def list_drivers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: DriverStatus = Query(None),
    is_active: bool = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List drivers with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Filter by driver status
        is_active: Filter by active status
        search: Search by name or email
        db: Database session
        current_user: Current authenticated user

    Returns:
        DriverListResponse: Paginated list of drivers
    """
    query = db.query(Driver)

    # Apply filters
    if status_filter:
        query = query.filter(Driver.status == status_filter)

    if is_active is not None:
        query = query.filter(Driver.is_active == is_active)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Driver.first_name.ilike(search_filter)) |
            (Driver.last_name.ilike(search_filter)) |
            (Driver.email.ilike(search_filter))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    drivers = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": drivers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{driver_id}", response_model=DriverSchema)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get driver by ID.

    Args:
        driver_id: Driver ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Driver: Driver data

    Raises:
        HTTPException: If driver not found
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    return driver


@router.put("/{driver_id}", response_model=DriverSchema)
def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update driver by ID.

    Args:
        driver_id: Driver ID
        driver_data: Driver update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Driver: Updated driver

    Raises:
        HTTPException: If driver not found
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Check if email is being changed and if new one already exists
    if driver_data.email and driver_data.email != driver.email:
        existing_email = db.query(Driver).filter(Driver.email == driver_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver with this email already exists"
            )

    # Check if license number is being changed and if new one already exists
    if (driver_data.license_number and
        driver_data.license_number != driver.license_number):
        existing_license = db.query(Driver).filter(
            Driver.license_number == driver_data.license_number
        ).first()
        if existing_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver with this license number already exists"
            )

    # Update fields
    update_data = driver_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    db.commit()
    db.refresh(driver)

    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete driver by ID (soft delete).

    Args:
        driver_id: Driver ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If driver not found
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Soft delete by marking as inactive
    driver.is_active = False
    driver.status = DriverStatus.UNAVAILABLE
    db.commit()


@router.put("/{driver_id}/status/{new_status}", response_model=DriverSchema)
def update_driver_status(
    driver_id: int,
    new_status: DriverStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update driver status (availability).

    Args:
        driver_id: Driver ID
        new_status: New driver status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Driver: Updated driver

    Raises:
        HTTPException: If driver not found
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    driver.status = new_status
    db.commit()
    db.refresh(driver)

    return driver


@router.put("/{driver_id}/rating", response_model=DriverSchema)
def update_driver_rating(
    driver_id: int,
    rating: int = Query(..., ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update driver rating.

    Args:
        driver_id: Driver ID
        rating: New rating (1-5 stars)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Driver: Updated driver

    Raises:
        HTTPException: If driver not found
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    driver.rating = rating
    db.commit()
    db.refresh(driver)

    return driver


@router.put("/{driver_id}/trips/increment", response_model=DriverSchema)
def increment_total_trips(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Increment total trips count for a driver.

    Args:
        driver_id: Driver ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Driver: Updated driver

    Raises:
        HTTPException: If driver not found
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    driver.total_trips += 1
    db.commit()
    db.refresh(driver)

    return driver
