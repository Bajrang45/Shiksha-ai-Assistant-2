import json
import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.schemas.quiz import QuizQuestion, QuizRequest, QuizResponse
from app.services.material_store import material_store

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])
STOP_WORDS = {"about", "after", "again", "also", "because", "been", "being", "between", "could", "does", "each", "from", "have", "into", "most", "only", "other", "should", "their", "there", "these", "they", "this", "through", "using", "what", "when", "where", "which", "with", "would"}


def fallback_make_quiz(topic: str, material: str) -> list[QuizQuestion]:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", material.replace("\n", " ")) if len(sentence.strip()) > 45]
    topic_terms = {word.lower() for word in re.findall(r"[A-Za-z]{3,}", topic) if word.lower() not in STOP_WORDS}
    ranked_sentences = sorted(
        enumerate(sentences),
        key=lambda item: (sum(term in item[1].lower() for term in topic_terms), -item[0]),
        reverse=True,
    )
    questions: list[QuizQuestion] = []
    used_answers: set[str] = set()
    for _, sentence in ranked_sentences:
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


def llm_make_quiz(topic: str, material: str, api_key: str, model: str) -> list[QuizQuestion]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
    
    prompt = f"""
Create exactly 5 quiz questions based ONLY on the following study material. 
The topic is: {topic}. 
Return the output as JSON with a single key 'questions' containing a list of objects with 'question' and 'answer' keys.

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
        return [QuizQuestion(question=q["question"], answer=q["answer"]) for q in data.get("questions", [])]
    except Exception:
        return fallback_make_quiz(topic, material)


@router.post("", response_model=QuizResponse)
async def create_quiz(payload: QuizRequest, current_user: dict = Depends(get_current_user)) -> QuizResponse:
    settings = get_settings()
    material = await material_store.combined_text(current_user["id"])
    if not material:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload study material first. The quiz creator builds questions from your uploaded notes.",
        )
        
    if settings.openai_api_key:
        questions = llm_make_quiz(payload.topic, material, settings.openai_api_key, settings.openai_chat_model)
    else:
        questions = fallback_make_quiz(payload.topic, material)
        
    if not questions:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="There is not enough readable content in the uploaded material to create a quiz.")
    return QuizResponse(topic=payload.topic, questions=questions)
