"""
Models package for Project Handler.
Exports all database models.
"""
from src.models.customer import Customer, CustomerType
from src.models.booking import Booking, BookingStatus
from src.models.invoice import Invoice, InvoiceStatus
from src.models.user import User, UserRole
from src.models.service import Service, ServiceType
from src.models.vehicle import Vehicle, VehicleType, VehicleStatus
from src.models.driver import Driver, DriverStatus
from src.models.route import Route
from src.models.quote import Quote, QuoteStatus
from src.models.payment import Payment, PaymentMethod, PaymentStatus
from src.models.communication_log import CommunicationLog, CommunicationType, CommunicationStatus

__all__ = [
    # Customer
    "Customer",
    "CustomerType",
    # Booking
    "Booking",
    "BookingStatus",
    # Invoice
    "Invoice",
    "InvoiceStatus",
    # User
    "User",
    "UserRole",
    # Service
    "Service",
    "ServiceType",
    # Vehicle
    "Vehicle",
    "VehicleType",
    "VehicleStatus",
    # Driver
    "Driver",
    "DriverStatus",
    # Route
    "Route",
    # Quote
    "Quote",
    "QuoteStatus",
    # Payment
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    # Communication
    "CommunicationLog",
    "CommunicationType",
    "CommunicationStatus",
]
