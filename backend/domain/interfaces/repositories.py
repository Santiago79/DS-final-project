"""
Repository interfaces for infrastructure implementations.

These interfaces define contracts that repositories must fulfill.
Infrastructure layer implements these with concrete ORM operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities import User, AccessRequest


class UserRepository(ABC):
    """Repository interface for User persistence."""

    @abstractmethod
    def add(self, user: User) -> None:
        """Add a new user to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email."""
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        """Retrieve all users."""
        pass

    @abstractmethod
    def update(self, user: User) -> None:
        """Update an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        """Delete a user by ID."""
        pass


class AccessRequestRepository(ABC):
    """Repository interface for AccessRequest persistence."""

    @abstractmethod
    def add(self, request: AccessRequest) -> None:
        """Add a new access request to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, request_id: str) -> Optional[AccessRequest]:
        """Retrieve access request by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[AccessRequest]:
        """Retrieve all access requests."""
        pass

    @abstractmethod
    def get_by_requester(self, requester_id: str) -> List[AccessRequest]:
        """Retrieve all requests by a specific requester."""
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[AccessRequest]:
        """Retrieve all requests with a specific status."""
        pass

    @abstractmethod
    def update(self, request: AccessRequest) -> None:
        """Update an existing access request."""
        pass

    @abstractmethod
    def delete(self, request_id: str) -> None:
        """Delete an access request by ID."""
        pass


class AuditLogRepository(ABC):
    """Repository interface for audit logging."""

    @abstractmethod
    def add(self, user_id: str, action: str, request_id: str, details: str) -> None:
        """Add an audit log entry."""
        pass

    @abstractmethod
    def get_by_request(self, request_id: str) -> List[dict]:
        """Retrieve all audit logs for a specific request."""
        pass

    @abstractmethod
    def get_all(self) -> List[dict]:
        """Retrieve all audit logs."""
        pass


class NotificationRepository(ABC):
    """Repository interface for notifications."""

    @abstractmethod
    def add(self, user_id: str, title: str, message: str, request_id: Optional[str] = None) -> None:
        """Create a new notification."""
        pass

    @abstractmethod
    def get_by_user(self, user_id: str, unread_only: bool = False) -> List[dict]:
        """Retrieve notifications for a specific user."""
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        pass

    @abstractmethod
    def delete(self, notification_id: str) -> None:
        """Delete a notification."""
        pass
