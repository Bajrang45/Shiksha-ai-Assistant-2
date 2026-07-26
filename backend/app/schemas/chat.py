from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4_000)


class ChatSource(BaseModel):
    filename: str
    page: int | None = None
    confidence: int = Field(ge=0, le=100)


class ChatResponse(BaseModel):
    answer: str
    source: ChatSource | None = None


class ChatHistoryItem(BaseModel):
    question: str
    answer: str
    created_at: datetime
