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

This project is developed in **15 modular phases** organized in 4 layers.

**📊 Current Progress: 60% (9/15 modules completed)**

For detailed roadmap, see **[PROJECT-STATUS.md](./PROJECT-STATUS.md)**

### Foundation Layer (F)
- **F1:** Core System Setup ✅
- **F2:** Data Architecture & Models ✅
- **F3:** Authentication & Security ✅
- **F4:** API Development 🔄 (80%)

### Integration Layer (I)
- **I1:** Twilio Integration (Phone/SMS) ✅
- **I2:** SendGrid Integration (Email) ✅
- **I3:** Stripe Integration (Payments) ✅
- **I4:** Google Maps Integration (Routing) ✅
- **I5:** WhatsApp Integration (Messaging) ✅

### Intelligence Layer (AI)
- **AI0:** Base Agent Structure ✅ (20% - basic structure only)
- **AI1:** Agent Framework Setup ⏳
- **AI2:** LangChain Implementation ⏳
- **AI3:** Claude Integration ⏳
- **AI4:** Agent Orchestration ⏳

### Application Layer (A)
- **A1:** Frontend Dashboard ⏳
- **A2:** Analytics & Reporting ⏳
- **A3:** Advanced Features ⏳

**Legend:** ✅ Complete | 🔄 In Progress | ⏳ Pending

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

**Current Version:** 0.1.0 (Foundation Setup)

**Status:** Active Development

This is the initial foundation setup. Additional features will be added in upcoming modules following the development roadmap.

---

**Built with ❤️ using Claude AI**
