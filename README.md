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

**Integrations:**
- Twilio (phone/SMS)
- SendGrid (email)
- Stripe (payments)
- Google Maps API (routing)

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

### API Keys
- `ANTHROPIC_API_KEY` - Claude API key
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `SENDGRID_API_KEY` - SendGrid API key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `GOOGLE_MAPS_API_KEY` - Google Maps API key

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
│   ├── agents/            # Multi-agent system
│   ├── api/               # FastAPI application
│   ├── core/              # Core functionality
│   ├── integrations/      # External integrations
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── utils/             # Utilities
├── tests/                 # Test suites
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── frontend/              # Frontend (future)
```

## Development Roadmap

This project is developed in **15 modular phases** organized in 4 layers:

### Foundation Layer (F)
- **F1:** Core System Setup ✅ Complete
- **F2:** Data Architecture & Models ✅ Complete
- **F3:** Authentication & Security ✅ Complete
- **F4:** API Development ✅ Complete

### Integration Layer (I)
- **I1:** Twilio Integration (Phone/SMS)
- **I2:** SendGrid Integration (Email)
- **I3:** Stripe Integration (Payments)
- **I4:** Google Maps Integration (Routing)

### Intelligence Layer (AI)
- **AI1:** Agent Framework Setup ✅ Complete
- **AI2:** LangChain Implementation ✅ Complete (Analytics Agent)
- **AI3:** Claude Integration ✅ Complete (Analytics Agent)
- **AI4:** Agent Orchestration ⏳ In Progress

### Application Layer (A)
- **A1:** Frontend Dashboard ✅ Complete (Basic)
- **A2:** Analytics & Reporting ✅ Complete (Backend API)
- **A3:** Advanced Features ⏳ Planned

## API Endpoints

### Health & Status
- `GET /` - API information
- `GET /info` - System information
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh

### Bookings Management
- `GET /api/v1/bookings` - List bookings (with pagination)
- `POST /api/v1/bookings` - Create new booking
- `GET /api/v1/bookings/{id}` - Get booking details
- `PUT /api/v1/bookings/{id}` - Update booking
- `DELETE /api/v1/bookings/{id}` - Cancel booking

### Customer Management
- `GET /api/v1/customers` - List customers (with pagination)
- `POST /api/v1/customers` - Create new customer
- `GET /api/v1/customers/{id}` - Get customer details
- `PUT /api/v1/customers/{id}` - Update customer
- `DELETE /api/v1/customers/{id}` - Delete customer

### Analytics & Reports (NEW - AI-Powered)
- `GET /api/v1/analytics/status` - Agent status
- `GET /api/v1/analytics/metrics` - Real-time metrics
- `GET /api/v1/analytics/kpis` - Key performance indicators
- `POST /api/v1/analytics/reports` - Generate custom report
- `POST /api/v1/analytics/insights` - Get AI strategic insights
- `GET /api/v1/analytics/performance` - Performance report
- `GET /api/v1/analytics/financial` - Financial report
- `GET /api/v1/analytics/operations` - Operations report
- `GET /api/v1/analytics/customer` - Customer analytics
- `GET /api/v1/analytics/predictive` - Predictive analytics

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

- [Project Status](PROJECT_STATUS.md) - Current development status
- [Architecture Overview](docs/architecture.md) - System architecture
- [Analytics Agent Guide](docs/ANALYTICS_AGENT.md) - Complete Analytics Agent documentation
- [Deployment Guide](DEPLOYMENT.md) - How to deploy the system
- [Development Roadmap](ROADMAP.md) - Detailed development plan
- [Next Steps](NEXT-STEPS.md) - Upcoming development tasks
- [API Reference](https://project-handler-api.onrender.com/docs) - Interactive API documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the development team

## Status

**Current Version:** 0.3.0 (Analytics Agent Complete)

**Status:** Active Development

**Recent Updates:**
- ✅ Foundation layer complete (F1-F4)
- ✅ Analytics Agent with full AI integration (LangChain + Claude)
- ✅ 11 Analytics API endpoints
- ✅ Real-time metrics and KPI calculation
- ✅ 5 specialized AI-powered report types
- ✅ Comprehensive testing (115+ tests)

**What's Working:**
- Multi-agent system architecture
- Complete CRUD API for customers and bookings
- JWT authentication and security
- AI-powered analytics and business intelligence
- Real-time metrics collection
- Automated KPI calculation
- Intelligent report generation

---

**Built with ❤️ using Claude AI**
