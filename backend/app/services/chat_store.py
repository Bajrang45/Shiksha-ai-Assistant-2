from datetime import UTC, datetime
from app.core.db import get_database


class ChatStore:
    """Small in-memory history store for the foundation phase, with MongoDB support."""

    def __init__(self) -> None:
        self._items: dict[str, list[dict]] = {}

    async def add(self, user_id: str, question: str, answer: str) -> dict:
        item = {"user_id": user_id, "question": question, "answer": answer, "created_at": datetime.now(UTC)}
        db = get_database()
        
        if db is not None:
            await db.chats.insert_one(item.copy())
        else:
            self._items.setdefault(user_id, []).append(item)
            
        return item

    async def list_for_user(self, user_id: str) -> list[dict]:
        db = get_database()
        if db is not None:
            cursor = db.chats.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1)
            return await cursor.to_list(length=100)
            
        return list(reversed(self._items.get(user_id, [])))

    async def count_for_user(self, user_id: str) -> int:
        db = get_database()
        if db is not None:
            return await db.chats.count_documents({"user_id": user_id})
        return len(self._items.get(user_id, []))

    async def list_recent_for_user(self, user_id: str, limit: int = 5) -> list[dict]:
        db = get_database()
        if db is not None:
            cursor = db.chats.find({"user_id": user_id}, {"_id": 0, "question": 1, "created_at": 1}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        return list(reversed(self._items.get(user_id, [])))[:limit]


chat_store = ChatStore()
