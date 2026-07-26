from pydantic import BaseModel


class MaterialResponse(BaseModel):
    filename: str
    summary: str
    characters_extracted: int
