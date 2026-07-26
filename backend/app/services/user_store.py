"""Temporary in-memory repository for local Phase 1 development.

Replace this adapter with the MongoDB repository in the persistence phase; the
router is intentionally independent of the storage implementation.
"""
from datetime import datetime, timezone
from uuid import uuid4

from app.core.security import hash_password, verify_password
from app.core.db import get_database


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, dict] = {}

    async def create(self, name: str, email: str, password: str) -> dict:
        db = get_database()
        normalized_email = email.lower()
        
        if db is not None:
            existing = await db.users.find_one({"email": normalized_email})
            if existing:
                raise ValueError("An account already exists for this email address.")
        else:
            if any(user["email"] == normalized_email for user in self._users.values()):
                raise ValueError("An account already exists for this email address.")
                
        user = {
            "id": str(uuid4()),
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc),
        }
        
        if db is not None:
            await db.users.insert_one(user)
        else:
            self._users[user["id"]] = user
            
        return user

    async def authenticate(self, email: str, password: str) -> dict | None:
        db = get_database()
        if db is not None:
            user = await db.users.find_one({"email": email.lower()})
        else:
            user = next((u for u in self._users.values() if u["email"] == email.lower()), None)
            
        return user if user and verify_password(password, user["password_hash"]) else None

    async def get(self, user_id: str) -> dict | None:
        db = get_database()
        if db is not None:
            return await db.users.find_one({"id": user_id})
        return self._users.get(user_id)


user_store = UserStore()
