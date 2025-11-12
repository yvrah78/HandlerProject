"""
CRUD API endpoints for Vehicle/Fleet management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.vehicle import Vehicle, VehicleStatus
from src.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    Vehicle as VehicleSchema,
    VehicleListResponse
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/", response_model=VehicleSchema, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new vehicle.

    Args:
        vehicle_data: Vehicle creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Vehicle: Created vehicle
    """
    # Check if license plate already exists
    existing_vehicle = db.query(Vehicle).filter(
        Vehicle.license_plate == vehicle_data.license_plate
    ).first()
    if existing_vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this license plate already exists"
        )

    # Create vehicle
    new_vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return new_vehicle


@router.get("/", response_model=VehicleListResponse)
def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: VehicleStatus = Query(None),
    vehicle_type: str = Query(None),
    is_active: bool = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List vehicles with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Filter by vehicle status
        vehicle_type: Filter by vehicle type
        is_active: Filter by active status
        db: Database session
        current_user: Current authenticated user

    Returns:
        VehicleListResponse: Paginated list of vehicles
    """
    query = db.query(Vehicle)

    # Apply filters
    if status_filter:
        query = query.filter(Vehicle.status == status_filter)

    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type == vehicle_type)

    if is_active is not None:
        query = query.filter(Vehicle.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    vehicles = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": vehicles,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{vehicle_id}", response_model=VehicleSchema)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get vehicle by ID.

    Args:
        vehicle_id: Vehicle ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Vehicle: Vehicle data

    Raises:
        HTTPException: If vehicle not found
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleSchema)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update vehicle by ID.

    Args:
        vehicle_id: Vehicle ID
        vehicle_data: Vehicle update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Vehicle: Updated vehicle

    Raises:
        HTTPException: If vehicle not found
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    # Check if license plate is being changed and if new one already exists
    if (vehicle_data.license_plate and
        vehicle_data.license_plate != vehicle.license_plate):
        existing_vehicle = db.query(Vehicle).filter(
            Vehicle.license_plate == vehicle_data.license_plate
        ).first()
        if existing_vehicle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle with this license plate already exists"
            )

    # Update fields
    update_data = vehicle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete vehicle by ID (soft delete).

    Args:
        vehicle_id: Vehicle ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If vehicle not found
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    # Soft delete by marking as inactive
    vehicle.is_active = False
    vehicle.status = VehicleStatus.OUT_OF_SERVICE
    db.commit()


@router.put("/{vehicle_id}/status/{new_status}", response_model=VehicleSchema)
def update_vehicle_status(
    vehicle_id: int,
    new_status: VehicleStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update vehicle status.

    Args:
        vehicle_id: Vehicle ID
        new_status: New vehicle status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Vehicle: Updated vehicle

    Raises:
        HTTPException: If vehicle not found
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    vehicle.status = new_status
    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.put("/{vehicle_id}/maintenance/schedule", response_model=VehicleSchema)
def schedule_maintenance(
    vehicle_id: int,
    next_maintenance_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schedule next maintenance for a vehicle.

    Args:
        vehicle_id: Vehicle ID
        next_maintenance_date: Next maintenance date
        db: Database session
        current_user: Current authenticated user

    Returns:
        Vehicle: Updated vehicle

    Raises:
        HTTPException: If vehicle not found
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    vehicle.next_maintenance_date = next_maintenance_date
    vehicle.last_maintenance_date = datetime.utcnow()
    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.put("/{vehicle_id}/mileage", response_model=VehicleSchema)
def update_mileage(
    vehicle_id: int,
    mileage_km: float = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update vehicle mileage.

    Args:
        vehicle_id: Vehicle ID
        mileage_km: New mileage in kilometers
        db: Database session
        current_user: Current authenticated user

    Returns:
        Vehicle: Updated vehicle

    Raises:
        HTTPException: If vehicle not found
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    if mileage_km < vehicle.mileage_km:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mileage cannot decrease"
        )

    vehicle.mileage_km = mileage_km
    db.commit()
    db.refresh(vehicle)

    return vehicle
