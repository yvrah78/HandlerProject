"""
CommunicationLog model for Project Handler.
Tracks all communications (SMS, calls, emails) sent to customers.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class CommunicationType(str, enum.Enum):
    """Communication type enumeration."""
    SMS = "sms"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    WHATSAPP = "whatsapp"


class CommunicationStatus(str, enum.Enum):
    """Communication status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class CommunicationLog(Base):
    """Communication log entity model."""

    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)

    # Communication details
    communication_type = Column(Enum(CommunicationType), nullable=False)
    recipient = Column(String(255), nullable=False)  # Phone number or email
    subject = Column(String(500), nullable=True)  # For emails
    message = Column(Text, nullable=False)

    # Status tracking
    status = Column(Enum(CommunicationStatus), default=CommunicationStatus.PENDING)

    # External service IDs
    twilio_sid = Column(String(255), nullable=True)  # Twilio message SID
    sendgrid_message_id = Column(String(255), nullable=True)  # SendGrid message ID

    # Delivery tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Cost tracking
    cost = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", backref="communications")
    booking = relationship("Booking", backref="communications")

    def __repr__(self):
        return f"<CommunicationLog(id={self.id}, type='{self.communication_type}', recipient='{self.recipient}', status='{self.status}')>"
