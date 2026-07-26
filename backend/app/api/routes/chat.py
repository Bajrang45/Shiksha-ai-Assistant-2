from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.schemas.chat import ChatHistoryItem, ChatRequest, ChatResponse
from app.services.chat_store import chat_store
from app.services.material_store import material_store

router = APIRouter(prefix="/chat", tags=["Chat"])

SYSTEM_INSTRUCTIONS = """You are Shiksha AI, a careful and encouraging study assistant.
Give clear, accurate educational answers. Explain important reasoning step by step when helpful.
Do not invent facts, sources, citations, or certainty. If a question is ambiguous, ask one focused
clarifying question. For medical, legal, financial, or other high-stakes topics, provide general
educational information and advise consulting a qualified professional. Keep answers concise unless
the student asks for depth."""


@router.post("", response_model=ChatResponse)
def ask_chat(payload: ChatRequest, current_user: dict = Depends(get_current_user)) -> ChatResponse:
    settings = get_settings()
    material_text = material_store.combined_text(current_user["id"])
    source = material_store.best_source(current_user["id"], payload.question)
    if not settings.openai_api_key:
        if material_text:
            answer = extractive_answer(payload.question, material_text)
            chat_store.add(current_user["id"], payload.question, answer)
            return ChatResponse(answer=answer, source=source)
        answer = local_study_response(payload.question)
        chat_store.add(current_user["id"], payload.question, answer)
        return ChatResponse(answer=answer)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=30.0, max_retries=0)
        response = client.responses.create(
            model=settings.openai_chat_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=f"Study material:\n{material_text or 'No uploaded material is available.'}\n\nStudent question: {payload.question}",
        )
        answer = response.output_text.strip()
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI chat dependencies are not installed. Run pip install -r requirements.txt.") from exc
    except Exception as exc:
        if exc.__class__.__name__ == "RateLimitError":
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenAI API quota is exhausted. Add credits or enable billing for the project that owns OPENAI_API_KEY, then try again.") from exc
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The AI service could not answer right now. Please try again.") from exc

    if not answer:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The AI service returned an empty answer. Please try again.")
    chat_store.add(current_user["id"], payload.question, answer)
    return ChatResponse(answer=answer, source=source)


@router.get("/history", response_model=list[ChatHistoryItem])
def chat_history(current_user: dict = Depends(get_current_user)) -> list[dict]:
    return chat_store.list_for_user(current_user["id"])


def extractive_answer(question: str, material: str) -> str:
    """Return the most relevant source sentences when hosted AI is not configured."""
    import re

    terms = {term.lower() for term in re.findall(r"[a-zA-Z]{3,}", question)}
    sentences = re.split(r"(?<=[.!?])\s+", material.replace("\n", " "))
    ranked = sorted(sentences, key=lambda sentence: sum(term in sentence.lower() for term in terms), reverse=True)
    selected = [sentence.strip() for sentence in ranked[:3] if sentence.strip()]
    if not selected:
        return "I could not find a relevant passage in your uploaded material. Try asking with terms used in the document."
    return "Based on your uploaded material:\n\n" + " ".join(selected)


def local_study_response(question: str) -> str:
    """Keep the local demo useful before an OpenAI key is configured."""
    normalized = question.lower()
    if "ohm" in normalized:
        return "Ohm's Law states that voltage equals current multiplied by resistance: V = I × R. For example, if a 2 A current flows through a 5 Ω resistor, the voltage is 10 V. Upload your Physics notes and I can explain it using your chapter's examples."
    if "summar" in normalized:
        return "Upload the chapter or notes you want summarised, and I will extract its key concepts, definitions, and revision points."
    if "mcq" in normalized or "quiz" in normalized:
        return "Upload your study material first, then ask for MCQs. I will create questions grounded in the concepts found in your notes."
    return "I am ready to help you study. Upload a PDF, DOCX, PPTX, TXT file, or image first so I can answer from your material. You can also ask for a summary, flashcards, or a quiz."
