"""
Twilio integration client for Project Handler.
Handles phone calls and SMS via Twilio API.

Rate Limits:
- SMS: 1 request per second per account (configurable)
- Voice: Same as SMS
- Best practice: Use retry logic with exponential backoff

Documentation: https://www.twilio.com/docs/usage/api
"""
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from src.core.config import get_settings
from src.core.exceptions import IntegrationError
from src.integrations.base import BaseIntegration

settings = get_settings()


class TwilioClient(BaseIntegration):
    """
    Client for Twilio API integration.

    Provides SMS and voice call functionality with automatic retry logic
    and comprehensive error handling.
    """

    def __init__(self):
        """Initialize Twilio client with credentials from settings."""
        super().__init__("twilio")

        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = getattr(settings, 'twilio_phone_number', None)

        # Validate configuration
        self._validate_config()

        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            self.logger.info("Twilio client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twilio client: {str(e)}")
            raise IntegrationError(
                f"Failed to initialize Twilio client: {str(e)}",
                integration_name=self.integration_name,
                details={"error": str(e)}
            )

    def _validate_config(self) -> None:
        """Validate that all required Twilio configuration is present."""
        self._check_config_value(self.account_sid, "TWILIO_ACCOUNT_SID")
        self._check_config_value(self.auth_token, "TWILIO_AUTH_TOKEN")

    async def send_sms(
        self,
        to: str,
        message: str,
        from_: Optional[str] = None,
        media_urls: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send SMS message via Twilio.

        Args:
            to: Recipient phone number (E.164 format recommended)
            message: Message content (max 1600 characters)
            from_: Sender phone number (defaults to configured number)
            media_urls: Optional list of media URLs for MMS

        Returns:
            dict: Message delivery information including SID and status

        Raises:
            IntegrationError: If SMS sending fails

        Example:
            >>> client = TwilioClient()
            >>> result = await client.send_sms(
            ...     to="+1234567890",
            ...     message="Your booking is confirmed!"
            ... )
        """
        # Sanitize phone numbers
        to_number = self._sanitize_phone_number(to)
        from_number = from_ or self.from_number

        if not from_number:
            raise IntegrationError(
                "No sender phone number configured. Set TWILIO_PHONE_NUMBER in .env",
                integration_name=self.integration_name
            )

        from_number = self._sanitize_phone_number(from_number)

        self.logger.info(f"Sending SMS to {to_number}")

        async def _send():
            try:
                params = {
                    "to": to_number,
                    "from_": from_number,
                    "body": message
                }

                if media_urls:
                    params["media_url"] = media_urls

                message_obj = self.client.messages.create(**params)

                result = {
                    "sid": message_obj.sid,
                    "status": message_obj.status,
                    "to": message_obj.to,
                    "from": message_obj.from_,
                    "date_created": message_obj.date_created.isoformat() if message_obj.date_created else None,
                    "direction": "outbound-api",
                    "num_segments": message_obj.num_segments
                }

                self._log_api_call("send_sms", {"to": to_number, "status": message_obj.status})
                return result

            except TwilioRestException as e:
                self._log_api_call("send_sms", {"to": to_number, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"Twilio API error: {e.msg}",
                    integration_name=self.integration_name,
                    details={
                        "code": e.code,
                        "status": e.status,
                        "uri": e.uri
                    }
                )

        return await self._retry_on_failure(_send, max_retries=3)

    async def make_call(
        self,
        to: str,
        message: str = None,
        twiml_url: Optional[str] = None,
        from_: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make automated phone call via Twilio.

        Args:
            to: Recipient phone number (E.164 format recommended)
            message: Message to speak (converted to TwiML if no twiml_url provided)
            twiml_url: Custom TwiML URL for call flow
            from_: Caller phone number (defaults to configured number)

        Returns:
            dict: Call information including SID and status

        Raises:
            IntegrationError: If call initiation fails

        Example:
            >>> client = TwilioClient()
            >>> result = await client.make_call(
            ...     to="+1234567890",
            ...     message="Your delivery is arriving in 10 minutes"
            ... )
        """
        if not message and not twiml_url:
            raise IntegrationError(
                "Either message or twiml_url must be provided",
                integration_name=self.integration_name
            )

        # Sanitize phone numbers
        to_number = self._sanitize_phone_number(to)
        from_number = from_ or self.from_number

        if not from_number:
            raise IntegrationError(
                "No caller phone number configured. Set TWILIO_PHONE_NUMBER in .env",
                integration_name=self.integration_name
            )

        from_number = self._sanitize_phone_number(from_number)

        self.logger.info(f"Making call to {to_number}")

        async def _make_call():
            try:
                params = {
                    "to": to_number,
                    "from_": from_number,
                }

                # If no TwiML URL provided, create simple TwiML from message
                if twiml_url:
                    params["url"] = twiml_url
                elif message:
                    # Create inline TwiML
                    twiml = f'<Response><Say voice="alice">{message}</Say></Response>'
                    params["twiml"] = twiml

                call = self.client.calls.create(**params)

                result = {
                    "sid": call.sid,
                    "status": call.status,
                    "to": call.to,
                    "from": call.from_,
                    "date_created": call.date_created.isoformat() if call.date_created else None,
                    "direction": "outbound-api"
                }

                self._log_api_call("make_call", {"to": to_number, "status": call.status})
                return result

            except TwilioRestException as e:
                self._log_api_call("make_call", {"to": to_number, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"Twilio API error: {e.msg}",
                    integration_name=self.integration_name,
                    details={
                        "code": e.code,
                        "status": e.status,
                        "uri": e.uri
                    }
                )

        return await self._retry_on_failure(_make_call, max_retries=2)

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get status of a sent message.

        Args:
            message_sid: Twilio message SID

        Returns:
            dict: Message status information

        Raises:
            IntegrationError: If status retrieval fails
        """
        self.logger.info(f"Retrieving message status for {message_sid}")

        async def _get_status():
            try:
                message = self.client.messages(message_sid).fetch()

                return {
                    "sid": message.sid,
                    "status": message.status,
                    "to": message.to,
                    "from": message.from_,
                    "error_code": message.error_code,
                    "error_message": message.error_message,
                    "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                    "date_updated": message.date_updated.isoformat() if message.date_updated else None
                }

            except TwilioRestException as e:
                raise IntegrationError(
                    f"Failed to get message status: {e.msg}",
                    integration_name=self.integration_name,
                    details={"code": e.code, "message_sid": message_sid}
                )

        return await self._retry_on_failure(_get_status, max_retries=2)

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get status of a call.

        Args:
            call_sid: Twilio call SID

        Returns:
            dict: Call status information

        Raises:
            IntegrationError: If status retrieval fails
        """
        self.logger.info(f"Retrieving call status for {call_sid}")

        async def _get_status():
            try:
                call = self.client.calls(call_sid).fetch()

                return {
                    "sid": call.sid,
                    "status": call.status,
                    "to": call.to,
                    "from": call.from_,
                    "duration": call.duration,
                    "date_created": call.date_created.isoformat() if call.date_created else None,
                    "date_updated": call.date_updated.isoformat() if call.date_updated else None
                }

            except TwilioRestException as e:
                raise IntegrationError(
                    f"Failed to get call status: {e.msg}",
                    integration_name=self.integration_name,
                    details={"code": e.code, "call_sid": call_sid}
                )

        return await self._retry_on_failure(_get_status, max_retries=2)
