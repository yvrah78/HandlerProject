"""
Communication tools for Communications Agent.
Tools for SMS, email, WhatsApp, and communication management.
"""
from typing import Dict, Any, Optional, List
from pydantic import Field
from datetime import datetime

from src.agents.tools.base_tool import BaseTool, ToolInput, ToolOutput
from src.core.logging import get_logger
from src.core.database import get_db
from src.models.communication_log import CommunicationLog, CommunicationType, CommunicationStatus

logger = get_logger(__name__)


class SendSMSInput(ToolInput):
    """Input for send_sms tool."""

    phone: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="Message content")
    customer_id: Optional[int] = Field(None, description="Customer ID (optional)")


class SendEmailInput(ToolInput):
    """Input for send_email tool."""

    email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    customer_id: Optional[int] = Field(None, description="Customer ID (optional)")


class SendWhatsAppInput(ToolInput):
    """Input for send_whatsapp tool."""

    phone: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="Message content")
    template_name: Optional[str] = Field(None, description="WhatsApp template name")


class GetCommunicationHistoryInput(ToolInput):
    """Input for get_communication_history tool."""

    customer_id: Optional[int] = Field(None, description="Customer ID")
    limit: int = Field(10, description="Number of records to retrieve")


class SendSMSTool(BaseTool):
    """Tool for sending SMS messages."""

    def __init__(self):
        super().__init__(
            name="send_sms",
            description="Send SMS message to customer",
            input_schema=SendSMSInput,
            required_permissions=["send:sms"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute send SMS."""
        try:
            phone = input_data.get("phone")
            message = input_data.get("message")
            customer_id = input_data.get("customer_id")

            # Log communication
            db = get_db()
            comm_log = CommunicationLog(
                customer_id=customer_id,
                type=CommunicationType.SMS,
                phone=phone,
                message=message,
                status=CommunicationStatus.PENDING,
            )

            db.add(comm_log)
            db.commit()
            db.refresh(comm_log)

            logger.info(f"SMS queued to {phone}: {message[:50]}...")

            return ToolOutput(
                success=True,
                data={
                    "message_id": comm_log.id,
                    "phone": phone,
                    "status": "queued",
                    "timestamp": comm_log.created_at.isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class SendEmailTool(BaseTool):
    """Tool for sending emails."""

    def __init__(self):
        super().__init__(
            name="send_email",
            description="Send email to customer",
            input_schema=SendEmailInput,
            required_permissions=["send:email"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute send email."""
        try:
            email = input_data.get("email")
            subject = input_data.get("subject")
            body = input_data.get("body")
            customer_id = input_data.get("customer_id")

            # Log communication
            db = get_db()
            comm_log = CommunicationLog(
                customer_id=customer_id,
                type=CommunicationType.EMAIL,
                email=email,
                subject=subject,
                message=body,
                status=CommunicationStatus.PENDING,
            )

            db.add(comm_log)
            db.commit()
            db.refresh(comm_log)

            logger.info(f"Email queued to {email}: {subject}")

            return ToolOutput(
                success=True,
                data={
                    "message_id": comm_log.id,
                    "email": email,
                    "subject": subject,
                    "status": "queued",
                    "timestamp": comm_log.created_at.isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class SendWhatsAppTool(BaseTool):
    """Tool for sending WhatsApp messages."""

    def __init__(self):
        super().__init__(
            name="send_whatsapp",
            description="Send WhatsApp message to customer",
            input_schema=SendWhatsAppInput,
            required_permissions=["send:whatsapp"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute send WhatsApp."""
        try:
            phone = input_data.get("phone")
            message = input_data.get("message")
            template_name = input_data.get("template_name")

            # Log communication
            db = get_db()
            comm_log = CommunicationLog(
                type=CommunicationType.WHATSAPP,
                phone=phone,
                message=message,
                status=CommunicationStatus.PENDING,
            )

            db.add(comm_log)
            db.commit()
            db.refresh(comm_log)

            logger.info(f"WhatsApp queued to {phone}: {message[:50]}...")

            return ToolOutput(
                success=True,
                data={
                    "message_id": comm_log.id,
                    "phone": phone,
                    "template": template_name,
                    "status": "queued",
                    "timestamp": comm_log.created_at.isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class GetCommunicationHistoryTool(BaseTool):
    """Tool for retrieving communication history."""

    def __init__(self):
        super().__init__(
            name="get_communication_history",
            description="Get communication history for customer",
            input_schema=GetCommunicationHistoryInput,
            required_permissions=["read:communications"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute get communication history."""
        try:
            customer_id = input_data.get("customer_id")
            limit = input_data.get("limit", 10)

            db = get_db()
            query = db.query(CommunicationLog)

            if customer_id:
                query = query.filter(CommunicationLog.customer_id == customer_id)

            communications = query.order_by(
                CommunicationLog.created_at.desc()
            ).limit(limit).all()

            history = [
                {
                    "id": comm.id,
                    "type": comm.type,
                    "status": comm.status,
                    "timestamp": comm.created_at.isoformat(),
                    "contact": comm.phone or comm.email,
                }
                for comm in communications
            ]

            return ToolOutput(
                success=True,
                data={
                    "count": len(history),
                    "communications": history,
                },
            )

        except Exception as e:
            logger.error(f"Error retrieving communication history: {str(e)}")
            return ToolOutput(success=False, error=str(e))


def register_communication_tools(registry) -> None:
    """
    Register all communication tools in the registry.

    Args:
        registry: ToolRegistry instance
    """
    registry.register(SendSMSTool(), category="communications")
    registry.register(SendEmailTool(), category="communications")
    registry.register(SendWhatsAppTool(), category="communications")
    registry.register(GetCommunicationHistoryTool(), category="communications")
    logger.info("Communication tools registered")
