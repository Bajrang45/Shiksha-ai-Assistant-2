from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.user_store import user_store

router = APIRouter(prefix="/auth", tags=["Authentication"])


def public_user(user: dict) -> UserResponse:
    return UserResponse(id=user["id"], name=user["name"], email=user["email"], created_at=user["created_at"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> TokenResponse:
    try:
        user = user_store.create(payload.name, str(payload.email), payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenResponse(access_token=create_access_token(user["id"]), user=public_user(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = user_store.authenticate(str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    return TokenResponse(access_token=create_access_token(user["id"]), user=public_user(user))


@router.get("/profile", response_model=UserResponse)
def profile(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return public_user(current_user)

