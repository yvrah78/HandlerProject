"""
WhatsApp Business API integration client for Project Handler.
Handles WhatsApp messaging via WhatsApp Cloud API.

Rate Limits:
- 1000 business-initiated conversations per day (tier 1)
- Higher tiers available upon request
- No limit on user-initiated conversations (replies within 24h)

Documentation: https://developers.facebook.com/docs/whatsapp/cloud-api
"""
from typing import Optional, Dict, Any, List
import httpx
import asyncio

from src.core.config import get_settings
from src.core.exceptions import IntegrationError
from src.integrations.base import BaseIntegration

settings = get_settings()


class WhatsAppClient(BaseIntegration):
    """
    Client for WhatsApp Business Cloud API integration.

    Provides functionality for:
    - Sending text messages
    - Sending template messages
    - Sending media (images, documents, etc.)
    - Managing message templates
    """

    def __init__(self):
        """Initialize WhatsApp client with credentials from settings."""
        super().__init__("whatsapp")

        self.api_token = settings.whatsapp_api_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.business_account_id = settings.whatsapp_business_account_id

        # Validate configuration
        self._validate_config()

        # WhatsApp API base URL
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        self.logger.info("WhatsApp client initialized successfully")

    def _validate_config(self) -> None:
        """Validate that all required WhatsApp configuration is present."""
        self._check_config_value(self.api_token, "WHATSAPP_API_TOKEN")
        self._check_config_value(self.phone_number_id, "WHATSAPP_PHONE_NUMBER_ID")

    async def send_text_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.

        Args:
            to: Recipient phone number (E.164 format)
            message: Message text content
            preview_url: Enable URL preview in message

        Returns:
            dict: Message send information including message ID

        Raises:
            IntegrationError: If message sending fails

        Example:
            >>> client = WhatsAppClient()
            >>> result = await client.send_text_message(
            ...     to="+1234567890",
            ...     message="Your booking is confirmed!"
            ... )
        """
        # Sanitize phone number
        to_number = self._sanitize_phone_number(to)

        self.logger.info(f"Sending WhatsApp message to {to_number}")

        async def _send():
            try:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to_number,
                    "type": "text",
                    "text": {
                        "preview_url": preview_url,
                        "body": message
                    }
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )

                    response.raise_for_status()
                    data = response.json()

                result = {
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "to": to_number,
                    "status": "sent",
                    "wa_id": data.get("contacts", [{}])[0].get("wa_id")
                }

                self._log_api_call("send_text_message", {"to": to_number})
                return result

            except httpx.HTTPStatusError as e:
                self._log_api_call(
                    "send_text_message",
                    {"to": to_number, "error": str(e), "status": e.response.status_code},
                    success=False
                )
                error_data = e.response.json() if e.response.content else {}
                raise IntegrationError(
                    f"WhatsApp API error: {error_data.get('error', {}).get('message', str(e))}",
                    integration_name=self.integration_name,
                    details={
                        "status_code": e.response.status_code,
                        "error_data": error_data
                    }
                )
            except Exception as e:
                self._log_api_call(
                    "send_text_message",
                    {"to": to_number, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Failed to send WhatsApp message: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_send, max_retries=3)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp.

        Templates must be pre-approved by WhatsApp.

        Args:
            to: Recipient phone number (E.164 format)
            template_name: Name of approved template
            language_code: Template language code (e.g., "en_US", "es_MX")
            parameters: Template parameter values

        Returns:
            dict: Message send information

        Raises:
            IntegrationError: If message sending fails

        Example:
            >>> client = WhatsAppClient()
            >>> result = await client.send_template_message(
            ...     to="+1234567890",
            ...     template_name="booking_confirmation",
            ...     parameters=[
            ...         {"type": "text", "text": "John"},
            ...         {"type": "text", "text": "12345"}
            ...     ]
            ... )
        """
        # Sanitize phone number
        to_number = self._sanitize_phone_number(to)

        self.logger.info(f"Sending WhatsApp template message to {to_number}")

        async def _send():
            try:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to_number,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {
                            "code": language_code
                        }
                    }
                }

                # Add parameters if provided
                if parameters:
                    payload["template"]["components"] = [
                        {
                            "type": "body",
                            "parameters": parameters
                        }
                    ]

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )

                    response.raise_for_status()
                    data = response.json()

                result = {
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "to": to_number,
                    "template": template_name,
                    "status": "sent"
                }

                self._log_api_call(
                    "send_template_message",
                    {"to": to_number, "template": template_name}
                )
                return result

            except httpx.HTTPStatusError as e:
                self._log_api_call(
                    "send_template_message",
                    {"to": to_number, "template": template_name, "error": str(e)},
                    success=False
                )
                error_data = e.response.json() if e.response.content else {}
                raise IntegrationError(
                    f"WhatsApp API error: {error_data.get('error', {}).get('message', str(e))}",
                    integration_name=self.integration_name,
                    details={
                        "status_code": e.response.status_code,
                        "error_data": error_data
                    }
                )

        return await self._retry_on_failure(_send, max_retries=3)

    async def send_media_message(
        self,
        to: str,
        media_type: str,
        media_url: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a media message via WhatsApp.

        Args:
            to: Recipient phone number (E.164 format)
            media_type: Type of media ("image", "document", "video", "audio")
            media_url: URL of media file (either url or id required)
            media_id: WhatsApp media ID (either url or id required)
            caption: Optional caption for image/video
            filename: Optional filename for documents

        Returns:
            dict: Message send information

        Raises:
            IntegrationError: If message sending fails

        Example:
            >>> client = WhatsAppClient()
            >>> result = await client.send_media_message(
            ...     to="+1234567890",
            ...     media_type="document",
            ...     media_url="https://example.com/invoice.pdf",
            ...     filename="invoice.pdf"
            ... )
        """
        if not media_url and not media_id:
            raise IntegrationError(
                "Either media_url or media_id must be provided",
                integration_name=self.integration_name
            )

        # Sanitize phone number
        to_number = self._sanitize_phone_number(to)

        self.logger.info(f"Sending WhatsApp {media_type} message to {to_number}")

        async def _send():
            try:
                # Build media object
                media_obj = {}
                if media_id:
                    media_obj["id"] = media_id
                else:
                    media_obj["link"] = media_url

                if caption and media_type in ["image", "video"]:
                    media_obj["caption"] = caption

                if filename and media_type == "document":
                    media_obj["filename"] = filename

                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to_number,
                    "type": media_type,
                    media_type: media_obj
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )

                    response.raise_for_status()
                    data = response.json()

                result = {
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "to": to_number,
                    "media_type": media_type,
                    "status": "sent"
                }

                self._log_api_call(
                    "send_media_message",
                    {"to": to_number, "media_type": media_type}
                )
                return result

            except httpx.HTTPStatusError as e:
                self._log_api_call(
                    "send_media_message",
                    {"to": to_number, "media_type": media_type, "error": str(e)},
                    success=False
                )
                error_data = e.response.json() if e.response.content else {}
                raise IntegrationError(
                    f"WhatsApp API error: {error_data.get('error', {}).get('message', str(e))}",
                    integration_name=self.integration_name,
                    details={
                        "status_code": e.response.status_code,
                        "error_data": error_data
                    }
                )

        return await self._retry_on_failure(_send, max_retries=3)

    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read.

        Args:
            message_id: WhatsApp message ID

        Returns:
            dict: Operation result

        Raises:
            IntegrationError: If operation fails
        """
        self.logger.info(f"Marking WhatsApp message {message_id} as read")

        async def _mark_read():
            try:
                payload = {
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers=self.headers,
                        json=payload,
                        timeout=30.0
                    )

                    response.raise_for_status()
                    data = response.json()

                result = {
                    "success": data.get("success", False),
                    "message_id": message_id
                }

                self._log_api_call("mark_message_as_read", {"message_id": message_id})
                return result

            except httpx.HTTPStatusError as e:
                error_data = e.response.json() if e.response.content else {}
                raise IntegrationError(
                    f"WhatsApp API error: {error_data.get('error', {}).get('message', str(e))}",
                    integration_name=self.integration_name,
                    details={"status_code": e.response.status_code}
                )

        return await self._retry_on_failure(_mark_read, max_retries=2)

    async def get_media_url(self, media_id: str) -> str:
        """
        Get downloadable URL for a media file.

        Args:
            media_id: WhatsApp media ID

        Returns:
            str: Downloadable media URL

        Raises:
            IntegrationError: If retrieval fails
        """
        self.logger.info(f"Getting media URL for {media_id}")

        async def _get_url():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://graph.facebook.com/v18.0/{media_id}",
                        headers=self.headers,
                        timeout=30.0
                    )

                    response.raise_for_status()
                    data = response.json()

                return data.get("url")

            except httpx.HTTPStatusError as e:
                error_data = e.response.json() if e.response.content else {}
                raise IntegrationError(
                    f"WhatsApp API error: {error_data.get('error', {}).get('message', str(e))}",
                    integration_name=self.integration_name,
                    details={"media_id": media_id}
                )

        return await self._retry_on_failure(_get_url, max_retries=2)
