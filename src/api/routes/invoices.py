"""
CRUD API endpoints for Invoice management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.invoice import Invoice, InvoiceStatus
from src.models.booking import Booking
from src.models.customer import Customer
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    Invoice as InvoiceSchema,
    InvoiceListResponse
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


def generate_invoice_number() -> str:
    """Generate a unique invoice number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:5].upper()
    return f"INV-{timestamp}-{unique_id}"


@router.post("/", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new invoice.

    Args:
        invoice_data: Invoice creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Invoice: Created invoice
    """
    # Verify booking exists
    booking = db.query(Booking).filter(Booking.id == invoice_data.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == invoice_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Check if invoice already exists for this booking
    existing_invoice = db.query(Invoice).filter(Invoice.booking_id == invoice_data.booking_id).first()
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice already exists for this booking"
        )

    # Create invoice
    invoice_data_dict = invoice_data.model_dump()
    invoice_data_dict["invoice_number"] = generate_invoice_number()
    invoice_data_dict["due_date"] = datetime.utcnow() + timedelta(days=30)  # 30 days payment terms

    new_invoice = Invoice(**invoice_data_dict)
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)

    return new_invoice


@router.get("/", response_model=InvoiceListResponse)
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: InvoiceStatus = Query(None),
    customer_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List invoices with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Filter by invoice status
        customer_id: Filter by customer ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        InvoiceListResponse: Paginated list of invoices
    """
    query = db.query(Invoice)

    # Apply filters
    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    invoices = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": invoices,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{invoice_id}", response_model=InvoiceSchema)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get invoice by ID.

    Args:
        invoice_id: Invoice ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Invoice: Invoice data

    Raises:
        HTTPException: If invoice not found
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.put("/{invoice_id}", response_model=InvoiceSchema)
def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update invoice by ID.

    Args:
        invoice_id: Invoice ID
        invoice_data: Invoice update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Invoice: Updated invoice

    Raises:
        HTTPException: If invoice not found
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Update sent_date if status changes to SENT
    if invoice_data.status == InvoiceStatus.SENT and invoice.sent_date is None:
        invoice.sent_date = datetime.utcnow()

    # Update paid_date if status changes to PAID
    if invoice_data.status == InvoiceStatus.PAID and invoice.paid_date is None:
        invoice.paid_date = datetime.utcnow()

    db.commit()
    db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete (soft delete) invoice by ID.

    Args:
        invoice_id: Invoice ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If invoice not found
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Soft delete by marking as cancelled
    invoice.status = InvoiceStatus.CANCELLED
    db.commit()


@router.put("/{invoice_id}/status/{new_status}", response_model=InvoiceSchema)
def update_invoice_status(
    invoice_id: int,
    new_status: InvoiceStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update invoice status.

    Args:
        invoice_id: Invoice ID
        new_status: New invoice status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Invoice: Updated invoice

    Raises:
        HTTPException: If invoice not found
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    invoice.status = new_status

    # Update timestamps based on status
    if new_status == InvoiceStatus.SENT and invoice.sent_date is None:
        invoice.sent_date = datetime.utcnow()
    elif new_status == InvoiceStatus.PAID and invoice.paid_date is None:
        invoice.paid_date = datetime.utcnow()

    db.commit()
    db.refresh(invoice)

    return invoice
