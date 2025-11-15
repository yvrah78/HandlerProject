"""
LangChain tools for communication operations.

These tools allow the CommunicationsAgent to send SMS, emails,
and make phone calls through external services like Twilio and SendGrid.
"""
from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from src.core.logging import get_logger


logger = get_logger(__name__)


class SendSMSInput(BaseModel):
    """Input schema for sending SMS."""
    recipient: str = Field(description="Phone number to send SMS to (E.164 format preferred)")
    message: str = Field(description="SMS message content (max 160 chars recommended)")
    sender: Optional[str] = Field(default=None, description="Sender phone number (optional)")


class SendSMSTool(BaseTool):
    """
    Tool for sending SMS messages via Twilio.

    Allows agents to send text messages to customers for notifications,
    confirmations, and updates.
    """
    name = "send_sms"
    description = """
    Send an SMS text message to a customer's phone number.
    Use this for quick notifications, booking confirmations, or urgent updates.
    Input should include recipient phone number and message text.
    """
    args_schema: Type[BaseModel] = SendSMSInput

    def _run(
        self,
        recipient: str,
        message: str,
        sender: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Send SMS message.

        Args:
            recipient: Recipient phone number
            message: SMS content
            sender: Sender phone number (optional)
            run_manager: Callback manager

        Returns:
            str: JSON response with status
        """
        try:
            # Import Twilio client
            from src.integrations.twilio_client import TwilioClient

            client = TwilioClient()
            result = client.send_sms(
                to=recipient,
                message=message,
                from_number=sender
            )

            logger.info(f"SMS sent to {recipient}: {result.get('status')}")

            import json
            return json.dumps({
                "success": True,
                "recipient": recipient,
                "status": result.get("status", "sent"),
                "message_id": result.get("sid") or result.get("message"),
            })

        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e),
                "recipient": recipient
            })

    async def _arun(
        self,
        recipient: str,
        message: str,
        sender: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(recipient, message, sender, run_manager)


class SendEmailInput(BaseModel):
    """Input schema for sending email."""
    recipient: str = Field(description="Email address of recipient")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content (can be HTML)")
    cc: Optional[str] = Field(default=None, description="CC email address (optional)")


class SendEmailTool(BaseTool):
    """
    Tool for sending emails via SendGrid.

    Allows agents to send formatted emails to customers with
    booking details, invoices, and other information.
    """
    name = "send_email"
    description = """
    Send an email to a customer. Use this for detailed information,
    invoices, booking confirmations, or any communication that requires
    formatted content. Input should include recipient, subject, and body.
    """
    args_schema: Type[BaseModel] = SendEmailInput

    def _run(
        self,
        recipient: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Send email message.

        Args:
            recipient: Recipient email
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: CC recipient (optional)
            run_manager: Callback manager

        Returns:
            str: JSON response with status
        """
        try:
            # Import SendGrid client (placeholder for now)
            # TODO: Implement actual SendGrid integration
            logger.info(f"Email sent to {recipient} with subject: {subject}")

            import json
            return json.dumps({
                "success": True,
                "recipient": recipient,
                "subject": subject,
                "status": "sent",
                "message": "Email queued for delivery (SendGrid not configured)"
            })

        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e),
                "recipient": recipient
            })

    async def _arun(
        self,
        recipient: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(recipient, subject, body, cc, run_manager)


class MakePhonecallInput(BaseModel):
    """Input schema for making phone calls."""
    recipient: str = Field(description="Phone number to call (E.164 format)")
    message: str = Field(description="Message to deliver via text-to-speech")
    callback_url: Optional[str] = Field(default=None, description="URL for call status callbacks")


class MakePhonecallTool(BaseTool):
    """
    Tool for making automated phone calls via Twilio.

    Allows agents to make calls to customers for important updates
    or when immediate contact is needed.
    """
    name = "make_phonecall"
    description = """
    Make an automated phone call to a customer. Use this for urgent
    communications or when SMS/email may not be sufficient.
    The message will be converted to speech.
    """
    args_schema: Type[BaseModel] = MakePhonecallInput

    def _run(
        self,
        recipient: str,
        message: str,
        callback_url: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Make phone call.

        Args:
            recipient: Recipient phone number
            message: Message for text-to-speech
            callback_url: Callback URL for status
            run_manager: Callback manager

        Returns:
            str: JSON response with status
        """
        try:
            # Import Twilio client
            from src.integrations.twilio_client import TwilioClient

            client = TwilioClient()
            result = client.make_call(
                to=recipient,
                message=message
            )

            logger.info(f"Phone call initiated to {recipient}: {result.get('status')}")

            import json
            return json.dumps({
                "success": True,
                "recipient": recipient,
                "status": result.get("status", "initiated"),
                "call_id": result.get("sid") or result.get("message"),
            })

        except Exception as e:
            logger.error(f"Failed to make call to {recipient}: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e),
                "recipient": recipient
            })

    async def _arun(
        self,
        recipient: str,
        message: str,
        callback_url: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(recipient, message, callback_url, run_manager)
