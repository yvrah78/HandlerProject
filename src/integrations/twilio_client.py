"""
Twilio integration client for Project Handler.
Handles phone calls, SMS, and WhatsApp via Twilio API.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from functools import wraps

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.exceptions import IntegrationError

logger = get_logger(__name__)
settings = get_settings()


def async_twilio_operation(func):
    """Decorator to run Twilio operations in thread pool (they're sync)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


class TwilioClient:
    """Client for Twilio API integration."""

    def __init__(self):
        """Initialize Twilio client with credentials."""
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.logger = logger
        self.enabled = False
        self.client = None
        self.from_phone = None
        self.from_whatsapp = None

        # Initialize Twilio client if credentials are available
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                self.logger.info("Twilio client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Twilio client: {str(e)}")
                self.enabled = False
        else:
            self.logger.info("Twilio credentials not provided - running in disabled mode")

    def _check_enabled(self):
        """Check if Twilio is enabled and raise error if not."""
        if not self.enabled:
            raise IntegrationError(
                "Twilio integration is not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.",
                integration_name="twilio"
            )

    async def send_sms(
        self,
        to: str,
        message: str,
        from_: Optional[str] = None,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send SMS message via Twilio.

        Args:
            to: Recipient phone number (E.164 format, e.g., +1234567890)
            message: Message content (max 1600 chars)
            from_: Optional sender phone number (uses default if not provided)
            media_urls: Optional list of media URLs to send (MMS)

        Returns:
            dict: Message delivery information with status and SID

        Raises:
            IntegrationError: If SMS sending fails
        """
        self._check_enabled()
        self.logger.info(f"Sending SMS to {to}")

        if not to.startswith('+'):
            raise IntegrationError(
                f"Phone number must be in E.164 format (e.g., +1234567890), got: {to}",
                integration_name="twilio"
            )

        try:
            # Run Twilio operation in thread pool (Twilio SDK is synchronous)
            loop = asyncio.get_event_loop()
            message_obj = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    to=to,
                    from_=from_ or self.from_phone,
                    body=message,
                    media_url=media_urls
                )
            )

            return {
                "sid": message_obj.sid,
                "status": message_obj.status,
                "to": to,
                "from": message_obj.from_,
                "body": message,
                "date_created": message_obj.date_created.isoformat() if message_obj.date_created else None,
                "price": message_obj.price,
                "price_unit": message_obj.price_unit,
                "num_media": message_obj.num_media,
                "error_code": message_obj.error_code,
                "error_message": message_obj.error_message
            }

        except TwilioRestException as e:
            self.logger.error(f"Twilio API error: {e.msg} (Code: {e.code})")
            raise IntegrationError(
                f"Failed to send SMS: {e.msg} (Code: {e.code})",
                integration_name="twilio"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error sending SMS: {str(e)}")
            raise IntegrationError(
                f"Failed to send SMS: {str(e)}",
                integration_name="twilio"
            )

    async def send_whatsapp(
        self,
        to: str,
        message: str,
        from_: Optional[str] = None,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio.

        Args:
            to: Recipient phone number (E.164 format, e.g., +1234567890)
            message: Message content
            from_: Optional sender WhatsApp number (uses default if not provided)
            media_urls: Optional list of media URLs to send

        Returns:
            dict: Message delivery information

        Raises:
            IntegrationError: If WhatsApp message sending fails
        """
        self._check_enabled()
        self.logger.info(f"Sending WhatsApp message to {to}")

        # WhatsApp numbers must be prefixed with 'whatsapp:'
        to_whatsapp = f"whatsapp:{to}" if not to.startswith('whatsapp:') else to
        from_whatsapp = from_ or self.from_whatsapp or f"whatsapp:{self.from_phone}"

        try:
            loop = asyncio.get_event_loop()
            message_obj = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    to=to_whatsapp,
                    from_=from_whatsapp,
                    body=message,
                    media_url=media_urls
                )
            )

            return {
                "sid": message_obj.sid,
                "status": message_obj.status,
                "to": to_whatsapp,
                "from": message_obj.from_,
                "body": message,
                "date_created": message_obj.date_created.isoformat() if message_obj.date_created else None,
                "num_media": message_obj.num_media
            }

        except TwilioRestException as e:
            self.logger.error(f"Twilio WhatsApp error: {e.msg} (Code: {e.code})")
            raise IntegrationError(
                f"Failed to send WhatsApp: {e.msg} (Code: {e.code})",
                integration_name="twilio"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error sending WhatsApp: {str(e)}")
            raise IntegrationError(
                f"Failed to send WhatsApp: {str(e)}",
                integration_name="twilio"
            )

    async def make_call(
        self,
        to: str,
        message: str,
        from_: Optional[str] = None,
        voice: str = "Polly.Joanna"
    ) -> Dict[str, Any]:
        """
        Make automated phone call with text-to-speech.

        Args:
            to: Recipient phone number (E.164 format)
            message: Message to speak via TTS
            from_: Optional caller phone number
            voice: Voice to use for TTS (default: Polly.Joanna)

        Returns:
            dict: Call information with status and SID

        Raises:
            IntegrationError: If call initiation fails
        """
        self._check_enabled()
        self.logger.info(f"Making call to {to}")

        if not to.startswith('+'):
            raise IntegrationError(
                f"Phone number must be in E.164 format (e.g., +1234567890), got: {to}",
                integration_name="twilio"
            )

        try:
            # Create TwiML for text-to-speech
            twiml = f'<Response><Say voice="{voice}">{message}</Say></Response>'

            loop = asyncio.get_event_loop()
            call_obj = await loop.run_in_executor(
                None,
                lambda: self.client.calls.create(
                    to=to,
                    from_=from_ or self.from_phone,
                    twiml=twiml
                )
            )

            return {
                "sid": call_obj.sid,
                "status": call_obj.status,
                "to": to,
                "from": call_obj.from_,
                "duration": call_obj.duration,
                "date_created": call_obj.date_created.isoformat() if call_obj.date_created else None,
                "price": call_obj.price,
                "price_unit": call_obj.price_unit
            }

        except TwilioRestException as e:
            self.logger.error(f"Twilio call error: {e.msg} (Code: {e.code})")
            raise IntegrationError(
                f"Failed to make call: {e.msg} (Code: {e.code})",
                integration_name="twilio"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error making call: {str(e)}")
            raise IntegrationError(
                f"Failed to make call: {str(e)}",
                integration_name="twilio"
            )

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get status of a sent message.

        Args:
            message_sid: Twilio message SID

        Returns:
            dict: Message status information

        Raises:
            IntegrationError: If status check fails
        """
        self._check_enabled()
        self.logger.info(f"Checking status for message {message_sid}")

        try:
            loop = asyncio.get_event_loop()
            message_obj = await loop.run_in_executor(
                None,
                lambda: self.client.messages(message_sid).fetch()
            )

            return {
                "sid": message_obj.sid,
                "status": message_obj.status,
                "to": message_obj.to,
                "from": message_obj.from_,
                "date_created": message_obj.date_created.isoformat() if message_obj.date_created else None,
                "date_sent": message_obj.date_sent.isoformat() if message_obj.date_sent else None,
                "error_code": message_obj.error_code,
                "error_message": message_obj.error_message
            }

        except TwilioRestException as e:
            self.logger.error(f"Twilio status check error: {e.msg}")
            raise IntegrationError(
                f"Failed to get message status: {e.msg}",
                integration_name="twilio"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to get message status: {str(e)}",
                integration_name="twilio"
            )

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get status of a call.

        Args:
            call_sid: Twilio call SID

        Returns:
            dict: Call status information

        Raises:
            IntegrationError: If status check fails
        """
        self._check_enabled()
        self.logger.info(f"Checking status for call {call_sid}")

        try:
            loop = asyncio.get_event_loop()
            call_obj = await loop.run_in_executor(
                None,
                lambda: self.client.calls(call_sid).fetch()
            )

            return {
                "sid": call_obj.sid,
                "status": call_obj.status,
                "to": call_obj.to,
                "from": call_obj.from_,
                "duration": call_obj.duration,
                "date_created": call_obj.date_created.isoformat() if call_obj.date_created else None,
                "price": call_obj.price,
                "price_unit": call_obj.price_unit
            }

        except TwilioRestException as e:
            self.logger.error(f"Twilio call status error: {e.msg}")
            raise IntegrationError(
                f"Failed to get call status: {e.msg}",
                integration_name="twilio"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to get call status: {str(e)}",
                integration_name="twilio"
            )

    async def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        from_: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Send SMS to multiple recipients.

        Args:
            recipients: List of phone numbers
            message: Message content
            from_: Optional sender phone number

        Returns:
            list: List of message delivery information for each recipient

        Raises:
            IntegrationError: If bulk sending fails
        """
        self._check_enabled()
        self.logger.info(f"Sending bulk SMS to {len(recipients)} recipients")

        results = []
        for recipient in recipients:
            try:
                result = await self.send_sms(to=recipient, message=message, from_=from_)
                results.append(result)
            except IntegrationError as e:
                self.logger.error(f"Failed to send SMS to {recipient}: {str(e)}")
                results.append({
                    "to": recipient,
                    "status": "failed",
                    "error": str(e)
                })

        return results

    def configure_phone_numbers(self, sms_number: str, whatsapp_number: Optional[str] = None):
        """
        Configure default phone numbers for sending.

        Args:
            sms_number: Default phone number for SMS/calls (E.164 format)
            whatsapp_number: Optional WhatsApp-enabled number
        """
        self.from_phone = sms_number
        self.from_whatsapp = f"whatsapp:{whatsapp_number}" if whatsapp_number else None
        self.logger.info(f"Configured Twilio phone numbers: SMS={sms_number}, WhatsApp={whatsapp_number}")

    async def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Validate and lookup phone number information.

        Args:
            phone_number: Phone number to validate (E.164 format)

        Returns:
            dict: Phone number information (carrier, type, etc.)

        Raises:
            IntegrationError: If validation fails
        """
        self._check_enabled()
        self.logger.info(f"Validating phone number {phone_number}")

        try:
            loop = asyncio.get_event_loop()
            lookup = await loop.run_in_executor(
                None,
                lambda: self.client.lookups.v1.phone_numbers(phone_number).fetch()
            )

            return {
                "phone_number": lookup.phone_number,
                "country_code": lookup.country_code,
                "national_format": lookup.national_format,
                "valid": True
            }

        except TwilioRestException as e:
            if e.code == 20404:
                return {
                    "phone_number": phone_number,
                    "valid": False,
                    "error": "Invalid phone number"
                }
            raise IntegrationError(
                f"Failed to validate phone number: {e.msg}",
                integration_name="twilio"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to validate phone number: {str(e)}",
                integration_name="twilio"
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get Twilio client status.

        Returns:
            dict: Client configuration and status
        """
        return {
            "enabled": self.enabled,
            "configured": bool(self.account_sid and self.auth_token),
            "account_sid": self.account_sid[:8] + "..." if self.account_sid else None,
            "from_phone": self.from_phone,
            "from_whatsapp": self.from_whatsapp,
            "capabilities": {
                "sms": self.enabled,
                "voice": self.enabled,
                "whatsapp": self.enabled and bool(self.from_whatsapp)
            }
        }
