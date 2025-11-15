"""
LangChain tools for financial operations.

These tools allow the FinancialAgent to create quotes, generate invoices,
process payments, and handle refunds through Stripe.
"""
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from src.core.logging import get_logger
from src.core.database import get_db


logger = get_logger(__name__)


class CreateQuoteInput(BaseModel):
    """Input schema for creating a quote."""
    customer_id: str = Field(description="Customer ID")
    service_type: str = Field(description="Type of service (e.g., 'airport_transfer', 'local_ride')")
    origin: str = Field(description="Pickup location")
    destination: str = Field(description="Dropoff location")
    passenger_count: int = Field(default=1, description="Number of passengers")


class CreateQuoteTool(BaseTool):
    """
    Tool for creating price quotes.

    Calculates and creates quotes for transportation services
    based on distance, service type, and other factors.
    """
    name = "create_quote"
    description = """
    Create a price quote for a transportation service. Use this when
    a customer requests pricing information. Input should include
    customer ID, service type, origin, and destination.
    """
    args_schema: Type[BaseModel] = CreateQuoteInput

    def _run(
        self,
        customer_id: str,
        service_type: str,
        origin: str,
        destination: str,
        passenger_count: int = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Create quote.

        Args:
            customer_id: Customer ID
            service_type: Service type
            origin: Origin location
            destination: Destination location
            passenger_count: Number of passengers
            run_manager: Callback manager

        Returns:
            str: JSON response with quote details
        """
        try:
            from src.models.quote import Quote
            from datetime import datetime

            # Calculate base price (simplified - would use actual routing in production)
            base_prices = {
                "airport_transfer": 75.00,
                "local_ride": 35.00,
                "long_distance": 120.00,
                "hourly": 50.00,
            }

            base_amount = Decimal(str(base_prices.get(service_type, 50.00)))

            # Add passenger surcharge if more than 4
            if passenger_count > 4:
                base_amount += Decimal(str((passenger_count - 4) * 10.00))

            # Create quote in database
            db = next(get_db())
            quote = Quote(
                customer_id=customer_id,
                service_type=service_type,
                origin=origin,
                destination=destination,
                amount=float(base_amount),
                valid_until=datetime.utcnow(),
                status="pending"
            )
            db.add(quote)
            db.commit()
            db.refresh(quote)

            logger.info(f"Quote created: {quote.id} for customer {customer_id}")

            import json
            return json.dumps({
                "success": True,
                "quote_id": quote.id,
                "customer_id": customer_id,
                "service_type": service_type,
                "amount": float(base_amount),
                "currency": "USD",
                "valid_until": quote.valid_until.isoformat(),
            })

        except Exception as e:
            logger.error(f"Failed to create quote: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        customer_id: str,
        service_type: str,
        origin: str,
        destination: str,
        passenger_count: int = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(customer_id, service_type, origin, destination, passenger_count, run_manager)


class GenerateInvoiceInput(BaseModel):
    """Input schema for generating invoices."""
    booking_id: str = Field(description="Booking ID to invoice")
    amount: float = Field(description="Invoice amount")
    due_date: Optional[str] = Field(default=None, description="Payment due date (ISO format)")


class GenerateInvoiceTool(BaseTool):
    """
    Tool for generating invoices.

    Creates formal invoices for completed or upcoming services.
    """
    name = "generate_invoice"
    description = """
    Generate an invoice for a booking. Use this after a booking is confirmed
    or completed. Input should include booking ID and amount.
    """
    args_schema: Type[BaseModel] = GenerateInvoiceInput

    def _run(
        self,
        booking_id: str,
        amount: float,
        due_date: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Generate invoice.

        Args:
            booking_id: Booking ID
            amount: Invoice amount
            due_date: Payment due date
            run_manager: Callback manager

        Returns:
            str: JSON response with invoice details
        """
        try:
            from src.models.invoice import Invoice
            from datetime import datetime, timedelta
            from dateutil import parser

            # Parse due date or default to 30 days
            if due_date:
                parsed_due_date = parser.parse(due_date)
            else:
                parsed_due_date = datetime.utcnow() + timedelta(days=30)

            # Create invoice
            db = next(get_db())
            invoice = Invoice(
                booking_id=booking_id,
                amount=amount,
                due_date=parsed_due_date,
                status="pending",
                invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{booking_id[:8]}"
            )
            db.add(invoice)
            db.commit()
            db.refresh(invoice)

            logger.info(f"Invoice generated: {invoice.id} for booking {booking_id}")

            import json
            return json.dumps({
                "success": True,
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "booking_id": booking_id,
                "amount": amount,
                "due_date": parsed_due_date.isoformat(),
                "status": "pending"
            })

        except Exception as e:
            logger.error(f"Failed to generate invoice: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        booking_id: str,
        amount: float,
        due_date: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(booking_id, amount, due_date, run_manager)


class ProcessPaymentInput(BaseModel):
    """Input schema for processing payments."""
    customer_id: str = Field(description="Customer ID")
    amount: float = Field(description="Payment amount")
    payment_method: str = Field(description="Payment method (e.g., 'card', 'bank_transfer')")
    invoice_id: Optional[str] = Field(default=None, description="Related invoice ID")


class ProcessPaymentTool(BaseTool):
    """
    Tool for processing payments via Stripe.

    Handles payment processing for invoices and bookings.
    """
    name = "process_payment"
    description = """
    Process a payment from a customer. Use this to charge a customer's
    payment method. Input should include customer ID, amount, and payment method.
    """
    args_schema: Type[BaseModel] = ProcessPaymentInput

    def _run(
        self,
        customer_id: str,
        amount: float,
        payment_method: str,
        invoice_id: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Process payment.

        Args:
            customer_id: Customer ID
            amount: Payment amount
            payment_method: Payment method
            invoice_id: Related invoice ID
            run_manager: Callback manager

        Returns:
            str: JSON response with payment status
        """
        try:
            from src.integrations.stripe_client import StripeClient
            from src.models.payment import Payment
            from datetime import datetime

            # Process payment via Stripe
            stripe_client = StripeClient()
            stripe_result = stripe_client.create_payment_intent(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                customer_id=customer_id
            )

            # Create payment record
            db = next(get_db())
            payment = Payment(
                customer_id=customer_id,
                amount=amount,
                payment_method=payment_method,
                invoice_id=invoice_id,
                status="completed" if stripe_result.get("id") != "pi_placeholder" else "pending",
                transaction_id=stripe_result.get("id"),
                payment_date=datetime.utcnow()
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)

            logger.info(f"Payment processed: {payment.id} for customer {customer_id}")

            import json
            return json.dumps({
                "success": True,
                "payment_id": payment.id,
                "customer_id": customer_id,
                "amount": amount,
                "status": payment.status,
                "transaction_id": stripe_result.get("id"),
            })

        except Exception as e:
            logger.error(f"Failed to process payment: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        customer_id: str,
        amount: float,
        payment_method: str,
        invoice_id: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(customer_id, amount, payment_method, invoice_id, run_manager)


class CreateRefundInput(BaseModel):
    """Input schema for creating refunds."""
    payment_id: str = Field(description="Payment ID to refund")
    amount: Optional[float] = Field(default=None, description="Refund amount (full refund if not specified)")
    reason: str = Field(description="Reason for refund")


class CreateRefundTool(BaseTool):
    """
    Tool for creating refunds via Stripe.

    Processes refunds for payments when needed.
    """
    name = "create_refund"
    description = """
    Create a refund for a payment. Use this when a customer requests
    a refund or when a service is cancelled. Input should include
    payment ID and reason.
    """
    args_schema: Type[BaseModel] = CreateRefundInput

    def _run(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Create refund.

        Args:
            payment_id: Payment ID to refund
            amount: Refund amount (None for full refund)
            reason: Refund reason
            run_manager: Callback manager

        Returns:
            str: JSON response with refund status
        """
        try:
            from src.integrations.stripe_client import StripeClient

            # Get original payment
            db = next(get_db())
            from src.models.payment import Payment
            payment = db.query(Payment).filter(Payment.id == payment_id).first()

            if not payment:
                raise ValueError(f"Payment {payment_id} not found")

            # Use full amount if not specified
            refund_amount = amount or payment.amount

            # Process refund via Stripe
            stripe_client = StripeClient()
            stripe_result = stripe_client.create_refund(
                payment_intent_id=payment.transaction_id,
                amount=int(refund_amount * 100),  # Convert to cents
                reason=reason
            )

            # Update payment status
            payment.status = "refunded"
            db.commit()

            logger.info(f"Refund created for payment {payment_id}: ${refund_amount}")

            import json
            return json.dumps({
                "success": True,
                "payment_id": payment_id,
                "refund_amount": refund_amount,
                "status": "refunded",
                "refund_id": stripe_result.get("id"),
                "reason": reason
            })

        except Exception as e:
            logger.error(f"Failed to create refund: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(payment_id, amount, reason, run_manager)
