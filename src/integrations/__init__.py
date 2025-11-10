"""
External API integrations for Project Handler.

This module provides clients for integrating with third-party services:
- Twilio: SMS and voice calls
- SendGrid: Transactional emails
- Stripe: Payment processing
- Google Maps: Geocoding and routing
- WhatsApp Business API: WhatsApp messaging

All clients extend BaseIntegration and include:
- Automatic retry logic with exponential backoff
- Comprehensive error handling
- Logging for monitoring and debugging
- Configuration validation

Example usage:
    >>> from src.integrations import TwilioClient, SendGridClient
    >>>
    >>> # Send SMS
    >>> twilio = TwilioClient()
    >>> result = await twilio.send_sms(to="+1234567890", message="Hello!")
    >>>
    >>> # Send email
    >>> sendgrid = SendGridClient()
    >>> result = await sendgrid.send_email(
    ...     to="customer@example.com",
    ...     subject="Booking Confirmed",
    ...     html_content="<h1>Your booking is confirmed!</h1>"
    ... )
"""

from src.integrations.base import BaseIntegration
from src.integrations.twilio_client import TwilioClient
from src.integrations.sendgrid_client import SendGridClient
from src.integrations.stripe_client import StripeClient
from src.integrations.google_maps_client import GoogleMapsClient
from src.integrations.whatsapp_client import WhatsAppClient

__all__ = [
    "BaseIntegration",
    "TwilioClient",
    "SendGridClient",
    "StripeClient",
    "GoogleMapsClient",
    "WhatsAppClient",
]
