"""
SQLAlchemy ORM models mapping domain entities to database tables.

These models implement the ORM mapping and are used by repositories
to persist and retrieve domain objects.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from infrastructure.database import Base
from domain.enums import AccessLevel, RequestStatus, UserRole, SystemType, NotificationStatus


# ============================================================
# UserORM
# ============================================================

class UserORM(Base):
    """ORM model for User entity."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    managed_access_requests = relationship(
        "AccessRequestORM",
        foreign_keys="AccessRequestORM.manager_id",
        back_populates="manager",
        cascade="all, delete-orphan",
    )
    created_access_requests = relationship(
        "AccessRequestORM",
        foreign_keys="AccessRequestORM.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship(
        "AuditLogORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "NotificationORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from domain.entities import User

        return User(
            id=self.id,
            name=self.name,
            email=self.email,
            hashed_password=self.hashed_password,
            role=self.role,
            manager_id=self.manager_id,
            is_active=self.is_active,
            created_at=self.created_at,
        )

    @staticmethod
    def from_domain(user) -> "UserORM":
        """Create ORM model from domain entity."""
        return UserORM(
            id=user.id,
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role,
            manager_id=user.manager_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )


# ============================================================
# AccessRequestORM
# ============================================================

class AccessRequestORM(Base):
    """ORM model for AccessRequest entity."""

    __tablename__ = "access_requests"

    id = Column(String(36), primary_key=True, index=True)
    requester_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    requester_name = Column(String(255), nullable=False)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    target_system = Column(String(255), nullable=False, index=True)
    access_level = Column(Enum(AccessLevel), nullable=False)
    system_type = Column(Enum(SystemType), nullable=False, default=SystemType.OTHER)
    justification = Column(Text, nullable=False)
    expiration_date = Column(Date, nullable=True)
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.DRAFT, index=True)
    rejection_reason = Column(Text, nullable=True)
    changes_requested_by = Column(String(36), nullable=True)
    changes_requested_comment = Column(Text, nullable=True)
    provisioned_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    requester = relationship(
        "UserORM",
        foreign_keys=[requester_id],
        back_populates="created_access_requests",
    )
    manager = relationship(
        "UserORM",
        foreign_keys=[manager_id],
        back_populates="managed_access_requests",
    )
    audit_logs = relationship(
        "AuditLogORM",
        back_populates="access_request",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "NotificationORM",
        back_populates="access_request",
        cascade="all, delete-orphan",
    )

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from domain.entities import AccessRequest

        return AccessRequest(
            id=self.id,
            requester_id=self.requester_id,
            requester_name=self.requester_name,
            manager_id=self.manager_id,
            target_system=self.target_system,
            access_level=self.access_level,
            system_type=self.system_type,
            justification=self.justification,
            expiration_date=self.expiration_date,
            _status=self.status,
            rejection_reason=self.rejection_reason,
            changes_requested_by=self.changes_requested_by,
            changes_requested_comment=self.changes_requested_comment,
            provisioned_by=self.provisioned_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(request) -> "AccessRequestORM":
        """Create ORM model from domain entity."""
        return AccessRequestORM(
            id=request.id,
            requester_id=request.requester_id,
            requester_name=request.requester_name,
            manager_id=request.manager_id,
            target_system=request.target_system,
            access_level=request.access_level,
            system_type=request.system_type,
            justification=request.justification,
            expiration_date=request.expiration_date,
            status=request._status,
            rejection_reason=request.rejection_reason,
            changes_requested_by=request.changes_requested_by,
            changes_requested_comment=request.changes_requested_comment,
            provisioned_by=request.provisioned_by,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )


# ============================================================
# AuditLogORM
# ============================================================

class AuditLogORM(Base):
    """ORM model for audit logging."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    request_id = Column(String(36), ForeignKey("access_requests.id"), nullable=True, index=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("UserORM", back_populates="audit_logs")
    access_request = relationship("AccessRequestORM", back_populates="audit_logs")


# ============================================================
# NotificationORM
# ============================================================

class NotificationORM(Base):
    """ORM model for notifications."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    request_id = Column(String(36), ForeignKey("access_requests.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserORM", back_populates="notifications")
    access_request = relationship("AccessRequestORM", back_populates="notifications")
