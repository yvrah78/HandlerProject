"""
Communications Agent for Project Handler.
Handles phone calls, SMS, WhatsApp, and email communications via Twilio and SendGrid.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, IntegrationError
from src.integrations.twilio_client import TwilioClient
from src.integrations.sendgrid_client import SendGridClient


class CommunicationsAgent(BaseAgent):
    """
    Agent responsible for all external communications.

    Integrations:
    - Twilio: Phone calls, SMS, WhatsApp
    - SendGrid: Email communications

    Capabilities:
    - Automated phone calls with TTS
    - SMS notifications
    - WhatsApp messages
    - Email delivery (HTML/text)
    - Template-based emails
    - Bulk communications
    - Communication tracking
    """

    def __init__(self):
        """Initialize Communications Agent with Twilio and SendGrid clients."""
        super().__init__(
            name="communications",
            description="Handles phone calls, SMS, WhatsApp, and email communications"
        )

        # Initialize integration clients
        self.twilio = TwilioClient()
        self.sendgrid = SendGridClient()

        # Track communication status
        self.stats = {
            "total_sent": 0,
            "sms_sent": 0,
            "calls_made": 0,
            "emails_sent": 0,
            "whatsapp_sent": 0,
            "failed": 0
        }

        self.logger.info(
            f"Communications Agent initialized - "
            f"Twilio: {self.twilio.enabled}, SendGrid: {self.sendgrid.enabled}"
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process communication request.

        Args:
            input_data: Communication request with type and details

        Returns:
            Dict[str, Any]: Communication result with status

        Raises:
            ValidationError: If input is invalid
            IntegrationError: If communication fails
        """
        await self.validate_input(input_data)

        comm_type = input_data.get("communication_type")
        self.logger.info(f"Processing {comm_type} communication")

        # Route to appropriate handler
        if comm_type == "sms":
            result = await self.send_sms(input_data)
        elif comm_type == "phone":
            result = await self.make_call(input_data)
        elif comm_type == "email":
            result = await self.send_email(input_data)
        elif comm_type == "whatsapp":
            result = await self.send_whatsapp(input_data)
        else:
            raise ValidationError(
                f"Unknown communication type: {comm_type}",
                details={"received": comm_type}
            )

        # Update statistics
        self.stats["total_sent"] += 1
        if result.get("status") in ["sent", "queued", "initiated"]:
            self.stats[f"{comm_type}_sent"] = self.stats.get(f"{comm_type}_sent", 0) + 1
        else:
            self.stats["failed"] += 1

        return result

    async def send_sms(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS via Twilio.

        Args:
            data: Must contain 'recipient' and 'message'

        Returns:
            dict: SMS delivery result
        """
        recipient = data.get("recipient")
        message = data.get("message")
        from_number = data.get("from_number")

        self.logger.info(f"Sending SMS to {recipient}")

        try:
            result = await self.twilio.send_sms(
                to=recipient,
                message=message,
                from_=from_number
            )
            return {
                "communication_type": "sms",
                "status": "sent",
                "recipient": recipient,
                "message_sid": result.get("sid"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except IntegrationError as e:
            self.logger.error(f"Failed to send SMS: {str(e)}")
            return {
                "communication_type": "sms",
                "status": "failed",
                "recipient": recipient,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def send_whatsapp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio.

        Args:
            data: Must contain 'recipient' and 'message'

        Returns:
            dict: WhatsApp delivery result
        """
        recipient = data.get("recipient")
        message = data.get("message")
        from_number = data.get("from_number")
        media_urls = data.get("media_urls")

        self.logger.info(f"Sending WhatsApp to {recipient}")

        try:
            result = await self.twilio.send_whatsapp(
                to=recipient,
                message=message,
                from_=from_number,
                media_urls=media_urls
            )
            return {
                "communication_type": "whatsapp",
                "status": "sent",
                "recipient": recipient,
                "message_sid": result.get("sid"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except IntegrationError as e:
            self.logger.error(f"Failed to send WhatsApp: {str(e)}")
            return {
                "communication_type": "whatsapp",
                "status": "failed",
                "recipient": recipient,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def make_call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make phone call via Twilio.

        Args:
            data: Must contain 'recipient' and 'message'

        Returns:
            dict: Call result
        """
        recipient = data.get("recipient")
        message = data.get("message")
        from_number = data.get("from_number")
        voice = data.get("voice", "Polly.Joanna")

        self.logger.info(f"Making call to {recipient}")

        try:
            result = await self.twilio.make_call(
                to=recipient,
                message=message,
                from_=from_number,
                voice=voice
            )
            return {
                "communication_type": "phone",
                "status": "initiated",
                "recipient": recipient,
                "call_sid": result.get("sid"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except IntegrationError as e:
            self.logger.error(f"Failed to make call: {str(e)}")
            return {
                "communication_type": "phone",
                "status": "failed",
                "recipient": recipient,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def send_email(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email via SendGrid.

        Args:
            data: Must contain 'recipient', 'subject', and content

        Returns:
            dict: Email delivery result
        """
        recipient = data.get("recipient")
        subject = data.get("subject")
        html_content = data.get("html_content")
        text_content = data.get("text_content")
        from_email = data.get("from_email")
        from_name = data.get("from_name")

        self.logger.info(f"Sending email to {recipient}")

        try:
            result = await self.sendgrid.send_email(
                to=recipient,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name
            )
            return {
                "communication_type": "email",
                "status": "sent",
                "recipient": recipient,
                "subject": subject,
                "message_id": result.get("message_id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except IntegrationError as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return {
                "communication_type": "email",
                "status": "failed",
                "recipient": recipient,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def send_bulk_communication(
        self,
        recipients: List[str],
        communication_type: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send communication to multiple recipients.

        Args:
            recipients: List of recipient addresses
            communication_type: Type of communication (sms, email, whatsapp)
            message: Message content
            **kwargs: Additional parameters

        Returns:
            dict: Bulk communication results
        """
        self.logger.info(f"Sending bulk {communication_type} to {len(recipients)} recipients")

        results = []
        for recipient in recipients:
            data = {
                "communication_type": communication_type,
                "recipient": recipient,
                "message": message,
                **kwargs
            }
            result = await self.process(data)
            results.append(result)

        successful = sum(1 for r in results if r.get("status") in ["sent", "queued", "initiated"])
        failed = len(results) - successful

        return {
            "total": len(recipients),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate communication input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ["communication_type", "recipient"]

        for field in required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"received_keys": list(input_data.keys())}
                )

        valid_types = ["phone", "sms", "email", "whatsapp"]
        if input_data["communication_type"] not in valid_types:
            raise ValidationError(
                f"Invalid communication type. Must be one of: {valid_types}",
                details={"received": input_data["communication_type"]}
            )

        # Validate message exists for all types
        if "message" not in input_data and "subject" not in input_data:
            raise ValidationError(
                "Either 'message' or 'subject' is required",
                details={"received_keys": list(input_data.keys())}
            )

        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status including integration status.

        Returns:
            dict: Agent and integration status
        """
        return {
            "agent_name": self.name,
            "enabled": True,
            "integrations": {
                "twilio": self.twilio.get_status(),
                "sendgrid": self.sendgrid.get_status()
            },
            "statistics": self.stats,
            "capabilities": {
                "sms": self.twilio.enabled,
                "phone": self.twilio.enabled,
                "whatsapp": self.twilio.enabled,
                "email": self.sendgrid.enabled,
                "bulk_communications": True
            }
        }
