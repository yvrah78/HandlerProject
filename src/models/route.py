"""
Route model for Project Handler.
Represents optimized routes for transportation bookings.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base


class Route(Base):
    """Route entity model."""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True)

    # Origin and destination
    origin_address = Column(String(500), nullable=False)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)

    destination_address = Column(String(500), nullable=False)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)

    # Waypoints (intermediate stops)
    waypoints = Column(JSON, nullable=True)  # List of addresses/coordinates

    # Route metrics
    distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)

    # Route data from Google Maps
    polyline = Column(Text, nullable=True)  # Encoded polyline from Google Maps
    route_data = Column(JSON, nullable=True)  # Full route response from Google Maps API

    # Optimization
    is_optimized = Column(Boolean, default=False)
    optimization_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="route", uselist=False)

    def __repr__(self):
        return f"<Route(id={self.id}, booking_id={self.booking_id}, distance={self.distance_km}km)>"
