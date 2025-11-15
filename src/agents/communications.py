"""
Communications Agent for Project Handler - AI-powered version.
Handles phone calls, SMS, and email communications via Twilio and SendGrid.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, AgentError
from src.core.logging import get_logger

logger = get_logger("agent.communications")


class CommunicationsAgent(BaseAgent):
    """
    Intelligent agent responsible for all external communications.

    Capabilities:
    - SMS notifications via Twilio
    - Phone calls via Twilio (TwiML)
    - Email communications via SendGrid
    - Customer follow-ups and reminders
    - Automated notifications for booking status
    - Multi-channel communication campaigns

    Modes:
    - Demo mode: Simulates communications without API calls
    - Live mode: Uses real Twilio/SendGrid APIs
    """

    def __init__(self):
        super().__init__(
            name="communications",
            description="AI-powered communications agent handling SMS, calls, and emails"
        )

        # Initialize integrations (lazy loading)
        self._twilio_client = None
        self._sendgrid_client = None

        # Communication history
        self.communication_history: List[Dict[str, Any]] = []

        # Check for API keys
        self.demo_mode = self._check_demo_mode()

    def _check_demo_mode(self) -> bool:
        """Check if we're in demo mode (no API keys)."""
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        sendgrid_key = os.getenv("SENDGRID_API_KEY")

        if not twilio_sid and not sendgrid_key:
            logger.warning("No communication API keys found - running in demo mode")
            return True

        return False

    @property
    def twilio_client(self):
        """Lazy load Twilio client."""
        if self._twilio_client is None and not self.demo_mode:
            try:
                from twilio.rest import Client
                account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                auth_token = os.getenv("TWILIO_AUTH_TOKEN")
                from_number = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

                if account_sid and auth_token:
                    self._twilio_client = Client(account_sid, auth_token)
                    self.twilio_from_number = from_number
                    logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
                self.demo_mode = True

        return self._twilio_client

    @property
    def sendgrid_client(self):
        """Lazy load SendGrid client."""
        if self._sendgrid_client is None and not self.demo_mode:
            try:
                from sendgrid import SendGridAPIClient
                api_key = os.getenv("SENDGRID_API_KEY")

                if api_key:
                    self._sendgrid_client = SendGridAPIClient(api_key)
                    logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
                self.demo_mode = True

        return self._sendgrid_client

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process communication request with intelligence.

        Args:
            input_data: Communication request data

        Returns:
            Dict[str, Any]: Communication result
        """
        comm_type = input_data.get("communication_type", "").lower()

        # Route to appropriate handler
        if comm_type == "sms":
            return await self._handle_sms(input_data)
        elif comm_type == "email":
            return await self._handle_email(input_data)
        elif comm_type == "call":
            return await self._handle_call(input_data)
        elif comm_type == "notification":
            return await self._handle_notification(input_data)
        else:
            return await self._handle_generic(input_data)

    async def _handle_sms(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SMS communication."""
        to_number = input_data.get("to") or input_data.get("recipient")
        message = input_data.get("message")

        self.logger.info(f"Sending SMS to {to_number}")

        if self.demo_mode or not self.twilio_client:
            # Demo mode response
            result = {
                "status": "demo_sent",
                "to": to_number,
                "message": message,
                "channel": "sms",
                "note": "Demo mode - no actual SMS sent. Configure TWILIO_ACCOUNT_SID to enable."
            }
        else:
            try:
                # Real Twilio SMS
                sms = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_from_number,
                    to=to_number
                )

                result = {
                    "status": "sent",
                    "sid": sms.sid,
                    "to": to_number,
                    "from": self.twilio_from_number,
                    "channel": "sms",
                    "message_preview": message[:50] + "..." if len(message) > 50 else message
                }

                logger.info(f"SMS sent successfully: {sms.sid}")

            except Exception as e:
                logger.error(f"Failed to send SMS: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "channel": "sms"
                }

        # Save to history
        self._add_to_history("sms", to_number, result)

        return result

    async def _handle_email(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email communication."""
        to_email = input_data.get("to") or input_data.get("recipient")
        subject = input_data.get("subject", "Notification from Project Handler")
        message = input_data.get("message") or input_data.get("body")
        from_email = input_data.get("from_email", "noreply@projecthandler.com")

        self.logger.info(f"Sending email to {to_email}")

        if self.demo_mode or not self.sendgrid_client:
            # Demo mode response
            result = {
                "status": "demo_sent",
                "to": to_email,
                "subject": subject,
                "channel": "email",
                "note": "Demo mode - no actual email sent. Configure SENDGRID_API_KEY to enable."
            }
        else:
            try:
                from sendgrid.helpers.mail import Mail

                mail = Mail(
                    from_email=from_email,
                    to_emails=to_email,
                    subject=subject,
                    html_content=f"<html><body><p>{message}</p></body></html>"
                )

                response = self.sendgrid_client.send(mail)

                result = {
                    "status": "sent",
                    "status_code": response.status_code,
                    "to": to_email,
                    "subject": subject,
                    "channel": "email"
                }

                logger.info(f"Email sent successfully to {to_email}")

            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "channel": "email"
                }

        # Save to history
        self._add_to_history("email", to_email, result)

        return result

    async def _handle_call(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle phone call communication."""
        to_number = input_data.get("to") or input_data.get("recipient")
        message = input_data.get("message")

        self.logger.info(f"Making call to {to_number}")

        if self.demo_mode or not self.twilio_client:
            # Demo mode response
            result = {
                "status": "demo_initiated",
                "to": to_number,
                "message": message,
                "channel": "call",
                "note": "Demo mode - no actual call made. Configure TWILIO_ACCOUNT_SID to enable."
            }
        else:
            try:
                # Generate TwiML for call
                from twilio.twiml.voice_response import VoiceResponse

                response = VoiceResponse()
                response.say(message, voice='alice', language='en-US')

                # Make call (requires TwiML URL setup)
                # Note: This is simplified - in production you'd need a TwiML endpoint
                call = self.twilio_client.calls.create(
                    to=to_number,
                    from_=self.twilio_from_number,
                    twiml=str(response)
                )

                result = {
                    "status": "initiated",
                    "sid": call.sid,
                    "to": to_number,
                    "from": self.twilio_from_number,
                    "channel": "call"
                }

                logger.info(f"Call initiated successfully: {call.sid}")

            except Exception as e:
                logger.error(f"Failed to make call: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "channel": "call"
                }

        # Save to history
        self._add_to_history("call", to_number, result)

        return result

    async def _handle_notification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-channel notification (smart routing)."""
        recipient = input_data.get("recipient")
        message = input_data.get("message")
        channels = input_data.get("channels", ["sms"])  # Default to SMS

        results = []

        # Send via all requested channels
        for channel in channels:
            if channel == "sms":
                result = await self._handle_sms({
                    "to": recipient,
                    "message": message
                })
            elif channel == "email":
                result = await self._handle_email({
                    "to": recipient,
                    "message": message,
                    "subject": "Notification from Project Handler"
                })
            elif channel == "call":
                result = await self._handle_call({
                    "to": recipient,
                    "message": message
                })

            results.append(result)

        return {
            "status": "multi_channel_sent",
            "channels": channels,
            "results": results,
            "recipient": recipient
        }

    async def _handle_generic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic communication request."""
        return {
            "status": "processed",
            "message": "Generic communication handler",
            "data": input_data
        }

    def _add_to_history(self, channel: str, recipient: str, result: Dict[str, Any]):
        """Add communication to history."""
        self.communication_history.append({
            "channel": channel,
            "recipient": recipient,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 100 communications
        if len(self.communication_history) > 100:
            self.communication_history = self.communication_history[-100:]

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
        if not isinstance(input_data, dict):
            raise ValidationError(
                "Input must be a dictionary",
                details={"received_type": type(input_data).__name__}
            )

        # Must have communication type
        comm_type = input_data.get("communication_type")
        if not comm_type:
            raise ValidationError(
                "Missing required field: communication_type",
                details={"received_keys": list(input_data.keys())}
            )

        valid_types = ["sms", "email", "call", "notification"]
        if comm_type.lower() not in valid_types:
            raise ValidationError(
                f"Invalid communication type. Must be one of: {valid_types}",
                details={"received": comm_type}
            )

        # Must have recipient
        recipient = input_data.get("to") or input_data.get("recipient")
        if not recipient:
            raise ValidationError(
                "Missing required field: to or recipient",
                details={"received_keys": list(input_data.keys())}
            )

        # Must have message (except for notification which can batch)
        if comm_type.lower() != "notification":
            message = input_data.get("message") or input_data.get("body")
            if not message:
                raise ValidationError(
                    "Missing required field: message or body",
                    details={"communication_type": comm_type}
                )

        return True

    def get_communication_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get communication history."""
        if limit:
            return self.communication_history[-limit:]
        return self.communication_history

    def clear_history(self):
        """Clear communication history."""
        self.communication_history = []
        logger.info("Communication history cleared")

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced agent status."""
        base_status = super().get_status()
        base_status.update({
            "demo_mode": self.demo_mode,
            "twilio_enabled": self.twilio_client is not None,
            "sendgrid_enabled": self.sendgrid_client is not None,
            "total_communications": len(self.communication_history),
            "supported_channels": ["sms", "email", "call", "notification"]
        })
        return base_status
