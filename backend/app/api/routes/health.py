from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "ai-smart-education-assistant"}

