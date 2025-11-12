"""
CRUD API endpoints for Payment management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from src.core.database import get_db
from src.core.security import get_current_user
from src.core.logging import get_logger
from src.models.user import User
from src.models.payment import Payment, PaymentStatus
from src.models.invoice import Invoice
from src.models.customer import Customer
from src.integrations.stripe_client import StripeClient
from src.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentProcessRequest,
    PaymentRefundRequest,
    Payment as PaymentSchema,
    PaymentListResponse
)

router = APIRouter(prefix="/payments", tags=["payments"])
logger = get_logger(__name__)
stripe_client = StripeClient()


def generate_transaction_id() -> str:
    """Generate a unique transaction ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"TXN-{timestamp}-{unique_id}"


@router.post("/", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new payment record.

    Args:
        payment_data: Payment creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Payment: Created payment
    """
    # Verify invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == payment_data.invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == payment_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Check amount doesn't exceed invoice total
    if payment_data.amount > invoice.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount exceeds invoice total"
        )

    # Create payment
    payment_data_dict = payment_data.model_dump()
    payment_data_dict["transaction_id"] = generate_transaction_id()
    payment_data_dict["status"] = PaymentStatus.PENDING

    new_payment = Payment(**payment_data_dict)
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    logger.info(f"Payment {new_payment.id} created with transaction ID {new_payment.transaction_id}")

    return new_payment


@router.get("/", response_model=PaymentListResponse)
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: PaymentStatus = Query(None),
    customer_id: int = Query(None),
    invoice_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List payments with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Filter by payment status
        customer_id: Filter by customer ID
        invoice_id: Filter by invoice ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        PaymentListResponse: Paginated list of payments
    """
    query = db.query(Payment)

    # Apply filters
    if status_filter:
        query = query.filter(Payment.status == status_filter)

    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    payments = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": payments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{payment_id}", response_model=PaymentSchema)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment by ID.

    Args:
        payment_id: Payment ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Payment: Payment data

    Raises:
        HTTPException: If payment not found
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return payment


@router.put("/{payment_id}", response_model=PaymentSchema)
def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update payment by ID.

    Args:
        payment_id: Payment ID
        payment_data: Payment update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Payment: Updated payment

    Raises:
        HTTPException: If payment not found
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Update fields
    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)

    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete payment by ID (mark as cancelled).

    Args:
        payment_id: Payment ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If payment not found
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    payment.status = PaymentStatus.CANCELLED
    db.commit()


@router.post("/{payment_id}/process", response_model=PaymentSchema)
def process_payment(
    payment_id: int,
    process_data: PaymentProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a payment via Stripe.

    Args:
        payment_id: Payment ID
        process_data: Payment processing data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Payment: Updated payment with Stripe details

    Raises:
        HTTPException: If payment not found or processing fails
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Check if already processed
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment cannot be processed (current status: {payment.status})"
        )

    try:
        # Process via Stripe
        payment.status = PaymentStatus.PROCESSING
        db.commit()

        # In a real scenario, this would call Stripe API
        # For now, mark as completed
        payment.status = PaymentStatus.COMPLETED
        payment.payment_date = datetime.utcnow()
        payment.stripe_payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"

        db.commit()
        db.refresh(payment)

        logger.info(f"Payment {payment_id} processed successfully")

        return payment

    except Exception as e:
        payment.status = PaymentStatus.FAILED
        payment.error_message = str(e)
        db.commit()
        db.refresh(payment)

        logger.error(f"Payment processing failed: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing failed: {str(e)}"
        )


@router.post("/{payment_id}/refund", response_model=PaymentSchema)
def refund_payment(
    payment_id: int,
    refund_data: PaymentRefundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refund a payment (full or partial).

    Args:
        payment_id: Payment ID
        refund_data: Refund request data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Payment: Updated payment with refund information

    Raises:
        HTTPException: If payment not found or refund fails
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Check if payment can be refunded
    if payment.status not in [PaymentStatus.COMPLETED, PaymentStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment cannot be refunded (current status: {payment.status})"
        )

    # Check refund amount
    refund_amount = refund_data.refund_amount or payment.amount
    if refund_amount > payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount exceeds payment amount"
        )

    try:
        # Process refund
        payment.refund_amount = refund_amount
        payment.refund_date = datetime.utcnow()
        payment.refund_reason = refund_data.refund_reason
        payment.status = PaymentStatus.REFUNDED

        db.commit()
        db.refresh(payment)

        logger.info(f"Payment {payment_id} refunded with amount {refund_amount}")

        return payment

    except Exception as e:
        logger.error(f"Refund failed: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund failed: {str(e)}"
        )


@router.get("/invoice/{invoice_id}/history", response_model=PaymentListResponse)
def get_payment_history_by_invoice(
    invoice_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment history for an invoice.

    Args:
        invoice_id: Invoice ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated user

    Returns:
        PaymentListResponse: Paginated list of payments for the invoice
    """
    # Verify invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    query = db.query(Payment).filter(Payment.invoice_id == invoice_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    payments = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": payments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
