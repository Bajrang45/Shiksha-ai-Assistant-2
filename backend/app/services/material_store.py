import re
from datetime import datetime, timezone
from app.core.db import get_database


class MaterialStore:
    """In-memory study materials for the current foundation-phase server session, with MongoDB support."""

    def __init__(self) -> None:
        self._materials: dict[str, list[dict]] = {}

    async def add(self, user_id: str, filename: str, text: str) -> None:
        db = get_database()
        if db is not None:
            await db.materials.insert_one({
                "user_id": user_id,
                "filename": filename,
                "text": text,
                "created_at": datetime.now(timezone.utc)
            })
        else:
            self._materials.setdefault(user_id, []).append({"filename": filename, "text": text})

    async def _get_materials_for_user(self, user_id: str) -> list[dict]:
        db = get_database()
        if db is not None:
            cursor = db.materials.find({"user_id": user_id}, {"_id": 0})
            return await cursor.to_list(length=None)
        return list(self._materials.get(user_id, []))

    async def combined_text(self, user_id: str, limit: int = 12_000) -> str:
        materials = await self._get_materials_for_user(user_id)
        return "\n\n".join(f"Source: {item['filename']}\n{item['text']}" for item in materials)[:limit]

    async def best_source(self, user_id: str, question: str) -> dict | None:
        """Return the most relevant uploaded document and, for PDFs, its source page."""
        terms = {term.lower() for term in re.findall(r"[a-zA-Z]{3,}", question)}
        materials = await self._get_materials_for_user(user_id)
        
        if not materials:
            return None
        def score(item: dict) -> int:
            return sum(item["text"].lower().count(term) for term in terms)
        selected = max(materials, key=score)
        page_match = None
        if terms:
            for match in re.finditer(r"\[\[PAGE (\d+)\]\]", selected["text"]):
                page_match = match
                remaining = selected["text"][match.end():]
                next_marker = re.search(r"\[\[PAGE \d+\]\]", remaining)
                page_text = remaining[:next_marker.start()] if next_marker else remaining
                if any(term in page_text.lower() for term in terms):
                    break
        return {
            "filename": selected["filename"],
            "page": int(page_match.group(1)) if page_match else None,
            "confidence": min(97, max(72, 72 + score(selected) * 4)),
        }

    async def count_for_user(self, user_id: str) -> int:
        materials = await self._get_materials_for_user(user_id)
        return len(materials)

    async def list_recent_for_user(self, user_id: str, limit: int = 5) -> list[dict]:
        db = get_database()
        if db is not None:
            cursor = db.materials.find({"user_id": user_id}, {"_id": 0, "filename": 1, "created_at": 1}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        mats = list(reversed(self._materials.get(user_id, [])))
        return [{"filename": m["filename"]} for m in mats[:limit]]


material_store = MaterialStore()
