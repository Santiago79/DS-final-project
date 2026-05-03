from domain.entities import User

# Empezamos con la base de datos vacía para probar que el startup event funciona
MOCK_USERS_DB = []

class MockUserRepository:
    """Mock alineado con la nueva interfaz UserRepository."""
    def add(self, user: User):
        MOCK_USERS_DB.append(user)

    def update(self, user: User):
        global MOCK_USERS_DB
        MOCK_USERS_DB = [u for u in MOCK_USERS_DB if u.email != user.email]
        MOCK_USERS_DB.append(user)

    def delete(self, user_id: str):
        global MOCK_USERS_DB
        MOCK_USERS_DB = [u for u in MOCK_USERS_DB if str(u.id) != str(user_id)]

    def get_by_id(self, user_id: str) -> User | None:
        return next((u for u in MOCK_USERS_DB if str(u.id) == str(user_id)), None)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in MOCK_USERS_DB if u.email == email), None)

    def get_all(self):
        return MOCK_USERS_DB


class MockRequestRepository:
    """Mock alineado con la nueva interfaz AccessRequestRepository."""
    def __init__(self):
        self.requests = []

    def add(self, request):
        self.requests.append(request)

    def update(self, request):
        self.requests = [r for r in self.requests if str(r.id) != str(request.id)]
        self.requests.append(request)

    def get_by_id(self, request_id: str):
        return next((r for r in self.requests if str(r.id) == request_id), None)

    def get_all(self):
        return self.requests

    def get_by_requester(self, requester_id: str):
        return [r for r in self.requests if str(r.requester_id) == str(requester_id)]

    def get_by_status(self, status_str: str):
        return [r for r in self.requests if str(r.status.value) == status_str]


class MockEventBus:
    def publish(self, event):
        print(f"[EventBus Mock] Evento publicado: {event.__class__.__name__}")