"""
Customer model for Project Handler.
Represents customers in the transportation system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class CustomerType(str, enum.Enum):
    """Customer type enumeration."""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"


class Customer(Base):
    """Customer entity model."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    alternate_phone = Column(String(20), nullable=True)

    # Type
    customer_type = Column(Enum(CustomerType), default=CustomerType.INDIVIDUAL)

    # Company info (for corporate customers)
    company = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    company_address = Column(String(500), nullable=True)

    # Personal address
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA")

    # Contact person (for corporate)
    contact_person_name = Column(String(255), nullable=True)
    contact_person_phone = Column(String(20), nullable=True)
    contact_person_email = Column(String(255), nullable=True)

    # Preferences
    preferred_payment_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Status and rating
    is_active = Column(Boolean, default=True)
    rating = Column(Integer, default=5)  # 1-5 stars
    total_bookings = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bookings = relationship("Booking", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    quotes = relationship("Quote", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}', type='{self.customer_type}')>"
