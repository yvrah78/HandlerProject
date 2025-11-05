#!/usr/bin/env python3
"""
Database initialization script for Project Handler.
Creates all database tables and performs initial setup.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import init_db, engine
from src.core.logging import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


def main():
    """Initialize database tables."""
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Database URL: {settings.database_url}")

        # Initialize database
        init_db()

        logger.info("Database initialization completed successfully!")
        logger.info("All tables have been created.")

        return 0

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
