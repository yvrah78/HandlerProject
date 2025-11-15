"""
Communication Workflow: Automated multi-channel communication.

Workflow Steps:
1. Send SMS notification (Communications Agent)
2. Send email with details (Communications Agent)
3. Follow-up call if needed (Communications Agent)

Error Handling:
- Retry failed communications
- Fallback to alternative channels
- Track delivery status
"""
from typing import Dict, Any, List
from src.agents.orchestration import (
    Workflow,
    WorkflowStep,
    WorkflowContext
)
from src.core.logging import get_logger

logger = get_logger("communication_workflow")


def on_sms_sent(context: WorkflowContext, result: Any) -> None:
    """Callback when SMS is sent."""
    logger.info(f"SMS sent: {result}")

    if isinstance(result, dict) and "result" in result:
        sms_result = result["result"]
        if isinstance(sms_result, dict):
            context.set("sms_id", sms_result.get("message_id"))
            context.set("sms_status", sms_result.get("status"))


def on_email_sent(context: WorkflowContext, result: Any) -> None:
    """Callback when email is sent."""
    logger.info(f"Email sent: {result}")

    if isinstance(result, dict) and "result" in result:
        email_result = result["result"]
        if isinstance(email_result, dict):
            context.set("email_id", email_result.get("message_id"))
            context.set("email_status", email_result.get("status"))


def on_call_made(context: WorkflowContext, result: Any) -> None:
    """Callback when call is made."""
    logger.info(f"Call made: {result}")

    if isinstance(result, dict) and "result" in result:
        call_result = result["result"]
        if isinstance(call_result, dict):
            context.set("call_id", call_result.get("call_id"))
            context.set("call_status", call_result.get("status"))
            context.set("call_duration", call_result.get("duration"))


def should_send_email(context: WorkflowContext) -> bool:
    """Check if email should be sent."""
    has_email = bool(context.get("recipient_email"))
    logger.debug(f"Should send email: {has_email}")
    return has_email


def should_make_call(context: WorkflowContext) -> bool:
    """Check if follow-up call should be made."""
    # Make call if SMS failed or if it's a high-priority message
    sms_status = context.get("sms_status")
    is_urgent = context.get("priority", "normal") in ["high", "urgent", "critical"]
    requires_call = context.get("require_call_followup", False)

    should_call = (
        requires_call or
        is_urgent or
        sms_status in ["failed", "undelivered"]
    )

    logger.debug(
        f"Should make call: {should_call} "
        f"(urgent={is_urgent}, requires_call={requires_call}, sms_status={sms_status})"
    )

    return should_call


def create_communication_workflow(
    communication_data: Dict[str, Any]
) -> Workflow:
    """
    Create a multi-channel communication workflow.

    Args:
        communication_data: Communication information including:
            - recipient_phone: Phone number for SMS/call
            - recipient_email: Email address
            - message: Message content
            - subject: Email subject
            - priority: Message priority (normal, high, urgent)
            - channels: List of channels to use (default: ["sms", "email"])
            - require_call_followup: Whether to make a follow-up call
            - template: Optional template name
            - template_data: Optional template data

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.update(communication_data)

    channels = communication_data.get("channels", ["sms", "email"])
    steps = []

    # Step 1: Send SMS (if enabled)
    if "sms" in channels:
        steps.append(
            WorkflowStep(
                name="send_sms",
                agent="communications",
                action="execute",
                params={
                    "type": "send_sms",
                    "communication_type": "sms",
                    "recipient": communication_data.get("recipient_phone"),
                    "message": communication_data.get("message", ""),
                    "template": communication_data.get("template"),
                    "template_data": communication_data.get("template_data", {})
                },
                retry_count=2,
                timeout=15.0,
                on_success=on_sms_sent
            )
        )

    # Step 2: Send email (if enabled)
    if "email" in channels:
        steps.append(
            WorkflowStep(
                name="send_email",
                agent="communications",
                action="execute",
                params={
                    "type": "send_email",
                    "communication_type": "email",
                    "recipient": communication_data.get("recipient_email"),
                    "subject": communication_data.get("subject", "Notification"),
                    "message": communication_data.get("message", ""),
                    "template": communication_data.get("template"),
                    "template_data": communication_data.get("template_data", {}),
                    "attachments": communication_data.get("attachments", [])
                },
                retry_count=2,
                timeout=20.0,
                condition=should_send_email,
                on_success=on_email_sent
            )
        )

    # Step 3: Make follow-up call (conditional)
    if "call" in channels or communication_data.get("require_call_followup"):
        steps.append(
            WorkflowStep(
                name="make_call",
                agent="communications",
                action="execute",
                params={
                    "type": "make_call",
                    "communication_type": "phone",
                    "recipient": communication_data.get("recipient_phone"),
                    "message": communication_data.get("call_message") or communication_data.get("message"),
                    "twiml_template": communication_data.get("twiml_template")
                },
                retry_count=1,
                timeout=60.0,
                condition=should_make_call,
                on_success=on_call_made
            )
        )

    # Create workflow
    workflow = Workflow(
        name="communication_workflow",
        description=f"Multi-channel communication via {', '.join(channels)}",
        steps=steps,
        context=context,
        parallel=False,  # Sequential by default
        stop_on_error=False  # Continue even if one channel fails
    )

    logger.info(
        f"Created communication workflow with {len(steps)} steps "
        f"using channels: {channels}"
    )

    return workflow


def create_notification_cascade_workflow(
    notification_data: Dict[str, Any]
) -> Workflow:
    """
    Create a cascading notification workflow.

    Tries channels in order until one succeeds:
    1. SMS
    2. Email
    3. Phone call

    Args:
        notification_data: Notification information

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.update(notification_data)

    def should_try_email(ctx: WorkflowContext) -> bool:
        """Try email if SMS failed."""
        sms_status = ctx.get("sms_status")
        failed = sms_status in ["failed", "undelivered", None]
        logger.debug(f"Should try email: {failed}")
        return failed

    def should_try_call(ctx: WorkflowContext) -> bool:
        """Try call if both SMS and email failed."""
        sms_status = ctx.get("sms_status")
        email_status = ctx.get("email_status")
        both_failed = (
            sms_status in ["failed", "undelivered", None] and
            email_status in ["failed", "undelivered", None]
        )
        logger.debug(f"Should try call: {both_failed}")
        return both_failed

    steps = [
        # Try 1: SMS
        WorkflowStep(
            name="try_sms",
            agent="communications",
            action="execute",
            params={
                "type": "send_sms",
                "communication_type": "sms",
                "recipient": notification_data.get("recipient_phone"),
                "message": notification_data.get("message")
            },
            retry_count=1,
            timeout=10.0,
            on_success=on_sms_sent
        ),

        # Try 2: Email (if SMS failed)
        WorkflowStep(
            name="try_email",
            agent="communications",
            action="execute",
            params={
                "type": "send_email",
                "communication_type": "email",
                "recipient": notification_data.get("recipient_email"),
                "subject": notification_data.get("subject", "Important Notification"),
                "message": notification_data.get("message")
            },
            retry_count=1,
            timeout=15.0,
            condition=should_try_email,
            on_success=on_email_sent
        ),

        # Try 3: Call (if both failed)
        WorkflowStep(
            name="try_call",
            agent="communications",
            action="execute",
            params={
                "type": "make_call",
                "communication_type": "phone",
                "recipient": notification_data.get("recipient_phone"),
                "message": notification_data.get("message")
            },
            retry_count=1,
            timeout=60.0,
            condition=should_try_call,
            on_success=on_call_made
        ),
    ]

    workflow = Workflow(
        name="notification_cascade_workflow",
        description="Cascading notification across SMS → Email → Call",
        steps=steps,
        context=context,
        parallel=False,
        stop_on_error=False
    )

    logger.info("Created notification cascade workflow")

    return workflow


def create_bulk_notification_workflow(
    recipients: List[Dict[str, Any]],
    message_data: Dict[str, Any]
) -> Workflow:
    """
    Create a workflow for bulk notifications.

    Args:
        recipients: List of recipient dicts with phone/email
        message_data: Message content and settings

    Returns:
        Workflow instance ready to execute
    """
    context = WorkflowContext()
    context.set("total_recipients", len(recipients))
    context.set("message_data", message_data)

    channel = message_data.get("channel", "sms")
    steps = []

    for i, recipient in enumerate(recipients):
        # Create a step for each recipient
        if channel == "sms":
            steps.append(
                WorkflowStep(
                    name=f"send_{channel}_to_{i}",
                    agent="communications",
                    action="execute",
                    params={
                        "type": "send_sms",
                        "communication_type": "sms",
                        "recipient": recipient.get("phone"),
                        "message": message_data.get("message"),
                        "template": message_data.get("template"),
                        "template_data": {**message_data.get("template_data", {}), **recipient}
                    },
                    retry_count=1,
                    timeout=10.0
                )
            )
        elif channel == "email":
            steps.append(
                WorkflowStep(
                    name=f"send_{channel}_to_{i}",
                    agent="communications",
                    action="execute",
                    params={
                        "type": "send_email",
                        "communication_type": "email",
                        "recipient": recipient.get("email"),
                        "subject": message_data.get("subject"),
                        "message": message_data.get("message"),
                        "template": message_data.get("template"),
                        "template_data": {**message_data.get("template_data", {}), **recipient}
                    },
                    retry_count=1,
                    timeout=15.0
                )
            )

    workflow = Workflow(
        name="bulk_notification_workflow",
        description=f"Send {channel} to {len(recipients)} recipients",
        steps=steps,
        context=context,
        parallel=True,  # Send in parallel for efficiency
        stop_on_error=False  # Continue even if some fail
    )

    logger.info(
        f"Created bulk notification workflow for {len(recipients)} recipients "
        f"via {channel}"
    )

    return workflow
