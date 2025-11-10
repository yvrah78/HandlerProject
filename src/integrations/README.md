# External API Integrations

This directory contains all external API integrations for the Project Handler system. Each integration is built on top of the `BaseIntegration` class and provides robust error handling, automatic retry logic, and comprehensive logging.

## Available Integrations

### 1. Twilio (SMS & Voice Calls)

**Client:** `TwilioClient`
**Documentation:** https://www.twilio.com/docs/usage/api

**Features:**
- Send SMS messages (including MMS with media)
- Make automated phone calls with text-to-speech
- Check message and call status
- Support for custom TwiML

**Rate Limits:**
- SMS: 1 request per second per account (configurable)
- Voice: Same as SMS

**Configuration:**
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**Usage Example:**
```python
from src.integrations import TwilioClient

twilio = TwilioClient()

# Send SMS
result = await twilio.send_sms(
    to="+1234567890",
    message="Your booking is confirmed!"
)

# Make call
result = await twilio.make_call(
    to="+1234567890",
    message="Your delivery is arriving in 10 minutes"
)
```

---

### 2. SendGrid (Transactional Emails)

**Client:** `SendGridClient`
**Documentation:** https://docs.sendgrid.com/api-reference

**Features:**
- Send transactional emails (HTML and plain text)
- Use dynamic templates
- Send bulk emails to multiple recipients
- Support for attachments, CC, BCC

**Rate Limits:**
- Free tier: 100 emails/day
- Paid tiers: Varies by plan

**Configuration:**
```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

**Usage Example:**
```python
from src.integrations import SendGridClient

sendgrid = SendGridClient()

# Send email
result = await sendgrid.send_email(
    to="customer@example.com",
    subject="Booking Confirmation",
    html_content="<h1>Your booking is confirmed!</h1>",
    plain_text_content="Your booking is confirmed!"
)

# Send template email
result = await sendgrid.send_template_email(
    to="customer@example.com",
    template_id="d-abc123",
    dynamic_data={"name": "John", "booking_id": "12345"}
)
```

---

### 3. Stripe (Payment Processing)

**Client:** `StripeClient`
**Documentation:** https://stripe.com/docs/api

**Features:**
- Create payment intents for one-time payments
- Manage customers
- Create and manage invoices
- Process refunds (full and partial)
- List customer payment history

**Rate Limits:**
- Default: 100 requests per second (live mode)
- Test mode: 25 requests per second

**Configuration:**
```env
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxx  # Use sk_live_ in production
```

**Usage Example:**
```python
from src.integrations import StripeClient

stripe_client = StripeClient()

# Create payment intent
result = await stripe_client.create_payment_intent(
    amount=100.50,  # $100.50
    currency="usd",
    description="Booking payment"
)

# Create customer
customer = await stripe_client.create_customer(
    email="customer@example.com",
    name="John Doe"
)

# Process refund
refund = await stripe_client.process_refund(
    payment_intent_id="pi_123",
    amount=50.00,  # Partial refund
    reason="requested_by_customer"
)
```

---

### 4. Google Maps (Geocoding & Routing)

**Client:** `GoogleMapsClient`
**Documentation:** https://developers.google.com/maps/documentation

**Features:**
- Geocode addresses to coordinates
- Reverse geocode coordinates to addresses
- Calculate distance matrices
- Get directions with step-by-step instructions
- Search for places

**Rate Limits:**
- Standard: 50 requests per second
- Daily quotas vary by API

**Configuration:**
```env
GOOGLE_MAPS_API_KEY=AIzaxxxxxxxxxxxxxxxxxx
```

**Usage Example:**
```python
from src.integrations import GoogleMapsClient

gmaps = GoogleMapsClient()

# Geocode address
result = await gmaps.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
print(result["location"])  # {"lat": 37.4224428, "lng": -122.0842467}

# Get directions
directions = await gmaps.get_directions(
    origin="New York, NY",
    destination="Boston, MA",
    mode="driving"
)

# Calculate distance
distance = await gmaps.calculate_distance_matrix(
    origins=["New York, NY"],
    destinations=["Los Angeles, CA"],
    mode="driving"
)
```

---

### 5. WhatsApp Business API

**Client:** `WhatsAppClient`
**Documentation:** https://developers.facebook.com/docs/whatsapp/cloud-api

**Features:**
- Send text messages
- Send template messages (pre-approved)
- Send media (images, documents, videos, audio)
- Mark messages as read
- Retrieve media URLs

**Rate Limits:**
- 1000 business-initiated conversations per day (tier 1)
- Higher tiers available upon request
- No limit on user-initiated conversations (replies within 24h)

**Configuration:**
```env
WHATSAPP_API_TOKEN=EAAxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_BUSINESS_ACCOUNT_ID=987654321
```

**Usage Example:**
```python
from src.integrations import WhatsAppClient

whatsapp = WhatsAppClient()

# Send text message
result = await whatsapp.send_text_message(
    to="+1234567890",
    message="Your booking is confirmed!"
)

# Send template message
result = await whatsapp.send_template_message(
    to="+1234567890",
    template_name="booking_confirmation",
    parameters=[
        {"type": "text", "text": "John"},
        {"type": "text", "text": "12345"}
    ]
)

# Send document
result = await whatsapp.send_media_message(
    to="+1234567890",
    media_type="document",
    media_url="https://example.com/invoice.pdf",
    filename="invoice.pdf"
)
```

---

## Common Features

All integration clients inherit from `BaseIntegration` and include:

### 1. Automatic Retry Logic
- Configurable retry attempts (default: 3)
- Exponential backoff between retries
- Intelligent handling of transient vs. permanent errors

### 2. Comprehensive Error Handling
- Custom `IntegrationError` exceptions with detailed context
- Proper handling of API-specific error types
- Configuration validation on initialization

### 3. Logging & Monitoring
- Structured logging for all API calls
- Success and failure tracking
- Automatic sanitization of sensitive data in logs

### 4. Input Validation & Sanitization
- Phone number formatting (E.164)
- Email address validation
- Currency amount formatting

---

## Testing

All integrations have comprehensive test suites in `tests/integration/`:

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration tests
pytest tests/integration/test_twilio.py
pytest tests/integration/test_sendgrid.py
pytest tests/integration/test_stripe.py
pytest tests/integration/test_google_maps.py
pytest tests/integration/test_whatsapp.py

# Run with coverage
pytest tests/integration/ --cov=src/integrations --cov-report=html
```

### Testing with Real APIs

To test with actual API credentials (recommended for staging environment):

1. Copy `.env.example` to `.env`
2. Fill in your test/sandbox credentials
3. Run tests with the `--real-api` flag (if implemented)

**Important:** Always use test/sandbox credentials, never production keys in tests!

---

## Error Handling

All integration methods can raise `IntegrationError`:

```python
from src.core.exceptions import IntegrationError

try:
    result = await twilio.send_sms(to="+1234567890", message="Test")
except IntegrationError as e:
    print(f"Integration failed: {e.message}")
    print(f"Integration: {e.integration_name}")
    print(f"Details: {e.details}")
```

---

## Best Practices

### 1. Use Environment Variables
Never hardcode API keys. Always use environment variables.

### 2. Handle Rate Limits
All clients implement retry logic, but you should also:
- Implement request queuing for high-volume operations
- Monitor rate limit headers
- Use batch operations when available

### 3. Monitor & Alert
- Set up logging aggregation (e.g., CloudWatch, Datadog)
- Create alerts for:
  - High error rates
  - API credential issues
  - Rate limit warnings

### 4. Security
- Use test/sandbox keys in development
- Rotate API keys regularly
- Never log sensitive data (credentials, tokens)
- Use environment-specific configurations

### 5. Testing
- Mock external APIs in unit tests
- Use sandbox/test credentials for integration tests
- Test error scenarios (network failures, invalid inputs)

---

## Troubleshooting

### Common Issues

**1. Configuration Errors**
```
ConfigurationError: Missing required configuration: TWILIO_ACCOUNT_SID
```
**Solution:** Ensure all required environment variables are set in `.env`

**2. Authentication Errors**
```
IntegrationError: Failed to initialize [integration] client
```
**Solution:** Verify your API credentials are correct and not expired

**3. Rate Limit Errors**
```
IntegrationError: Rate limit exceeded
```
**Solution:** Implement exponential backoff (already built-in) or upgrade your API plan

**4. Network Errors**
```
IntegrationError: Failed after 3 attempts: Connection timeout
```
**Solution:** Check network connectivity and firewall settings

---

## Adding New Integrations

To add a new integration:

1. Create `src/integrations/new_service_client.py`
2. Extend `BaseIntegration`
3. Implement `_validate_config()` method
4. Add integration-specific methods
5. Create tests in `tests/integration/test_new_service.py`
6. Update `src/integrations/__init__.py`
7. Update this README

Example template:

```python
from src.integrations.base import BaseIntegration
from src.core.config import get_settings
from src.core.exceptions import IntegrationError

settings = get_settings()

class NewServiceClient(BaseIntegration):
    def __init__(self):
        super().__init__("new_service")
        self.api_key = settings.new_service_api_key
        self._validate_config()

    def _validate_config(self) -> None:
        self._check_config_value(self.api_key, "NEW_SERVICE_API_KEY")

    async def do_something(self, param: str) -> dict:
        async def _do():
            # Implementation
            pass

        return await self._retry_on_failure(_do, max_retries=3)
```

---

## Support & Resources

- **Project Documentation:** See main README.md
- **Issue Tracker:** GitHub Issues
- **API Documentation Links:** See individual integration sections above
- **Contact:** [Your team contact information]

---

## License

This integration module is part of the Project Handler system and follows the same license.
