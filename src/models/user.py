"""
User model for Project Handler.
Represents system users with authentication and role-based access.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration for RBAC."""
    ADMIN = "admin"
    MANAGER = "manager"
    DISPATCHER = "dispatcher"
    DRIVER = "driver"
    CLIENT = "client"


class User(Base):
    """User entity model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile info
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)

    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.CLIENT, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
