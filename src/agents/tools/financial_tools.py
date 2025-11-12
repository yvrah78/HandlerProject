"""
Financial tools for Financial Agent.
Tools for invoice, payment, and quote management.
"""
from typing import Dict, Any, Optional
from pydantic import Field

from src.agents.tools.base_tool import BaseTool, ToolInput, ToolOutput
from src.core.logging import get_logger
from src.core.database import get_db
from src.models.invoice import Invoice, InvoiceStatus
from src.models.payment import Payment, PaymentStatus
from src.models.quote import Quote

logger = get_logger(__name__)


class GetQuoteInput(ToolInput):
    """Input for get_quote tool."""

    quote_id: int = Field(..., description="Quote ID to retrieve")


class CreateInvoiceInput(ToolInput):
    """Input for create_invoice tool."""

    booking_id: int = Field(..., description="Associated booking ID")
    customer_id: int = Field(..., description="Customer ID")
    amount: float = Field(..., gt=0, description="Invoice amount")
    tax_amount: Optional[float] = Field(0.0, description="Tax amount")
    discount_amount: Optional[float] = Field(0.0, description="Discount amount")


class GetInvoiceInput(ToolInput):
    """Input for get_invoice tool."""

    invoice_id: int = Field(..., description="Invoice ID to retrieve")


class UpdateInvoiceStatusInput(ToolInput):
    """Input for update_invoice_status tool."""

    invoice_id: int = Field(..., description="Invoice ID")
    status: str = Field(
        ...,
        description="New status (draft, sent, paid, overdue, cancelled)",
    )


class GetQuoteTool(BaseTool):
    """Tool for retrieving quote information."""

    def __init__(self):
        super().__init__(
            name="get_quote",
            description="Retrieve quote details by ID",
            input_schema=GetQuoteInput,
            required_permissions=["read:quotes"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute get quote."""
        try:
            quote_id = input_data.get("quote_id")
            db = get_db()
            quote = db.query(Quote).filter(Quote.id == quote_id).first()

            if not quote:
                return ToolOutput(
                    success=False,
                    error=f"Quote {quote_id} not found",
                )

            return ToolOutput(
                success=True,
                data={
                    "id": quote.id,
                    "quote_number": quote.quote_number,
                    "customer_id": quote.customer_id,
                    "total_amount": float(quote.total_amount),
                    "status": quote.status,
                    "valid_until": quote.valid_until.isoformat()
                    if quote.valid_until
                    else None,
                },
            )

        except Exception as e:
            logger.error(f"Error retrieving quote: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class CreateInvoiceTool(BaseTool):
    """Tool for creating invoices."""

    def __init__(self):
        super().__init__(
            name="create_invoice",
            description="Create new invoice from booking",
            input_schema=CreateInvoiceInput,
            required_permissions=["write:invoices", "read:bookings"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute create invoice."""
        try:
            from datetime import datetime, timedelta

            booking_id = input_data.get("booking_id")
            customer_id = input_data.get("customer_id")
            amount = input_data.get("amount")
            tax_amount = input_data.get("tax_amount", 0.0)
            discount_amount = input_data.get("discount_amount", 0.0)

            db = get_db()

            # Check if invoice already exists for this booking
            existing = (
                db.query(Invoice).filter(Invoice.booking_id == booking_id).first()
            )
            if existing:
                return ToolOutput(
                    success=False,
                    error=f"Invoice already exists for booking {booking_id}",
                )

            # Create invoice
            import uuid

            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:5].upper()}"
            total_amount = amount + tax_amount - discount_amount

            invoice = Invoice(
                booking_id=booking_id,
                customer_id=customer_id,
                invoice_number=invoice_number,
                amount=amount,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                due_date=datetime.utcnow() + timedelta(days=30),
                status=InvoiceStatus.DRAFT,
            )

            db.add(invoice)
            db.commit()
            db.refresh(invoice)

            return ToolOutput(
                success=True,
                data={
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "total_amount": float(invoice.total_amount),
                    "status": invoice.status,
                },
            )

        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class GetInvoiceTool(BaseTool):
    """Tool for retrieving invoice information."""

    def __init__(self):
        super().__init__(
            name="get_invoice",
            description="Retrieve invoice details by ID",
            input_schema=GetInvoiceInput,
            required_permissions=["read:invoices"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute get invoice."""
        try:
            invoice_id = input_data.get("invoice_id")
            db = get_db()
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

            if not invoice:
                return ToolOutput(
                    success=False,
                    error=f"Invoice {invoice_id} not found",
                )

            return ToolOutput(
                success=True,
                data={
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "booking_id": invoice.booking_id,
                    "amount": float(invoice.amount),
                    "tax_amount": float(invoice.tax_amount),
                    "discount_amount": float(invoice.discount_amount),
                    "total_amount": float(invoice.total_amount),
                    "status": invoice.status,
                    "issued_date": invoice.issued_date.isoformat()
                    if invoice.issued_date
                    else None,
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                    "paid_date": invoice.paid_date.isoformat() if invoice.paid_date else None,
                },
            )

        except Exception as e:
            logger.error(f"Error retrieving invoice: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class UpdateInvoiceStatusTool(BaseTool):
    """Tool for updating invoice status."""

    def __init__(self):
        super().__init__(
            name="update_invoice_status",
            description="Update invoice status",
            input_schema=UpdateInvoiceStatusInput,
            required_permissions=["write:invoices"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute update invoice status."""
        try:
            invoice_id = input_data.get("invoice_id")
            status_str = input_data.get("status").upper()

            db = get_db()
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

            if not invoice:
                return ToolOutput(
                    success=False,
                    error=f"Invoice {invoice_id} not found",
                )

            # Validate status
            try:
                new_status = InvoiceStatus[status_str]
            except KeyError:
                return ToolOutput(
                    success=False,
                    error=f"Invalid status: {status_str}",
                )

            invoice.status = new_status

            # Update timestamp if needed
            if new_status == InvoiceStatus.PAID:
                from datetime import datetime

                invoice.paid_date = datetime.utcnow()

            db.commit()
            db.refresh(invoice)

            return ToolOutput(
                success=True,
                data={
                    "invoice_id": invoice.id,
                    "status": invoice.status,
                    "updated_at": invoice.updated_at.isoformat()
                    if invoice.updated_at
                    else None,
                },
            )

        except Exception as e:
            logger.error(f"Error updating invoice status: {str(e)}")
            return ToolOutput(success=False, error=str(e))


def register_financial_tools(registry) -> None:
    """
    Register all financial tools in the registry.

    Args:
        registry: ToolRegistry instance
    """
    registry.register(GetQuoteTool(), category="financial")
    registry.register(CreateInvoiceTool(), category="financial")
    registry.register(GetInvoiceTool(), category="financial")
    registry.register(UpdateInvoiceStatusTool(), category="financial")
    logger.info("Financial tools registered")
