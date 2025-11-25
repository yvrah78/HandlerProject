"""
SendGrid integration client for Project Handler.
Handles email delivery via SendGrid API.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
from python_http_client.exceptions import HTTPError

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.exceptions import IntegrationError

logger = get_logger(__name__)
settings = get_settings()


class SendGridClient:
    """Client for SendGrid email API integration."""

    def __init__(self):
        """Initialize SendGrid client with API key."""
        self.api_key = settings.sendgrid_api_key
        self.logger = logger
        self.enabled = False
        self.client = None
        self.from_email = None
        self.from_name = "Project Handler"

        # Initialize SendGrid client if API key is available
        if self.api_key:
            try:
                self.client = SendGridAPIClient(self.api_key)
                self.enabled = True
                self.logger.info("SendGrid client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize SendGrid client: {str(e)}")
                self.enabled = False
        else:
            self.logger.info("SendGrid API key not provided - running in disabled mode")

    def _check_enabled(self):
        """Check if SendGrid is enabled and raise error if not."""
        if not self.enabled:
            raise IntegrationError(
                "SendGrid integration is not configured. Please set SENDGRID_API_KEY.",
                integration_name="sendgrid"
            )

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid.

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (fallback)
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            attachments: Optional list of attachments
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients

        Returns:
            dict: Email delivery information with status

        Raises:
            IntegrationError: If email sending fails
        """
        self._check_enabled()
        self.logger.info(f"Sending email to {to}")

        if not html_content and not text_content:
            raise IntegrationError(
                "Either html_content or text_content must be provided",
                integration_name="sendgrid"
            )

        try:
            # Create email message
            message = Mail(
                from_email=Email(from_email or self.from_email, from_name or self.from_name),
                to_emails=To(to),
                subject=subject
            )

            # Add content
            if html_content:
                message.add_content(Content("text/html", html_content))
            if text_content:
                message.add_content(Content("text/plain", text_content))

            # Add CC recipients
            if cc:
                for cc_email in cc:
                    message.add_cc(cc_email)

            # Add BCC recipients
            if bcc:
                for bcc_email in bcc:
                    message.add_bcc(bcc_email)

            # Add attachments
            if attachments:
                for attachment in attachments:
                    att = Attachment()
                    att.file_content = FileContent(attachment.get('content'))
                    att.file_name = FileName(attachment.get('filename'))
                    att.file_type = FileType(attachment.get('type', 'application/octet-stream'))
                    att.disposition = Disposition(attachment.get('disposition', 'attachment'))
                    message.add_attachment(att)

            # Send email in thread pool (SendGrid SDK is synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.send(message)
            )

            return {
                "status_code": response.status_code,
                "status": "sent" if response.status_code == 202 else "failed",
                "to": to,
                "subject": subject,
                "message_id": response.headers.get('X-Message-Id'),
                "timestamp": datetime.utcnow().isoformat()
            }

        except HTTPError as e:
            self.logger.error(f"SendGrid API error: {e.body}")
            raise IntegrationError(
                f"Failed to send email: {e.body}",
                integration_name="sendgrid"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {str(e)}")
            raise IntegrationError(
                f"Failed to send email: {str(e)}",
                integration_name="sendgrid"
            )

    async def send_template_email(
        self,
        to: str,
        template_id: str,
        dynamic_data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using SendGrid template.

        Args:
            to: Recipient email address
            template_id: SendGrid template ID
            dynamic_data: Dynamic data for template variables
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)

        Returns:
            dict: Email delivery information

        Raises:
            IntegrationError: If template email sending fails
        """
        self._check_enabled()
        self.logger.info(f"Sending template email {template_id} to {to}")

        try:
            message = Mail(
                from_email=Email(from_email or self.from_email, from_name or self.from_name),
                to_emails=To(to)
            )
            message.template_id = template_id
            message.dynamic_template_data = dynamic_data

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.send(message)
            )

            return {
                "status_code": response.status_code,
                "status": "sent" if response.status_code == 202 else "failed",
                "to": to,
                "template_id": template_id,
                "message_id": response.headers.get('X-Message-Id'),
                "timestamp": datetime.utcnow().isoformat()
            }

        except HTTPError as e:
            self.logger.error(f"SendGrid template error: {e.body}")
            raise IntegrationError(
                f"Failed to send template email: {e.body}",
                integration_name="sendgrid"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error sending template email: {str(e)}")
            raise IntegrationError(
                f"Failed to send template email: {str(e)}",
                integration_name="sendgrid"
            )

    async def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Send email to multiple recipients.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            from_email: Sender email
            from_name: Sender name

        Returns:
            list: List of delivery results for each recipient

        Raises:
            IntegrationError: If bulk sending fails
        """
        self._check_enabled()
        self.logger.info(f"Sending bulk email to {len(recipients)} recipients")

        results = []
        for recipient in recipients:
            try:
                result = await self.send_email(
                    to=recipient,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    from_email=from_email,
                    from_name=from_name
                )
                results.append(result)
            except IntegrationError as e:
                self.logger.error(f"Failed to send email to {recipient}: {str(e)}")
                results.append({
                    "to": recipient,
                    "status": "failed",
                    "error": str(e)
                })

        return results

    def configure_sender(self, email: str, name: str = "Project Handler"):
        """
        Configure default sender email and name.

        Args:
            email: Default sender email address
            name: Default sender name
        """
        self.from_email = email
        self.from_name = name
        self.logger.info(f"Configured SendGrid sender: {name} <{email}>")

    def get_status(self) -> Dict[str, Any]:
        """
        Get SendGrid client status.

        Returns:
            dict: Client configuration and status
        """
        return {
            "enabled": self.enabled,
            "configured": bool(self.api_key),
            "from_email": self.from_email,
            "from_name": self.from_name,
            "capabilities": {
                "email": self.enabled,
                "templates": self.enabled,
                "bulk_email": self.enabled,
                "attachments": self.enabled
            }
        }
