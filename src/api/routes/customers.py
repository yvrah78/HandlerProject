"""
CRUD API endpoints for Customer management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.customer import Customer
from src.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    Customer as CustomerSchema,
    CustomerListResponse
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerSchema, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new customer.

    Args:
        customer_data: Customer creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Customer: Created customer
    """
    # Check if email already exists
    existing_customer = db.query(Customer).filter(Customer.email == customer_data.email).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )

    # Create customer
    new_customer = Customer(**customer_data.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return new_customer


@router.get("/", response_model=CustomerListResponse)
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str = Query(None),
    is_active: bool = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List customers with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        search: Search by name or email
        is_active: Filter by active status
        db: Database session
        current_user: Current authenticated user

    Returns:
        CustomerListResponse: Paginated list of customers
    """
    query = db.query(Customer)

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Customer.name.ilike(search_filter)) | (Customer.email.ilike(search_filter))
        )

    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    customers = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": customers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{customer_id}", response_model=CustomerSchema)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get customer by ID.

    Args:
        customer_id: Customer ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Customer: Customer data

    Raises:
        HTTPException: If customer not found
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.put("/{customer_id}", response_model=CustomerSchema)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update customer by ID.

    Args:
        customer_id: Customer ID
        customer_data: Customer update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Customer: Updated customer

    Raises:
        HTTPException: If customer not found
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Update fields
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete customer by ID (soft delete - sets is_active=False).

    Args:
        customer_id: Customer ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If customer not found
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Soft delete
    customer.is_active = False
    db.commit()

    return None
