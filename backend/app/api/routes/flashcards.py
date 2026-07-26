import json
import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.schemas.flashcards import Flashcard, FlashcardRequest, FlashcardResponse
from app.services.material_store import material_store

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


def fallback_make_flashcards(topic: str, material: str) -> list[Flashcard]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", material.replace("\n", " "))
        if 45 <= len(sentence.strip()) <= 420
    ]
    topic_terms = {term.lower() for term in re.findall(r"[A-Za-z]{3,}", topic)}
    ranked_sentences = sorted(
        enumerate(sentences),
        key=lambda item: (sum(term in item[1].lower() for term in topic_terms), -item[0]),
        reverse=True,
    )
    cards: list[Flashcard] = []
    seen: set[str] = set()
    for _, sentence in ranked_sentences:
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


def llm_make_flashcards(topic: str, material: str, api_key: str, model: str) -> list[Flashcard]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
    
    prompt = f"""
Create exactly 8 flashcards based ONLY on the following study material. 
The topic is: {topic}. 
Return the output as JSON with a single key 'cards' containing a list of objects with 'front' and 'back' keys.

Study Material:
{material[:12000]}
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return [Flashcard(front=c["front"], back=c["back"]) for c in data.get("cards", [])]
    except Exception:
        return fallback_make_flashcards(topic, material)


@router.post("", response_model=FlashcardResponse)
async def create_flashcards(payload: FlashcardRequest, current_user: dict = Depends(get_current_user)) -> FlashcardResponse:
    settings = get_settings()
    material = await material_store.combined_text(current_user["id"])
    if not material:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload study material first. Flashcards are created from your uploaded notes.",
        )
        
    if settings.openai_api_key:
        cards = llm_make_flashcards(payload.topic, material, settings.openai_api_key, settings.openai_chat_model)
    else:
        cards = fallback_make_flashcards(payload.topic, material)
        
    if not cards:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="There is not enough readable content in the uploaded material to create flashcards.",
        )
    return FlashcardResponse(topic=payload.topic, cards=cards)
