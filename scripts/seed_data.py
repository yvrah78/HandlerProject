#!/usr/bin/env python3
"""
Seed data script for Project Handler.
Populates database with sample data for development and testing.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import SessionLocal
from src.models.customer import Customer
from src.models.booking import Booking, BookingStatus
from src.models.invoice import Invoice, InvoiceStatus
from src.core.logging import get_logger

logger = get_logger(__name__)


def seed_customers(db):
    """Seed sample customers."""
    customers = [
        Customer(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="Acme Corp",
            address="123 Main St, New York, NY 10001"
        ),
        Customer(
            name="Jane Smith",
            email="jane.smith@example.com",
            phone="+1234567891",
            company="Tech Solutions Inc",
            address="456 Oak Ave, San Francisco, CA 94102"
        ),
        Customer(
            name="Bob Johnson",
            email="bob.johnson@example.com",
            phone="+1234567892",
            company="Global Logistics",
            address="789 Pine Rd, Chicago, IL 60601"
        ),
    ]

    for customer in customers:
        db.add(customer)

    db.commit()
    logger.info(f"Seeded {len(customers)} customers")
    return customers


def seed_bookings(db, customers):
    """Seed sample bookings."""
    bookings = [
        Booking(
            customer_id=customers[0].id,
            origin="123 Main St, New York, NY 10001",
            destination="789 Broadway, New York, NY 10003",
            pickup_datetime=datetime.utcnow() + timedelta(days=1),
            cargo_description="Office furniture",
            cargo_weight=500.0,
            status=BookingStatus.CONFIRMED
        ),
        Booking(
            customer_id=customers[1].id,
            origin="456 Oak Ave, San Francisco, CA 94102",
            destination="321 Market St, San Francisco, CA 94103",
            pickup_datetime=datetime.utcnow() + timedelta(days=2),
            cargo_description="Electronics",
            cargo_weight=200.0,
            status=BookingStatus.PENDING
        ),
        Booking(
            customer_id=customers[2].id,
            origin="789 Pine Rd, Chicago, IL 60601",
            destination="654 Lake Shore Dr, Chicago, IL 60611",
            pickup_datetime=datetime.utcnow() + timedelta(days=3),
            cargo_description="Construction materials",
            cargo_weight=1500.0,
            status=BookingStatus.PENDING
        ),
    ]

    for booking in bookings:
        db.add(booking)

    db.commit()
    logger.info(f"Seeded {len(bookings)} bookings")
    return bookings


def seed_invoices(db, customers, bookings):
    """Seed sample invoices."""
    invoices = [
        Invoice(
            booking_id=bookings[0].id,
            customer_id=customers[0].id,
            invoice_number="INV-2025-001",
            amount=500.0,
            tax_amount=50.0,
            total_amount=550.0,
            status=InvoiceStatus.SENT,
            due_date=datetime.utcnow() + timedelta(days=30)
        ),
        Invoice(
            booking_id=bookings[1].id,
            customer_id=customers[1].id,
            invoice_number="INV-2025-002",
            amount=300.0,
            tax_amount=30.0,
            total_amount=330.0,
            status=InvoiceStatus.DRAFT,
            due_date=datetime.utcnow() + timedelta(days=30)
        ),
    ]

    for invoice in invoices:
        db.add(invoice)

    db.commit()
    logger.info(f"Seeded {len(invoices)} invoices")
    return invoices


def main():
    """Main seed function."""
    try:
        logger.info("Starting database seeding...")

        db = SessionLocal()

        # Seed data
        customers = seed_customers(db)
        bookings = seed_bookings(db, customers)
        invoices = seed_invoices(db, customers, bookings)

        db.close()

        logger.info("Database seeding completed successfully!")
        logger.info(f"Total records created:")
        logger.info(f"  - Customers: {len(customers)}")
        logger.info(f"  - Bookings: {len(bookings)}")
        logger.info(f"  - Invoices: {len(invoices)}")

        return 0

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
