from pydantic import BaseModel, Field


class FlashcardRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=200)


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardResponse(BaseModel):
    topic: str
    cards: list[Flashcard]
