"""
Payment Workflow: Complete payment processing flow.

Workflow Steps:
1. Create quote (Financial Agent)
2. Create invoice from quote (Financial Agent)
3. Send invoice to customer (Communications Agent)
4. Process payment (Financial Agent)
5. Send receipt (Communications Agent)

Error Handling:
- Retry failed payment attempts
- Send failure notifications
- Handle refund scenarios
"""
from typing import Dict, Any, Optional
from src.agents.orchestration import (
    Workflow,
    WorkflowStep,
    WorkflowContext
)
from src.core.logging import get_logger

logger = get_logger("payment_workflow")


def on_quote_created(context: WorkflowContext, result: Any) -> None:
    """Callback when quote is created."""
    logger.info(f"Quote created: {result}")

    if isinstance(result, dict) and "result" in result:
        quote = result["result"]
        if isinstance(quote, dict):
            context.set("quote_id", quote.get("quote_id"))
            context.set("quoted_amount", quote.get("amount"))
            context.set("quote_details", quote)


def on_invoice_created(context: WorkflowContext, result: Any) -> None:
    """Callback when invoice is created."""
    logger.info(f"Invoice created: {result}")

    if isinstance(result, dict) and "result" in result:
        invoice = result["result"]
        if isinstance(invoice, dict):
            context.set("invoice_id", invoice.get("invoice_id"))
            context.set("invoice_number", invoice.get("invoice_number"))
            context.set("total_amount", invoice.get("total"))
            context.set("invoice_url", invoice.get("url"))


def on_payment_processed(context: WorkflowContext, result: Any) -> None:
    """Callback when payment is processed."""
    logger.info(f"Payment processed: {result}")

    if isinstance(result, dict) and "result" in result:
        payment = result["result"]
        if isinstance(payment, dict):
            context.set("payment_id", payment.get("payment_id"))
            context.set("payment_status", payment.get("status"))
            context.set("payment_method", payment.get("method"))
            context.set("transaction_id", payment.get("transaction_id"))


def on_payment_failed(context: WorkflowContext, error: Exception) -> None:
    """Callback when payment fails."""
    logger.error(f"Payment failed: {error}")

    context.set("payment_status", "failed")
    context.set("payment_error", str(error))


def should_send_invoice(context: WorkflowContext) -> bool:
    """Check if invoice should be sent."""
    has_invoice = context.has("invoice_id")
    has_recipient = context.has("customer_email") or context.has("customer_phone")
    should_send = has_invoice and has_recipient

    logger.debug(f"Should send invoice: {should_send}")
    return should_send


def should_process_payment(context: WorkflowContext) -> bool:
    """Check if payment should be processed."""
    has_invoice = context.has("invoice_id")
    auto_process = context.get("auto_process_payment", True)
    should_process = has_invoice and auto_process

    logger.debug(f"Should process payment: {should_process}")
    return should_process


def should_send_receipt(context: WorkflowContext) -> bool:
    """Check if receipt should be sent."""
    payment_status = context.get("payment_status")
    success = payment_status in ["succeeded", "completed", "paid"]

    logger.debug(f"Should send receipt: {success} (status: {payment_status})")
    return success


def create_payment_workflow(
    payment_data: Dict[str, Any],
    skip_quote: bool = False
) -> Workflow:
    """
    Create a complete payment workflow.

    Args:
        payment_data: Payment information including:
            - customer_id: Customer ID
            - booking_id: Optional booking ID
            - service_type: Type of service
            - amount: Optional predetermined amount
            - payment_method: Payment method (card, bank_transfer, etc.)
            - customer_email: Customer email for invoice/receipt
            - customer_phone: Optional customer phone
            - auto_process_payment: Whether to auto-process payment
            - description: Payment description

        skip_quote: If True, skip quote creation and go straight to invoice

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.update(payment_data)

    steps = []

    # Step 1: Create quote (optional)
    if not skip_quote:
        steps.append(
            WorkflowStep(
                name="create_quote",
                agent="financial",
                action="execute",
                params={
                    "type": "create_quote",
                    "customer_id": payment_data.get("customer_id"),
                    "service_type": payment_data.get("service_type"),
                    "booking_id": payment_data.get("booking_id"),
                    "calculate_price": True,
                    "include_taxes": True,
                    "include_fees": True
                },
                retry_count=3,
                timeout=20.0,
                on_success=on_quote_created
            )
        )

    # Step 2: Create invoice
    steps.append(
        WorkflowStep(
            name="create_invoice",
            agent="financial",
            action="execute",
            params={
                "type": "create_invoice",
                "customer_id": payment_data.get("customer_id"),
                "quote_id": None if skip_quote else None,  # From context if quote was created
                "amount": payment_data.get("amount") if skip_quote else None,
                "description": payment_data.get("description", "Service payment"),
                "due_date": payment_data.get("due_date"),
                "booking_id": payment_data.get("booking_id")
            },
            retry_count=3,
            timeout=25.0,
            on_success=on_invoice_created
        )
    )

    # Step 3: Send invoice to customer
    steps.append(
        WorkflowStep(
            name="send_invoice",
            agent="communications",
            action="execute",
            params={
                "type": "send_email",
                "communication_type": "email",
                "recipient": payment_data.get("customer_email"),
                "subject": "Your Invoice",
                "template": "invoice",
                "invoice_id": None,  # From context
                "include_payment_link": True
            },
            retry_count=2,
            timeout=15.0,
            condition=should_send_invoice
        )
    )

    # Step 4: Process payment (conditional)
    steps.append(
        WorkflowStep(
            name="process_payment",
            agent="financial",
            action="execute",
            params={
                "type": "process_payment",
                "invoice_id": None,  # From context
                "payment_method": payment_data.get("payment_method", "card"),
                "payment_token": payment_data.get("payment_token"),
                "auto_capture": payment_data.get("auto_capture", True),
                "customer_id": payment_data.get("customer_id")
            },
            retry_count=2,
            timeout=30.0,
            condition=should_process_payment,
            on_success=on_payment_processed,
            on_failure=on_payment_failed
        )
    )

    # Step 5: Send receipt (conditional)
    steps.append(
        WorkflowStep(
            name="send_receipt",
            agent="communications",
            action="execute",
            params={
                "type": "send_email",
                "communication_type": "email",
                "recipient": payment_data.get("customer_email"),
                "subject": "Payment Receipt",
                "template": "receipt",
                "payment_id": None,  # From context
                "invoice_id": None,  # From context
                "include_pdf": True
            },
            retry_count=2,
            timeout=15.0,
            condition=should_send_receipt
        )
    )

    # Create workflow
    workflow = Workflow(
        name="complete_payment_workflow",
        description="Complete payment processing from quote to receipt",
        steps=steps,
        context=context,
        parallel=False,
        stop_on_error=False
    )

    logger.info(
        f"Created payment workflow with {len(steps)} steps "
        f"for customer {payment_data.get('customer_id')}"
    )

    return workflow


def create_refund_workflow(refund_data: Dict[str, Any]) -> Workflow:
    """
    Create a refund processing workflow.

    Args:
        refund_data: Refund information including:
            - payment_id: Original payment ID
            - amount: Refund amount (optional, defaults to full refund)
            - reason: Refund reason
            - customer_email: Customer email for notification

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.update(refund_data)

    def on_refund_processed(ctx: WorkflowContext, result: Any) -> None:
        """Callback when refund is processed."""
        logger.info(f"Refund processed: {result}")

        if isinstance(result, dict) and "result" in result:
            refund = result["result"]
            if isinstance(refund, dict):
                ctx.set("refund_id", refund.get("refund_id"))
                ctx.set("refund_status", refund.get("status"))
                ctx.set("refunded_amount", refund.get("amount"))

    def should_send_notification(ctx: WorkflowContext) -> bool:
        """Check if refund notification should be sent."""
        refund_status = ctx.get("refund_status")
        return refund_status in ["succeeded", "completed"]

    steps = [
        # Step 1: Process refund
        WorkflowStep(
            name="process_refund",
            agent="financial",
            action="execute",
            params={
                "type": "refund_payment",
                "payment_id": refund_data.get("payment_id"),
                "amount": refund_data.get("amount"),  # None = full refund
                "reason": refund_data.get("reason", "customer_request"),
                "metadata": {
                    "refund_type": refund_data.get("refund_type", "full"),
                    "requested_by": refund_data.get("requested_by", "system")
                }
            },
            retry_count=2,
            timeout=30.0,
            on_success=on_refund_processed
        ),

        # Step 2: Send refund notification
        WorkflowStep(
            name="send_refund_notification",
            agent="communications",
            action="execute",
            params={
                "type": "send_email",
                "communication_type": "email",
                "recipient": refund_data.get("customer_email"),
                "subject": "Refund Processed",
                "template": "refund_confirmation",
                "refund_id": None,  # From context
                "refunded_amount": None  # From context
            },
            retry_count=2,
            timeout=15.0,
            condition=should_send_notification
        ),
    ]

    workflow = Workflow(
        name="refund_workflow",
        description="Process refund and notify customer",
        steps=steps,
        context=context,
        parallel=False,
        stop_on_error=True
    )

    logger.info(
        f"Created refund workflow for payment {refund_data.get('payment_id')}"
    )

    return workflow


def create_invoice_only_workflow(invoice_data: Dict[str, Any]) -> Workflow:
    """
    Create a workflow that only generates and sends an invoice.

    Useful for manual payment scenarios or quotes.

    Args:
        invoice_data: Invoice information

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.update(invoice_data)

    steps = [
        # Step 1: Create invoice
        WorkflowStep(
            name="create_invoice",
            agent="financial",
            action="execute",
            params={
                "type": "create_invoice",
                **invoice_data
            },
            retry_count=3,
            timeout=25.0,
            on_success=on_invoice_created
        ),

        # Step 2: Send invoice
        WorkflowStep(
            name="send_invoice",
            agent="communications",
            action="execute",
            params={
                "type": "send_email",
                "communication_type": "email",
                "recipient": invoice_data.get("customer_email"),
                "subject": "Your Invoice",
                "template": "invoice",
                "invoice_id": None,  # From context
                "include_payment_link": invoice_data.get("include_payment_link", True)
            },
            retry_count=2,
            timeout=15.0,
            condition=should_send_invoice
        ),
    ]

    workflow = Workflow(
        name="invoice_only_workflow",
        description="Generate and send invoice without payment processing",
        steps=steps,
        context=context,
        parallel=False,
        stop_on_error=True
    )

    logger.info("Created invoice-only workflow")

    return workflow
