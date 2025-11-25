# 🔌 External Integrations Guide

Complete guide for all external service integrations in Project Handler.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Twilio Integration (I1)](#twilio-integration)
3. [SendGrid Integration (I2)](#sendgrid-integration)
4. [Stripe Integration (I3)](#stripe-integration)
5. [Google Maps Integration (I4)](#google-maps-integration)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Error Handling](#error-handling)
9. [Testing](#testing)

---

## 🎯 Overview

Project Handler integrates with 4 major external services to provide comprehensive transportation management capabilities:

| Integration | Purpose | Agent | Status |
|------------|---------|-------|--------|
| **Twilio** | SMS, Phone, WhatsApp | Communications (AI2) | ✅ Complete |
| **SendGrid** | Email delivery | Communications (AI2) | ✅ Complete |
| **Stripe** | Payment processing | Financial (AI3) | ✅ Complete |
| **Google Maps** | Routing & geocoding | Operations (AI4) | ✅ Complete |

All integrations support:
- ✅ Graceful degradation (works without API keys)
- ✅ Comprehensive error handling
- ✅ Async/await patterns
- ✅ Detailed logging
- ✅ Status monitoring

---

## 📱 Twilio Integration (I1)

**File:** `src/integrations/twilio_client.py` (275 lines)
**Agent:** Communications Agent (AI2)
**Purpose:** Phone calls, SMS, and WhatsApp messaging

### Capabilities

- ✅ Send SMS messages (with MMS support)
- ✅ Make automated phone calls (TTS)
- ✅ Send WhatsApp messages
- ✅ Bulk SMS sending
- ✅ Message status tracking
- ✅ Phone number validation

### Configuration

Required environment variables:
```bash
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
```

### Usage Examples

#### Send SMS
```python
from src.integrations.twilio_client import TwilioClient

client = TwilioClient()
client.configure_phone_numbers(sms_number="+15551234567")

result = await client.send_sms(
    to="+15559876543",
    message="Your booking is confirmed!"
)

# Result:
# {
#   "sid": "SM123456789",
#   "status": "queued",
#   "to": "+15559876543",
#   "from": "+15551234567",
#   "body": "Your booking is confirmed!",
#   "date_created": "2025-11-15T10:00:00",
#   "price": "0.0075",
#   "price_unit": "USD"
# }
```

#### Make Phone Call
```python
result = await client.make_call(
    to="+15559876543",
    message="Hello! Your driver will arrive in 10 minutes.",
    voice="Polly.Joanna"
)

# Result:
# {
#   "sid": "CA123456789",
#   "status": "initiated",
#   "to": "+15559876543",
#   "duration": null,
#   "price": null
# }
```

#### Send WhatsApp
```python
client.configure_phone_numbers(
    sms_number="+15551234567",
    whatsapp_number="+15551234567"
)

result = await client.send_whatsapp(
    to="+15559876543",
    message="Your booking #12345 is confirmed!",
    media_urls=["https://example.com/map.png"]
)
```

#### Bulk SMS
```python
recipients = ["+15551111111", "+15552222222", "+15553333333"]
results = await client.send_bulk_sms(
    recipients=recipients,
    message="Important update: Service disruption tomorrow 9-11 AM"
)

# Results contains array of individual results
```

### API Reference

```python
class TwilioClient:
    async def send_sms(to: str, message: str, from_: str = None, media_urls: List[str] = None) -> dict
    async def send_whatsapp(to: str, message: str, from_: str = None, media_urls: List[str] = None) -> dict
    async def make_call(to: str, message: str, from_: str = None, voice: str = "Polly.Joanna") -> dict
    async def send_bulk_sms(recipients: List[str], message: str, from_: str = None) -> List[dict]
    async def get_message_status(message_sid: str) -> dict
    async def get_call_status(call_sid: str) -> dict
    async def validate_phone_number(phone_number: str) -> dict
    def configure_phone_numbers(sms_number: str, whatsapp_number: str = None) -> None
    def get_status() -> dict
```

---

## 📧 SendGrid Integration (I2)

**File:** `src/integrations/sendgrid_client.py` (260 lines)
**Agent:** Communications Agent (AI2)
**Purpose:** Email delivery and management

### Capabilities

- ✅ Send HTML/text emails
- ✅ Template-based emails
- ✅ Email with attachments
- ✅ CC/BCC support
- ✅ Bulk email sending
- ✅ Custom sender configuration

### Configuration

Required environment variable:
```bash
SENDGRID_API_KEY=your_sendgrid_api_key_here
```

### Usage Examples

#### Send HTML Email
```python
from src.integrations.sendgrid_client import SendGridClient

client = SendGridClient()
client.configure_sender(
    email="noreply@projecthandler.com",
    name="Project Handler"
)

result = await client.send_email(
    to="customer@example.com",
    subject="Booking Confirmation #12345",
    html_content="<h1>Your booking is confirmed!</h1><p>Details...</p>",
    text_content="Your booking is confirmed! Details..."
)

# Result:
# {
#   "status_code": 202,
#   "status": "sent",
#   "to": "customer@example.com",
#   "subject": "Booking Confirmation #12345",
#   "message_id": "abc123xyz",
#   "timestamp": "2025-11-15T10:00:00"
# }
```

#### Send Template Email
```python
result = await client.send_template_email(
    to="customer@example.com",
    template_id="d-abc123xyz",
    dynamic_data={
        "customer_name": "John Doe",
        "booking_id": "12345",
        "pickup_time": "2025-11-15 14:00",
        "total_price": "$150.00"
    }
)
```

#### Send Email with Attachments
```python
result = await client.send_email(
    to="customer@example.com",
    subject="Invoice #12345",
    html_content="<p>Please find your invoice attached.</p>",
    attachments=[
        {
            "content": base64_encoded_pdf,
            "filename": "invoice_12345.pdf",
            "type": "application/pdf",
            "disposition": "attachment"
        }
    ]
)
```

#### Bulk Email
```python
recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
results = await client.send_bulk_email(
    recipients=recipients,
    subject="Newsletter - November 2025",
    html_content="<h1>Monthly Newsletter</h1>..."
)
```

### API Reference

```python
class SendGridClient:
    async def send_email(to: str, subject: str, html_content: str = None, text_content: str = None,
                        from_email: str = None, from_name: str = None,
                        attachments: List[dict] = None, cc: List[str] = None, bcc: List[str] = None) -> dict
    async def send_template_email(to: str, template_id: str, dynamic_data: dict,
                                  from_email: str = None, from_name: str = None) -> dict
    async def send_bulk_email(recipients: List[str], subject: str, html_content: str = None,
                             text_content: str = None, from_email: str = None, from_name: str = None) -> List[dict]
    def configure_sender(email: str, name: str = "Project Handler") -> None
    def get_status() -> dict
```

---

## 💳 Stripe Integration (I3)

**File:** `src/integrations/stripe_client.py` (279 lines)
**Agent:** Financial Agent (AI3)
**Purpose:** Payment processing and invoicing

### Capabilities

- ✅ Create payment intents
- ✅ Process payments
- ✅ Create Stripe customers
- ✅ Generate invoices
- ✅ Process refunds
- ✅ Manage subscriptions
- ✅ Payment status tracking

### Configuration

Required environment variable:
```bash
STRIPE_SECRET_KEY=sk_test_or_live_your_key_here
```

### Usage Examples

#### Create Payment Intent
```python
from src.integrations.stripe_client import StripeClient

client = StripeClient()

result = await client.create_payment_intent(
    amount=150.00,  # in dollars
    currency="usd",
    customer_id="cus_123456",
    description="Booking #12345 - Airport transfer",
    metadata={"booking_id": "12345"}
)

# Result:
# {
#   "id": "pi_1234567890",
#   "client_secret": "pi_123_secret_xyz",
#   "amount": 150.00,
#   "amount_cents": 15000,
#   "currency": "USD",
#   "status": "requires_payment_method",
#   "customer": "cus_123456",
#   "created": "2025-11-15T10:00:00"
# }
```

#### Create Stripe Customer
```python
result = await client.create_customer(
    email="customer@example.com",
    name="John Doe",
    phone="+15551234567",
    metadata={"internal_customer_id": "12345"}
)

# Result:
# {
#   "id": "cus_123456",
#   "email": "customer@example.com",
#   "name": "John Doe",
#   "phone": "+15551234567",
#   "created": "2025-11-15T10:00:00"
# }
```

#### Create Invoice
```python
result = await client.create_invoice(
    customer_id="cus_123456",
    amount=200.00,
    description="Monthly service fee - November 2025",
    auto_advance=True
)

# Result includes hosted_invoice_url and invoice_pdf URLs
```

#### Process Refund
```python
result = await client.process_refund(
    payment_intent_id="pi_1234567890",
    amount=50.00,  # partial refund
    reason="requested_by_customer"
)

# Result:
# {
#   "id": "re_123456",
#   "payment_intent": "pi_1234567890",
#   "amount": 50.00,
#   "currency": "USD",
#   "status": "succeeded",
#   "reason": "requested_by_customer"
# }
```

#### Create Subscription
```python
result = await client.create_subscription(
    customer_id="cus_123456",
    price_id="price_monthly_premium",
    trial_days=14
)
```

### API Reference

```python
class StripeClient:
    async def create_payment_intent(amount: float, currency: str = "usd", customer_id: str = None,
                                   metadata: dict = None, description: str = None,
                                   payment_method_types: List[str] = None) -> dict
    async def create_customer(email: str, name: str = None, phone: str = None, metadata: dict = None) -> dict
    async def create_invoice(customer_id: str, amount: float, description: str = None, auto_advance: bool = True) -> dict
    async def process_refund(payment_intent_id: str, amount: float = None, reason: str = None) -> dict
    async def get_payment_status(payment_intent_id: str) -> dict
    async def create_subscription(customer_id: str, price_id: str, trial_days: int = None) -> dict
    async def cancel_subscription(subscription_id: str) -> dict
    def get_status() -> dict
```

---

## 🗺️ Google Maps Integration (I4)

**File:** `src/integrations/googlemaps_client.py` (335 lines)
**Agent:** Operations Agent (AI4)
**Purpose:** Routing, geocoding, and distance calculations

### Capabilities

- ✅ Geocoding (address → coordinates)
- ✅ Reverse geocoding (coordinates → address)
- ✅ Distance calculations
- ✅ Route planning with directions
- ✅ Multi-waypoint route optimization
- ✅ Address validation

### Configuration

Required environment variable:
```bash
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Usage Examples

#### Geocode Address
```python
from src.integrations.googlemaps_client import GoogleMapsClient

client = GoogleMapsClient()

result = await client.geocode("1600 Amphitheatre Parkway, Mountain View, CA")

# Result:
# {
#   "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
#   "latitude": 37.4224764,
#   "longitude": -122.0842499,
#   "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA",
#   "location_type": "ROOFTOP"
# }
```

#### Calculate Distance
```python
result = await client.calculate_distance(
    origin="San Francisco, CA",
    destination="Los Angeles, CA",
    mode="driving",
    units="metric"
)

# Result:
# {
#   "origin": "San Francisco, CA",
#   "destination": "Los Angeles, CA",
#   "distance": {
#     "value": 615386,  # meters
#     "text": "615 km"
#   },
#   "duration": {
#     "value": 21420,  # seconds
#     "text": "5 hours 57 mins"
#   },
#   "mode": "driving"
# }
```

#### Get Directions
```python
result = await client.get_directions(
    origin="New York, NY",
    destination="Boston, MA",
    mode="driving",
    alternatives=True
)

# Result includes:
# - Distance and duration
# - Turn-by-turn steps
# - Encoded polyline for map display
# - Alternative routes (if requested)
```

#### Optimize Route with Waypoints
```python
result = await client.optimize_route(
    origin="Warehouse, 123 Main St",
    destination="Final Destination",
    waypoints=[
        "Delivery 1, 456 Oak Ave",
        "Delivery 2, 789 Pine St",
        "Delivery 3, 321 Elm Dr"
    ]
)

# Result:
# {
#   "origin": "Warehouse, 123 Main St",
#   "destination": "Final Destination",
#   "optimized_order": [1, 0, 2],  # Optimized waypoint order
#   "total_distance": {"value": 25000, "text": "25 km"},
#   "total_duration": {"value": 1800, "text": "30 mins"},
#   "waypoints_count": 3
# }
```

#### Validate Address
```python
result = await client.validate_address("123 Main Street, City")

# Result:
# {
#   "valid": true,
#   "original_address": "123 Main Street, City",
#   "formatted_address": "123 Main St, City, ST 12345, USA",
#   "latitude": 40.7128,
#   "longitude": -74.0060,
#   "location_type": "ROOFTOP"
# }
```

### API Reference

```python
class GoogleMapsClient:
    async def geocode(address: str) -> dict
    async def reverse_geocode(latitude: float, longitude: float) -> dict
    async def calculate_distance(origin: str, destination: str, mode: str = "driving", units: str = "metric") -> dict
    async def get_directions(origin: str, destination: str, mode: str = "driving",
                           waypoints: List[str] = None, optimize_waypoints: bool = False,
                           alternatives: bool = False) -> dict
    async def optimize_route(origin: str, destination: str, waypoints: List[str]) -> dict
    async def validate_address(address: str) -> dict
    def get_status() -> dict
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here

# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_or_live_your_key_here

# Google Maps Configuration
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Getting API Keys

#### Twilio
1. Sign up at https://www.twilio.com/try-twilio
2. Get Account SID and Auth Token from Console Dashboard
3. Purchase a phone number for SMS/voice
4. Enable WhatsApp sandbox for testing

#### SendGrid
1. Sign up at https://sendgrid.com/pricing/
2. Create API key in Settings → API Keys
3. Verify sender email address
4. Create email templates (optional)

#### Stripe
1. Sign up at https://stripe.com/
2. Get API keys from Developers → API keys
3. Use test keys (sk_test_) for development
4. Switch to live keys (sk_live_) for production

#### Google Maps
1. Create project in Google Cloud Console
2. Enable Maps JavaScript API, Geocoding API, Directions API
3. Create API key in Credentials
4. Restrict key to your domain/IP

---

## 🔧 Agent Integration

### Communications Agent (AI2)

**File:** `src/agents/communications.py` (272 lines)

Integrated with Twilio and SendGrid:

```python
from src.agents.communications import CommunicationsAgent

agent = CommunicationsAgent()

# Send SMS
result = await agent.process({
    "communication_type": "sms",
    "recipient": "+15551234567",
    "message": "Your booking is confirmed!"
})

# Send Email
result = await agent.process({
    "communication_type": "email",
    "recipient": "customer@example.com",
    "subject": "Booking Confirmation",
    "html_content": "<h1>Confirmed!</h1>"
})

# Check agent status
status = agent.get_status()
# Shows Twilio and SendGrid integration status
```

### Financial Agent (AI3)

**File:** `src/agents/financial.py` (283 lines)

Integrated with Stripe:

```python
from src.agents.financial import FinancialAgent

agent = FinancialAgent()

# Create quotation
quote = await agent.process({
    "operation_type": "quotation",
    "service_type": "premium",
    "distance": 25,
    "duration": 45
})

# Process payment
payment = await agent.process({
    "operation_type": "payment",
    "amount": 150.00,
    "customer_id": "cus_123",
    "description": "Booking #12345"
})

# Check agent status
status = agent.get_status()
# Shows Stripe integration status and financial statistics
```

### Operations Agent (AI4)

**File:** `src/agents/operations.py` (280 lines)

Integrated with Google Maps:

```python
from src.agents.operations import OperationsAgent

agent = OperationsAgent()

# Plan route
route = await agent.process({
    "operation_type": "route_planning",
    "origin": "123 Main St, City A",
    "destination": "456 Oak Ave, City B",
    "mode": "driving"
})

# Optimize multi-stop route
optimized = await agent.process({
    "operation_type": "route_optimization",
    "origin": "Warehouse",
    "destination": "Final Stop",
    "waypoints": ["Stop 1", "Stop 2", "Stop 3"]
})

# Validate address
validation = await agent.process({
    "operation_type": "address_validation",
    "address": "123 Main Street"
})

# Check agent status
status = agent.get_status()
# Shows Google Maps integration status and operational statistics
```

---

## ⚠️ Error Handling

All integrations use consistent error handling:

```python
from src.core.exceptions import IntegrationError

try:
    result = await twilio_client.send_sms(to="+1234567890", message="Test")
except IntegrationError as e:
    print(f"Integration error: {str(e)}")
    print(f"Integration: {e.integration_name}")
    # Handle error (retry, log, notify, etc.)
```

### Common Error Scenarios

#### Integration Not Configured
```python
# Error: "Twilio integration is not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
# Solution: Add API keys to .env file
```

#### Invalid Input Format
```python
# Error: "Phone number must be in E.164 format (e.g., +1234567890)"
# Solution: Use international format with country code
```

#### API Rate Limits
```python
# Error: "Rate limit exceeded"
# Solution: Implement exponential backoff or reduce request frequency
```

#### Invalid API Key
```python
# Error: "Authentication failed"
# Solution: Verify API key is correct and has necessary permissions
```

---

## 🧪 Testing

### Unit Tests

**File:** `tests/unit/test_integrations.py`

```bash
# Run integration unit tests
pytest tests/unit/test_integrations.py -v

# Tests cover:
# - Client initialization
# - Graceful degradation
# - Input validation
# - Error handling
# - Status checking
```

### Integration Tests

**File:** `tests/integration/test_agents_integrations.py`

```bash
# Run agent integration tests
pytest tests/integration/test_agents_integrations.py -v

# Tests cover:
# - Agent-integration interaction
# - End-to-end workflows
# - Error scenarios
# - Statistics tracking
```

### Test Coverage

| Integration | Unit Tests | Integration Tests | Total |
|------------|-----------|-------------------|-------|
| Twilio | 6+ | 3+ | 9+ |
| SendGrid | 5+ | 3+ | 8+ |
| Stripe | 4+ | 3+ | 7+ |
| Google Maps | 4+ | 3+ | 7+ |
| **Total** | **19+** | **12+** | **31+** |

---

## 📊 Monitoring & Status

### Check Integration Status

```python
# Check individual integration
twilio_status = twilio_client.get_status()
# {
#   "enabled": true,
#   "configured": true,
#   "account_sid": "AC12345...",
#   "capabilities": {
#     "sms": true,
#     "voice": true,
#     "whatsapp": true
#   }
# }

# Check agent status (includes integration status)
agent_status = communications_agent.get_status()
# {
#   "agent_name": "communications",
#   "enabled": true,
#   "integrations": {
#     "twilio": {...},
#     "sendgrid": {...}
#   },
#   "statistics": {
#     "total_sent": 150,
#     "sms_sent": 80,
#     "emails_sent": 70
#   }
# }
```

---

## 🚀 Production Deployment

### Render Configuration

Add environment variables in Render dashboard:

```bash
# Settings → Environment → Add Environment Variable

TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
SENDGRID_API_KEY=SG...
STRIPE_SECRET_KEY=sk_live_...
GOOGLE_MAPS_API_KEY=AIza...
```

### Security Best Practices

1. ✅ **Never commit API keys** to version control
2. ✅ **Use environment variables** for all secrets
3. ✅ **Rotate keys regularly** (every 90 days recommended)
4. ✅ **Use test keys** in development
5. ✅ **Restrict API keys** to specific IPs/domains
6. ✅ **Monitor usage** for unexpected spikes
7. ✅ **Enable webhook signatures** for Stripe webhooks

### Cost Optimization

#### Twilio
- Use SMS for non-urgent notifications
- Batch messages when possible
- Monitor per-message costs by region

#### SendGrid
- Use free tier for up to 100 emails/day
- Implement email batching for newsletters
- Use templates to reduce bandwidth

#### Stripe
- No monthly fee for standard plan
- Pay only per successful transaction (2.9% + $0.30)
- Use test mode extensively before going live

#### Google Maps
- $200 free credit per month
- Optimize by caching geocoding results
- Use distance matrix for batch calculations

---

## 📈 Next Steps

### Immediate Enhancements

1. **Add Webhooks** for Twilio and Stripe events
2. **Implement Email Templates** in SendGrid
3. **Add Retry Logic** with exponential backoff
4. **Create Admin Dashboard** to monitor integration status

### Future Integrations

- **Slack** - Team notifications
- **AWS S3** - Document storage
- **Redis** - Caching geocoding results
- **WebSockets** - Real-time updates

---

## 🔗 Additional Resources

- [Twilio Documentation](https://www.twilio.com/docs)
- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Stripe Documentation](https://stripe.com/docs)
- [Google Maps Platform](https://developers.google.com/maps/documentation)

---

**Last Updated:** 2025-11-15
**Integration Layer Status:** ✅ Complete (I1-I4)
