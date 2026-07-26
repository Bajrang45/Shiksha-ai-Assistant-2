import re
from threading import Lock


class MaterialStore:
    """In-memory study materials for the current foundation-phase server session."""

    def __init__(self) -> None:
        self._materials: dict[str, list[dict]] = {}
        self._lock = Lock()

    def add(self, user_id: str, filename: str, text: str) -> None:
        with self._lock:
            self._materials.setdefault(user_id, []).append({"filename": filename, "text": text})

    def combined_text(self, user_id: str, limit: int = 12_000) -> str:
        with self._lock:
            materials = self._materials.get(user_id, [])
            return "\n\n".join(f"Source: {item['filename']}\n{item['text']}" for item in materials)[:limit]

    def best_source(self, user_id: str, question: str) -> dict | None:
        """Return the most relevant uploaded document and, for PDFs, its source page."""
        terms = {term.lower() for term in re.findall(r"[a-zA-Z]{3,}", question)}
        with self._lock:
            materials = list(self._materials.get(user_id, []))
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


material_store = MaterialStore()
