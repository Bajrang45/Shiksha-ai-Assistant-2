import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.flashcards import Flashcard, FlashcardRequest, FlashcardResponse
from app.services.material_store import material_store

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


def make_flashcards(topic: str, material: str) -> list[Flashcard]:
    """Create concise recall cards from readable sentences in uploaded notes."""
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", material.replace("\n", " "))
        if 45 <= len(sentence.strip()) <= 420
    ]
    cards: list[Flashcard] = []
    seen: set[str] = set()
    for sentence in sentences:
        terms = re.findall(r"\b[A-Za-z][A-Za-z-]{4,}\b", sentence)
        if not terms:
            continue
        term = max(terms, key=len)
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        cards.append(Flashcard(front=f"What should you remember about {term}?", back=sentence))
        if len(cards) == 8:
            break
    return cards


@router.post("", response_model=FlashcardResponse)
def create_flashcards(payload: FlashcardRequest, current_user: dict = Depends(get_current_user)) -> FlashcardResponse:
    material = material_store.combined_text(current_user["id"])
    if not material:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload study material first. Flashcards are created from your uploaded notes.",
        )
    cards = make_flashcards(payload.topic, material)
    if not cards:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="There is not enough readable content in the uploaded material to create flashcards.",
        )
    return FlashcardResponse(topic=payload.topic, cards=cards)
