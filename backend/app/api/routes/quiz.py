import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.quiz import QuizQuestion, QuizRequest, QuizResponse
from app.services.material_store import material_store

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])
STOP_WORDS = {"about", "after", "again", "also", "because", "been", "being", "between", "could", "does", "each", "from", "have", "into", "most", "only", "other", "should", "their", "there", "these", "they", "this", "through", "using", "what", "when", "where", "which", "with", "would"}


def make_source_quiz(topic: str, material: str) -> list[QuizQuestion]:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", material.replace("\n", " ")) if len(sentence.strip()) > 45]
    questions: list[QuizQuestion] = []
    used_answers: set[str] = set()
    for sentence in sentences:
        words = re.findall(r"\b[A-Za-z][A-Za-z-]{4,}\b", sentence)
        candidates = [word for word in words if word.lower() not in STOP_WORDS and word.lower() not in used_answers]
        if not candidates:
            continue
        answer = max(candidates, key=len)
        masked = re.sub(rf"\b{re.escape(answer)}\b", "_____", sentence, count=1, flags=re.IGNORECASE)
        questions.append(QuizQuestion(question=f"Complete the statement about {topic}: {masked}", answer=answer))
        used_answers.add(answer.lower())
        if len(questions) == 5:
            break
    return questions


@router.post("", response_model=QuizResponse)
def create_quiz(payload: QuizRequest, current_user: dict = Depends(get_current_user)) -> QuizResponse:
    material = material_store.combined_text(current_user["id"])
    if not material:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload study material first. The quiz creator builds questions from your uploaded notes.",
        )
    questions = make_source_quiz(payload.topic, material)
    if not questions:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="There is not enough readable content in the uploaded material to create a quiz.")
    return QuizResponse(topic=payload.topic, questions=questions)
