"""
PostgreSQL repository implementations for domain interfaces.

These repositories encapsulate all ORM queries and provide
domain-friendly interfaces to the infrastructure layer.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from domain.entities import User, AccessRequest
from domain.enums import RequestStatus
from domain.interfaces.repositories import (
    UserRepository,
    AccessRequestRepository,
    AuditLogRepository,
    NotificationRepository,
)
from infrastructure.models import UserORM, AccessRequestORM, AuditLogORM, NotificationORM


# ============================================================
# PostgreSQL User Repository
# ============================================================

class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> None:
        """Add a new user to the database."""
        user_orm = UserORM.from_domain(user)
        self.session.add(user_orm)
        self.session.commit()

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID from database."""
        user_orm = self.session.query(UserORM).filter(UserORM.id == user_id).first()
        if user_orm is None:
            return None
        return user_orm.to_domain()

    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email from database."""
        user_orm = self.session.query(UserORM).filter(UserORM.email == email).first()
        if user_orm is None:
            return None
        return user_orm.to_domain()

    def get_all(self) -> List[User]:
        """Retrieve all users from database."""
        users_orm = self.session.query(UserORM).all()
        return [user_orm.to_domain() for user_orm in users_orm]

    def update(self, user: User) -> None:
        """Update an existing user in the database."""
        user_orm = self.session.query(UserORM).filter(UserORM.id == user.id).first()
        if user_orm is None:
            raise ValueError(f"User with id {user.id} not found")
        
        user_orm.name = user.name
        user_orm.email = user.email
        user_orm.hashed_password = user.hashed_password
        user_orm.role = user.role
        user_orm.manager_id = user.manager_id
        user_orm.is_active = user.is_active
        
        self.session.commit()

    def delete(self, user_id: str) -> None:
        """Delete a user by ID from the database."""
        user_orm = self.session.query(UserORM).filter(UserORM.id == user_id).first()
        if user_orm:
            self.session.delete(user_orm)
            self.session.commit()


# ============================================================
# PostgreSQL Access Request Repository
# ============================================================

class PostgresAccessRequestRepository(AccessRequestRepository):
    """PostgreSQL implementation of AccessRequestRepository."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, request: AccessRequest) -> None:
        """Add a new access request to the database."""
        request_orm = AccessRequestORM.from_domain(request)
        self.session.add(request_orm)
        self.session.commit()

    def get_by_id(self, request_id: str) -> Optional[AccessRequest]:
        """Retrieve access request by ID from database."""
        request_orm = self.session.query(AccessRequestORM).filter(
            AccessRequestORM.id == request_id
        ).first()
        if request_orm is None:
            return None
        return request_orm.to_domain()

    def get_all(self) -> List[AccessRequest]:
        """Retrieve all access requests from database."""
        requests_orm = self.session.query(AccessRequestORM).order_by(
            AccessRequestORM.created_at.desc()
        ).all()
        return [request_orm.to_domain() for request_orm in requests_orm]

    def get_by_requester(self, requester_id: str) -> List[AccessRequest]:
        """Retrieve all requests by a specific requester from database."""
        requests_orm = self.session.query(AccessRequestORM).filter(
            AccessRequestORM.requester_id == requester_id
        ).order_by(AccessRequestORM.created_at.desc()).all()
        return [request_orm.to_domain() for request_orm in requests_orm]

    def get_by_status(self, status: str) -> List[AccessRequest]:
        """Retrieve all requests with a specific status from database."""
        # Convert string status to enum
        try:
            status_enum = RequestStatus[status]
        except KeyError:
            return []
        
        requests_orm = self.session.query(AccessRequestORM).filter(
            AccessRequestORM.status == status_enum
        ).order_by(AccessRequestORM.created_at.desc()).all()
        return [request_orm.to_domain() for request_orm in requests_orm]

    def update(self, request: AccessRequest) -> None:
        """Update an existing access request in the database."""
        request_orm = self.session.query(AccessRequestORM).filter(
            AccessRequestORM.id == request.id
        ).first()
        if request_orm is None:
            raise ValueError(f"AccessRequest with id {request.id} not found")
        
        request_orm.requester_id = request.requester_id
        request_orm.requester_name = request.requester_name
        request_orm.manager_id = request.manager_id
        request_orm.target_system = request.target_system
        request_orm.access_level = request.access_level
        request_orm.system_type = request.system_type
        request_orm.justification = request.justification
        request_orm.expiration_date = request.expiration_date
        request_orm.status = request._status
        request_orm.rejection_reason = request.rejection_reason
        request_orm.changes_requested_by = request.changes_requested_by
        request_orm.changes_requested_comment = request.changes_requested_comment
        request_orm.provisioned_by = request.provisioned_by
        request_orm.updated_at = request.updated_at
        
        self.session.commit()

    def delete(self, request_id: str) -> None:
        """Delete an access request by ID from the database."""
        request_orm = self.session.query(AccessRequestORM).filter(
            AccessRequestORM.id == request_id
        ).first()
        if request_orm:
            self.session.delete(request_orm)
            self.session.commit()


# ============================================================
# PostgreSQL Audit Log Repository
# ============================================================

class PostgresAuditLogRepository(AuditLogRepository):
    """PostgreSQL implementation of AuditLogRepository."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, user_id: str, action: str, request_id: str, details: str) -> None:
        """Add an audit log entry to the database."""
        audit_log = AuditLogORM(
            user_id=user_id,
            action=action,
            request_id=request_id,
            details=details,
        )
        self.session.add(audit_log)
        self.session.commit()

    def get_by_request(self, request_id: str) -> List[dict]:
        """Retrieve all audit logs for a specific request from database."""
        logs = self.session.query(AuditLogORM).filter(
            AuditLogORM.request_id == request_id
        ).order_by(AuditLogORM.created_at.asc()).all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ]

    def get_all(self) -> List[dict]:
        """Retrieve all audit logs from database."""
        logs = self.session.query(AuditLogORM).order_by(
            AuditLogORM.created_at.desc()
        ).all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "request_id": log.request_id,
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ]


# ============================================================
# PostgreSQL Notification Repository
# ============================================================

class PostgresNotificationRepository(NotificationRepository):
    """PostgreSQL implementation of NotificationRepository."""

    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        user_id: str,
        title: str,
        message: str,
        request_id: Optional[str] = None,
    ) -> None:
        """Create a new notification in the database."""
        from uuid import uuid4
        from datetime import datetime, timezone
        
        notification = NotificationORM(
            id=str(uuid4()),
            user_id=user_id,
            title=title,
            message=message,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(notification)
        self.session.commit()

    def get_by_user(self, user_id: str, unread_only: bool = False) -> List[dict]:
        """Retrieve notifications for a specific user from database."""
        query = self.session.query(NotificationORM).filter(
            NotificationORM.user_id == user_id
        )
        
        if unread_only:
            from domain.enums import NotificationStatus
            query = query.filter(NotificationORM.status == NotificationStatus.PENDING)
        
        notifications = query.order_by(NotificationORM.created_at.desc()).all()
        
        return [
            {
                "id": notif.id,
                "title": notif.title,
                "message": notif.message,
                "status": notif.status.value,
                "request_id": notif.request_id,
                "created_at": notif.created_at,
                "read_at": notif.read_at,
            }
            for notif in notifications
        ]

    def mark_as_read(self, notification_id: str) -> None:
        """Mark a notification as read in the database."""
        from datetime import datetime, timezone
        from domain.enums import NotificationStatus
        
        notification = self.session.query(NotificationORM).filter(
            NotificationORM.id == notification_id
        ).first()
        
        if notification:
            notification.status = NotificationStatus.READ
            notification.read_at = datetime.now(timezone.utc)
            self.session.commit()

    def delete(self, notification_id: str) -> None:
        """Delete a notification from the database."""
        notification = self.session.query(NotificationORM).filter(
            NotificationORM.id == notification_id
        ).first()
        
        if notification:
            self.session.delete(notification)
            self.session.commit()
