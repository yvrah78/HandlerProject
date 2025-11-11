# PROJECT HANDLER

**Multi-Agent Transportation Management System**

Project Handler is an advanced AI-powered automation system designed for transportation operations. It leverages multi-agent architecture to handle complex logistics workflows including customer communications, financial operations, route optimization, and analytics.

## Overview

This system uses specialized AI agents powered by Claude (Anthropic) to automate and optimize transportation business operations. Each agent handles specific domains while a coordinator orchestrates their interactions.

## Architecture

### Multi-Agent System

The system is built around five specialized agents:

1. **Coordinator Agent** - Central orchestration and task delegation
2. **Communications Agent** - Automated phone calls, SMS, and emails (Twilio/SendGrid)
3. **Financial Agent** - Quotations, invoicing, and payments (Stripe)
4. **Operations Agent** - Route planning, fleet management (Google Maps)
5. **Analytics Agent** - Metrics, reporting, and business intelligence

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (REST API framework)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- Redis (caching)

**AI & Agents:**
- LangChain (agent framework)
- Claude API (Anthropic)

**Integrations:** ✅ ALL IMPLEMENTED
- Twilio (phone/SMS) - Complete with retry logic
- SendGrid (email) - Complete with templates
- Stripe (payments) - Complete with refunds
- Google Maps API (routing/geocoding) - Complete
- WhatsApp Business API - Complete

**Infrastructure:**
- Docker & Docker Compose
- Alembic (database migrations)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for future frontend)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yvrah78/project-handler.git
cd project-handler
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Start services with Docker:**
```bash
docker-compose up -d
```

6. **Run database migrations:**
```bash
python scripts/init_db.py
```

7. **Start the API server:**
```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Environment Variables

Required environment variables (see `.env.example`):

### API Keys (All integrations ready)
- `ANTHROPIC_API_KEY` - Claude API key for AI agents
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_PHONE_NUMBER` - Twilio phone number for SMS/calls
- `SENDGRID_API_KEY` - SendGrid API key
- `SENDGRID_FROM_EMAIL` - Verified sender email
- `STRIPE_SECRET_KEY` - Stripe secret key (use sk_test_ for dev)
- `GOOGLE_MAPS_API_KEY` - Google Maps API key
- `WHATSAPP_API_TOKEN` - WhatsApp Business API token
- `WHATSAPP_PHONE_NUMBER_ID` - WhatsApp phone number ID
- `WHATSAPP_BUSINESS_ACCOUNT_ID` - WhatsApp business account ID

### Database
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### Application
- `ENVIRONMENT` - Environment (development/staging/production)
- `DEBUG` - Debug mode (true/false)
- `API_PORT` - API server port (default: 8000)

## Project Structure

```
project-handler/
├── src/                    # Source code
│   ├── agents/            # Multi-agent system (AI-powered)
│   ├── api/               # FastAPI application with REST endpoints
│   ├── core/              # Core functionality (config, database, logging)
│   ├── integrations/      # External API integrations ✅ COMPLETE
│   │   ├── base.py        # Base integration class with retry logic
│   │   ├── twilio_client.py        # SMS & Voice calls
│   │   ├── sendgrid_client.py      # Transactional emails
│   │   ├── stripe_client.py        # Payment processing
│   │   ├── google_maps_client.py   # Geocoding & routing
│   │   ├── whatsapp_client.py      # WhatsApp messaging
│   │   └── README.md      # Complete integration documentation
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic schemas for validation
│   ├── services/          # Business logic layer
│   └── utils/             # Utility functions
├── tests/                 # Test suites
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests (5 complete test suites)
├── docs/                  # Documentation
├── scripts/               # Utility scripts (init_db, seed_data)
└── frontend/              # Basic frontend (React app planned)
```

## Development Roadmap

This project is developed in **15 modular phases** organized in 4 layers:

### Foundation Layer (F)
- **F1:** Core System Setup ✅ (Current)
- **F2:** Data Architecture & Models
- **F3:** Authentication & Security
- **F4:** API Development

### Integration Layer (I) ✅ COMPLETED
- **I1:** Twilio Integration (Phone/SMS) ✅
- **I2:** SendGrid Integration (Email) ✅
- **I3:** Stripe Integration (Payments) ✅
- **I4:** Google Maps Integration (Routing) ✅
- **I5:** WhatsApp Business API ✅ (Bonus)

### Intelligence Layer (AI)
- **AI1:** Agent Framework Setup
- **AI2:** LangChain Implementation
- **AI3:** Claude Integration
- **AI4:** Agent Orchestration

### Application Layer (A)
- **A1:** Frontend Dashboard
- **A2:** Analytics & Reporting
- **A3:** Advanced Features

## API Endpoints

### Health & Status
- `GET /` - API information
- `GET /info` - System information
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Future Endpoints
- Bookings management
- Customer management
- Invoice operations
- Agent interactions
- Analytics & reports

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=src

# Specific test file
pytest tests/unit/test_agents.py

# Integration tests only
pytest tests/integration/
```

## Docker Usage

### Start all services:
```bash
docker-compose up -d
```

### View logs:
```bash
docker-compose logs -f
```

### Stop services:
```bash
docker-compose down
```

### Rebuild containers:
```bash
docker-compose up -d --build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Code Quality

The project follows these standards:
- PEP 8 for Python code style
- Type hints for all functions
- Docstrings for all classes and methods
- Comprehensive test coverage
- Clean, modular architecture

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Module Documentation](docs/modules/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the development team

## Status

**Current Version:** 0.3.0 (Integrations Complete)

**Status:** Active Development - Phase 2

**Completed Modules:**
- ✅ F1: Core System Setup (Foundation)
- ✅ F2: Data Architecture & Models
- ✅ F3: Authentication & Security (JWT)
- ✅ F4: API Development (CRUD endpoints)
- ✅ I1-I5: All External Integrations (Twilio, SendGrid, Stripe, Google Maps, WhatsApp)

**Next Phase:**
- 🔄 Connecting integrations with AI agents
- 🔄 Instant quote calculator system
- 🔄 Complete booking workflow automation

**Note:** Mobile apps (driver/customer) and web portals are planned for future phases after core business system is complete.

See [ROADMAP.md](ROADMAP.md) for detailed development plan.

---

**Built with ❤️ using Claude AI**
