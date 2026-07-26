from pydantic import BaseModel, Field


class QuizRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=200)


class QuizQuestion(BaseModel):
    question: str
    answer: str


class QuizResponse(BaseModel):
    topic: str
    questions: list[QuizQuestion]
