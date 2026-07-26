"""Temporary in-memory repository for local Phase 1 development.

Replace this adapter with the MongoDB repository in the persistence phase; the
router is intentionally independent of the storage implementation.
"""
from datetime import datetime, timezone
from uuid import uuid4

from app.core.security import hash_password, verify_password


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, dict] = {}

    def create(self, name: str, email: str, password: str) -> dict:
        normalized_email = email.lower()
        if any(user["email"] == normalized_email for user in self._users.values()):
            raise ValueError("An account already exists for this email address.")
        user = {
            "id": str(uuid4()),
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc),
        }
        self._users[user["id"]] = user
        return user

    def authenticate(self, email: str, password: str) -> dict | None:
        user = next((u for u in self._users.values() if u["email"] == email.lower()), None)
        return user if user and verify_password(password, user["password_hash"]) else None

    def get(self, user_id: str) -> dict | None:
        return self._users.get(user_id)


user_store = UserStore()

