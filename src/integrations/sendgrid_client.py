"""
SendGrid integration client for Project Handler.
Handles transactional emails via SendGrid API.

Rate Limits:
- Free tier: 100 emails/day
- Paid tiers: Varies by plan
- Best practice: Use batch sending for multiple recipients

Documentation: https://docs.sendgrid.com/api-reference
"""
from typing import Optional, Dict, Any, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
from python_http_client.exceptions import HTTPError
import base64

from src.core.config import get_settings
from src.core.exceptions import IntegrationError
from src.integrations.base import BaseIntegration

settings = get_settings()


class SendGridClient(BaseIntegration):
    """
    Client for SendGrid API integration.

    Provides email sending functionality with automatic retry logic
    and comprehensive error handling.
    """

    def __init__(self):
        """Initialize SendGrid client with API key from settings."""
        super().__init__("sendgrid")

        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.sendgrid_from_email

        # Validate configuration
        self._validate_config()

        # Initialize SendGrid client
        try:
            self.client = SendGridAPIClient(self.api_key)
            self.logger.info("SendGrid client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SendGrid client: {str(e)}")
            raise IntegrationError(
                f"Failed to initialize SendGrid client: {str(e)}",
                integration_name=self.integration_name,
                details={"error": str(e)}
            )

    def _validate_config(self) -> None:
        """Validate that all required SendGrid configuration is present."""
        self._check_config_value(self.api_key, "SENDGRID_API_KEY")
        self._check_config_value(self.from_email, "SENDGRID_FROM_EMAIL")

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: Optional[str] = None,
        plain_text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send transactional email via SendGrid.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_content: HTML email content
            plain_text_content: Plain text email content (fallback)
            from_email: Sender email (defaults to configured email)
            from_name: Sender name
            reply_to: Reply-to email address
            attachments: List of attachments with 'content', 'filename', 'type'
            cc: List of CC email addresses
            bcc: List of BCC email addresses

        Returns:
            dict: Email send information including message ID

        Raises:
            IntegrationError: If email sending fails

        Example:
            >>> client = SendGridClient()
            >>> result = await client.send_email(
            ...     to="customer@example.com",
            ...     subject="Booking Confirmation",
            ...     html_content="<h1>Your booking is confirmed!</h1>"
            ... )
        """
        if not html_content and not plain_text_content:
            raise IntegrationError(
                "Either html_content or plain_text_content must be provided",
                integration_name=self.integration_name
            )

        # Sanitize email addresses
        to_email = self._sanitize_email(to)
        sender_email = from_email or self.from_email
        sender_email = self._sanitize_email(sender_email)

        self.logger.info(f"Sending email to {to_email}")

        async def _send():
            try:
                # Create Mail object
                message = Mail(
                    from_email=Email(sender_email, from_name),
                    to_emails=To(to_email),
                    subject=subject
                )

                # Add content
                if plain_text_content:
                    message.content = Content("text/plain", plain_text_content)

                if html_content:
                    message.content = Content("text/html", html_content)

                # Add reply-to if specified
                if reply_to:
                    message.reply_to = Email(self._sanitize_email(reply_to))

                # Add CC recipients
                if cc:
                    for cc_email in cc:
                        message.add_cc(Email(self._sanitize_email(cc_email)))

                # Add BCC recipients
                if bcc:
                    for bcc_email in bcc:
                        message.add_bcc(Email(self._sanitize_email(bcc_email)))

                # Add attachments if provided
                if attachments:
                    for attachment_data in attachments:
                        attachment = Attachment()
                        attachment.file_content = FileContent(attachment_data['content'])
                        attachment.file_name = FileName(attachment_data['filename'])
                        attachment.file_type = FileType(attachment_data.get('type', 'application/octet-stream'))
                        attachment.disposition = Disposition('attachment')
                        message.add_attachment(attachment)

                # Send email
                response = self.client.send(message)

                result = {
                    "status_code": response.status_code,
                    "message_id": response.headers.get('X-Message-Id', 'unknown'),
                    "to": to_email,
                    "from": sender_email,
                    "subject": subject,
                    "success": response.status_code in [200, 201, 202]
                }

                self._log_api_call("send_email", {"to": to_email, "status": response.status_code})
                return result

            except HTTPError as e:
                self._log_api_call("send_email", {"to": to_email, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"SendGrid API error: {e.reason}",
                    integration_name=self.integration_name,
                    details={
                        "status_code": e.status_code,
                        "body": e.body,
                        "reason": e.reason
                    }
                )
            except Exception as e:
                self._log_api_call("send_email", {"to": to_email, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"Failed to send email: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_send, max_retries=3)

    async def send_template_email(
        self,
        to: str,
        template_id: str,
        dynamic_data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using SendGrid dynamic template.

        Args:
            to: Recipient email address
            template_id: SendGrid template ID
            dynamic_data: Dictionary of template variables
            from_email: Sender email (defaults to configured email)
            from_name: Sender name
            subject: Email subject (if not defined in template)

        Returns:
            dict: Email send information

        Raises:
            IntegrationError: If email sending fails

        Example:
            >>> client = SendGridClient()
            >>> result = await client.send_template_email(
            ...     to="customer@example.com",
            ...     template_id="d-abc123",
            ...     dynamic_data={"name": "John", "booking_id": "12345"}
            ... )
        """
        # Sanitize email addresses
        to_email = self._sanitize_email(to)
        sender_email = from_email or self.from_email
        sender_email = self._sanitize_email(sender_email)

        self.logger.info(f"Sending template email to {to_email}")

        async def _send():
            try:
                # Create message with template
                message = Mail(
                    from_email=Email(sender_email, from_name),
                    to_emails=To(to_email)
                )

                message.template_id = template_id
                message.dynamic_template_data = dynamic_data

                if subject:
                    message.subject = subject

                # Send email
                response = self.client.send(message)

                result = {
                    "status_code": response.status_code,
                    "message_id": response.headers.get('X-Message-Id', 'unknown'),
                    "to": to_email,
                    "from": sender_email,
                    "template_id": template_id,
                    "success": response.status_code in [200, 201, 202]
                }

                self._log_api_call(
                    "send_template_email",
                    {"to": to_email, "template_id": template_id, "status": response.status_code}
                )
                return result

            except HTTPError as e:
                self._log_api_call(
                    "send_template_email",
                    {"to": to_email, "template_id": template_id, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"SendGrid API error: {e.reason}",
                    integration_name=self.integration_name,
                    details={
                        "status_code": e.status_code,
                        "body": e.body
                    }
                )

        return await self._retry_on_failure(_send, max_retries=3)

    async def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_content: Optional[str] = None,
        plain_text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send bulk emails to multiple recipients.

        Args:
            recipients: List of recipient dicts with 'email' and optional 'name'
            subject: Email subject line
            html_content: HTML email content
            plain_text_content: Plain text email content
            from_email: Sender email (defaults to configured email)
            from_name: Sender name

        Returns:
            dict: Bulk send information

        Raises:
            IntegrationError: If bulk email sending fails

        Example:
            >>> client = SendGridClient()
            >>> result = await client.send_bulk_emails(
            ...     recipients=[
            ...         {"email": "user1@example.com", "name": "User 1"},
            ...         {"email": "user2@example.com", "name": "User 2"}
            ...     ],
            ...     subject="Weekly Newsletter",
            ...     html_content="<h1>This week's updates</h1>"
            ... )
        """
        if not html_content and not plain_text_content:
            raise IntegrationError(
                "Either html_content or plain_text_content must be provided",
                integration_name=self.integration_name
            )

        sender_email = from_email or self.from_email
        sender_email = self._sanitize_email(sender_email)

        self.logger.info(f"Sending bulk email to {len(recipients)} recipients")

        async def _send():
            try:
                # Create Mail object with multiple recipients
                to_emails = []
                for recipient in recipients:
                    email = self._sanitize_email(recipient['email'])
                    name = recipient.get('name')
                    to_emails.append(To(email, name))

                message = Mail(
                    from_email=Email(sender_email, from_name),
                    to_emails=to_emails,
                    subject=subject
                )

                # Add content
                if plain_text_content:
                    message.content = Content("text/plain", plain_text_content)

                if html_content:
                    message.content = Content("text/html", html_content)

                # Send email
                response = self.client.send(message)

                result = {
                    "status_code": response.status_code,
                    "message_id": response.headers.get('X-Message-Id', 'unknown'),
                    "recipient_count": len(recipients),
                    "success": response.status_code in [200, 201, 202]
                }

                self._log_api_call(
                    "send_bulk_emails",
                    {"recipient_count": len(recipients), "status": response.status_code}
                )
                return result

            except HTTPError as e:
                self._log_api_call(
                    "send_bulk_emails",
                    {"recipient_count": len(recipients), "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"SendGrid API error: {e.reason}",
                    integration_name=self.integration_name,
                    details={
                        "status_code": e.status_code,
                        "body": e.body
                    }
                )

        return await self._retry_on_failure(_send, max_retries=3)
