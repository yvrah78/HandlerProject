"""
Booking Workflow: Complete booking creation and management process.

Workflow Steps:
1. Create booking (Operations Agent)
2. Assign vehicle and driver (Operations Agent)
3. Send confirmation notification (Communications Agent)
4. Create invoice (Financial Agent)
5. Process payment (Financial Agent)
6. Send receipt (Communications Agent)

Error Handling:
- Retry failed steps up to 3 times
- Cancel booking if critical steps fail
- Notify customer of issues
"""
from typing import Dict, Any
from src.agents.orchestration import (
    Workflow,
    WorkflowStep,
    WorkflowContext
)
from src.core.logging import get_logger

logger = get_logger("booking_workflow")


def on_booking_created(context: WorkflowContext, result: Any) -> None:
    """Callback when booking is created successfully."""
    logger.info(f"Booking created: {result}")

    # Extract booking ID and store in context
    if isinstance(result, dict) and "result" in result:
        booking_data = result["result"]
        if isinstance(booking_data, dict):
            booking_id = booking_data.get("booking_id")
            if booking_id:
                context.set("booking_id", booking_id)
                context.set("booking_data", booking_data)
                logger.info(f"Stored booking ID in context: {booking_id}")


def on_vehicle_assigned(context: WorkflowContext, result: Any) -> None:
    """Callback when vehicle and driver are assigned."""
    logger.info(f"Vehicle assigned: {result}")

    # Extract assignment details
    if isinstance(result, dict) and "result" in result:
        assignment = result["result"]
        if isinstance(assignment, dict):
            context.set("vehicle_id", assignment.get("vehicle_id"))
            context.set("driver_id", assignment.get("driver_id"))


def on_invoice_created(context: WorkflowContext, result: Any) -> None:
    """Callback when invoice is created."""
    logger.info(f"Invoice created: {result}")

    # Extract invoice details
    if isinstance(result, dict) and "result" in result:
        invoice = result["result"]
        if isinstance(invoice, dict):
            context.set("invoice_id", invoice.get("invoice_id"))
            context.set("amount", invoice.get("amount"))


def on_payment_processed(context: WorkflowContext, result: Any) -> None:
    """Callback when payment is processed."""
    logger.info(f"Payment processed: {result}")

    # Extract payment details
    if isinstance(result, dict) and "result" in result:
        payment = result["result"]
        if isinstance(payment, dict):
            context.set("payment_id", payment.get("payment_id"))
            context.set("payment_status", payment.get("status"))


def on_critical_failure(context: WorkflowContext, error: Exception) -> None:
    """Callback when a critical step fails."""
    logger.error(f"Critical failure in booking workflow: {error}")

    # Mark booking as failed
    context.set("workflow_status", "failed")
    context.set("failure_reason", str(error))


def should_process_payment(context: WorkflowContext) -> bool:
    """
    Condition to check if payment should be processed.

    Only process payment if invoice was created successfully.
    """
    has_invoice = context.has("invoice_id")
    logger.debug(f"Should process payment: {has_invoice}")
    return has_invoice


def should_send_receipt(context: WorkflowContext) -> bool:
    """
    Condition to check if receipt should be sent.

    Only send receipt if payment was successful.
    """
    payment_status = context.get("payment_status")
    success = payment_status == "succeeded"
    logger.debug(f"Should send receipt: {success} (status: {payment_status})")
    return success


def create_booking_workflow(booking_data: Dict[str, Any]) -> Workflow:
    """
    Create a complete booking workflow.

    Args:
        booking_data: Booking information including:
            - customer_id: Customer ID
            - service_type: Type of service
            - pickup_location: Pickup address
            - dropoff_location: Dropoff address
            - pickup_time: Scheduled pickup time
            - passenger_count: Number of passengers
            - special_requirements: Optional special requirements

    Returns:
        Workflow instance ready to execute
    """
    # Create workflow context with initial data
    context = WorkflowContext()
    context.update(booking_data)

    # Build workflow steps
    steps = [
        # Step 1: Create booking
        WorkflowStep(
            name="create_booking",
            agent="operations",
            action="execute",
            params={
                "type": "create_booking",
                "customer_id": booking_data.get("customer_id"),
                "service_type": booking_data.get("service_type"),
                "pickup_location": booking_data.get("pickup_location"),
                "dropoff_location": booking_data.get("dropoff_location"),
                "pickup_time": booking_data.get("pickup_time"),
                "passenger_count": booking_data.get("passenger_count", 1),
                "special_requirements": booking_data.get("special_requirements", "")
            },
            retry_count=3,
            timeout=30.0,
            on_success=on_booking_created,
            on_failure=on_critical_failure
        ),

        # Step 2: Assign vehicle and driver
        WorkflowStep(
            name="assign_vehicle_and_driver",
            agent="operations",
            action="execute",
            params={
                "type": "assign_vehicle",
                "booking_id": None,  # Will be filled from context
                "service_type": booking_data.get("service_type"),
                "passenger_count": booking_data.get("passenger_count", 1),
                "pickup_time": booking_data.get("pickup_time")
            },
            retry_count=3,
            timeout=20.0,
            on_success=on_vehicle_assigned,
            on_failure=on_critical_failure
        ),

        # Step 3: Send booking confirmation
        WorkflowStep(
            name="send_confirmation",
            agent="communications",
            action="execute",
            params={
                "type": "send_sms",
                "communication_type": "sms",
                "recipient": booking_data.get("customer_phone", ""),
                "message": "Your booking has been confirmed! Details will follow via email.",
                "template": "booking_confirmation"
            },
            retry_count=2,
            timeout=15.0
        ),

        # Step 4: Create invoice
        WorkflowStep(
            name="create_invoice",
            agent="financial",
            action="execute",
            params={
                "type": "create_invoice",
                "customer_id": booking_data.get("customer_id"),
                "booking_id": None,  # Will be filled from context
                "service_type": booking_data.get("service_type"),
                "calculate_price": True
            },
            retry_count=3,
            timeout=20.0,
            on_success=on_invoice_created
        ),

        # Step 5: Process payment (conditional)
        WorkflowStep(
            name="process_payment",
            agent="financial",
            action="execute",
            params={
                "type": "process_payment",
                "invoice_id": None,  # Will be filled from context
                "payment_method": booking_data.get("payment_method", "card"),
                "auto_capture": booking_data.get("auto_capture", True)
            },
            retry_count=2,
            timeout=30.0,
            condition=should_process_payment,
            on_success=on_payment_processed
        ),

        # Step 6: Send receipt (conditional)
        WorkflowStep(
            name="send_receipt",
            agent="communications",
            action="execute",
            params={
                "type": "send_email",
                "communication_type": "email",
                "recipient": booking_data.get("customer_email", ""),
                "subject": "Your Booking Receipt",
                "template": "payment_receipt",
                "invoice_id": None,  # Will be filled from context
                "payment_id": None  # Will be filled from context
            },
            retry_count=2,
            timeout=15.0,
            condition=should_send_receipt
        ),
    ]

    # Create workflow
    workflow = Workflow(
        name="complete_booking_workflow",
        description="Complete booking creation from start to payment confirmation",
        steps=steps,
        context=context,
        parallel=False,  # Sequential execution
        stop_on_error=False  # Continue even if non-critical steps fail
    )

    logger.info(
        f"Created booking workflow with {len(steps)} steps for "
        f"customer {booking_data.get('customer_id')}"
    )

    return workflow


def create_quick_booking_workflow(booking_data: Dict[str, Any]) -> Workflow:
    """
    Create a simplified booking workflow without payment processing.

    Useful for bookings that will be paid later or cash on delivery.

    Args:
        booking_data: Booking information

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.update(booking_data)

    steps = [
        # Step 1: Create booking
        WorkflowStep(
            name="create_booking",
            agent="operations",
            action="execute",
            params={
                "type": "create_booking",
                **booking_data
            },
            retry_count=3,
            timeout=30.0,
            on_success=on_booking_created,
            on_failure=on_critical_failure
        ),

        # Step 2: Assign vehicle and driver
        WorkflowStep(
            name="assign_vehicle_and_driver",
            agent="operations",
            action="execute",
            params={
                "type": "assign_vehicle",
                "service_type": booking_data.get("service_type"),
            },
            retry_count=3,
            timeout=20.0,
            on_success=on_vehicle_assigned
        ),

        # Step 3: Send booking confirmation
        WorkflowStep(
            name="send_confirmation",
            agent="communications",
            action="execute",
            params={
                "type": "send_sms",
                "communication_type": "sms",
                "recipient": booking_data.get("customer_phone", ""),
                "message": "Your booking has been confirmed!"
            },
            retry_count=2,
            timeout=15.0
        ),
    ]

    workflow = Workflow(
        name="quick_booking_workflow",
        description="Simplified booking workflow without payment",
        steps=steps,
        context=context,
        parallel=False,
        stop_on_error=True
    )

    logger.info(f"Created quick booking workflow with {len(steps)} steps")

    return workflow
