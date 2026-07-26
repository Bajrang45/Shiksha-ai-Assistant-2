from datetime import UTC, datetime
from threading import Lock


class ChatStore:
    """Small in-memory history store for the foundation phase."""

    def __init__(self) -> None:
        self._items: dict[str, list[dict]] = {}
        self._lock = Lock()

    def add(self, user_id: str, question: str, answer: str) -> dict:
        item = {"question": question, "answer": answer, "created_at": datetime.now(UTC)}
        with self._lock:
            self._items.setdefault(user_id, []).append(item)
        return item

    def list_for_user(self, user_id: str) -> list[dict]:
        with self._lock:
            return list(reversed(self._items.get(user_id, [])))


chat_store = ChatStore()
