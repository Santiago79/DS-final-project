import os
import requests

class AccessFlowClient:
    def __init__(self):
        self.base_url = os.getenv("BACKEND_API_URL", "http://backend:8000")
        self.session = requests.Session()

    def set_token(self, token: str):
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def login(self, email: str, password: str) -> dict:
        url = f"{self.base_url}/auth/login"
        payload = {"username": email, "password": password}
        response = self.session.post(url, data=payload)
        response.raise_for_status()
        data = response.json()
        self.set_token(data["access_token"])
        return data

    def get_requests(self) -> list:
        url = f"{self.base_url}/requests"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
        
    def provision_request(self, request_id: str) -> dict:
        url = f"{self.base_url}/requests/{request_id}/provision"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def get_notifications(self, unread_only: bool = False) -> list:
        url = f"{self.base_url}/notifications"
        response = self.session.get(url)
        response.raise_for_status()
        notifications = response.json()
        if unread_only:
            notifications = [n for n in notifications if n["status"] == "PENDING"]
        return notifications

    def mark_notification_read(self, notification_id: str) -> dict:
        url = f"{self.base_url}/notifications/{notification_id}/read"
        response = self.session.put(url)
        response.raise_for_status()
        return response.json()

    def get_audit_log(self, request_id: str = None) -> list:
        if request_id:
            url = f"{self.base_url}/requests/{request_id}/audit-log"
        else:
            url = f"{self.base_url}/audit-log"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_request_detail(self, request_id: str) -> dict:
        url = f"{self.base_url}/requests/{request_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_request(self, target_system: str, access_level: str, justification: str, system_type: str = "OTHER", expiration_date: str = None) -> dict:
        url = f"{self.base_url}/requests"
        payload = {
            "target_system": target_system,
            "access_level": access_level,
            "justification": justification,
            "system_type": system_type,
        }
        if expiration_date:
            payload["expiration_date"] = expiration_date

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def approve_request(self, request_id: str) -> dict:
        url = f"{self.base_url}/requests/{request_id}/approve"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def reject_request(self, request_id: str, reason: str) -> dict:
        url = f"{self.base_url}/requests/{request_id}/reject"
        response = self.session.post(url, json={"reason": reason})
        response.raise_for_status()
        return response.json()

    def request_changes(self, request_id: str, reason: str) -> dict:
        url = f"{self.base_url}/requests/{request_id}/request-changes"
        response = self.session.post(url, json={"reason": reason})
        response.raise_for_status()
        return response.json()
    
    def return_to_draft(self, request_id: str) -> dict:
        """Devuelve la solicitud a DRAFT para edición (cuando se solicitaron cambios)."""
        url = f"{self.base_url}/requests/{request_id}/return-to-draft"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()
    def update_request(self, request_id: str, target_system: str, access_level: str,
                   justification: str, system_type: str = "OTHER",
                   expiration_date: str = None) -> dict:
        url = f"{self.base_url}/requests/{request_id}"
        payload = {
            "target_system": target_system,
            "access_level": access_level,
            "justification": justification,
            "system_type": system_type,
        }
        if expiration_date:
            payload["expiration_date"] = expiration_date
        response = self.session.put(url, json=payload)
        response.raise_for_status()
        return response.json()

    def submit_request(self, request_id: str) -> dict:
        url = f"{self.base_url}/requests/{request_id}/submit"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()