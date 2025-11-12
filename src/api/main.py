"""
Main FastAPI application for Project Handler.
Multi-Agent Transportation Management System API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.database import init_db
from src.api.routes import health, auth, customers, bookings, quotes, invoices, vehicles, drivers, payments

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Project Handler API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield
    # Shutdown
    logger.info("Shutting down Project Handler API...")


# Create FastAPI application
app = FastAPI(
    title="Project Handler API",
    description="Multi-Agent Transportation Management System",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(customers.router, prefix="/api/v1", tags=["customers"])
app.include_router(bookings.router, prefix="/api/v1", tags=["bookings"])
app.include_router(quotes.router, prefix="/api/v1", tags=["quotes"])
app.include_router(invoices.router, prefix="/api/v1", tags=["invoices"])
app.include_router(vehicles.router, prefix="/api/v1", tags=["vehicles"])
app.include_router(drivers.router, prefix="/api/v1", tags=["drivers"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])


@app.get("/")
async def root():
    """
    Root endpoint providing API information.

    Returns:
        dict: API metadata
    """
    return {
        "message": "Project Handler API",
        "version": "0.1.0",
        "status": "operational",
        "environment": settings.environment,
        "documentation": "/docs"
    }


@app.get("/info")
async def info():
    """
    Get system information.

    Returns:
        dict: System information
    """
    return {
        "name": "Project Handler",
        "description": "Multi-Agent Transportation Management System",
        "version": "0.1.0",
        "features": [
            "Multi-agent orchestration",
            "Automated communications",
            "Financial operations",
            "Route optimization",
            "Analytics and reporting"
        ],
        "agents": [
            "Coordinator Agent",
            "Communications Agent",
            "Financial Agent",
            "Operations Agent",
            "Analytics Agent"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
