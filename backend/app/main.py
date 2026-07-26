import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, health, materials, quiz
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title=settings.app_name, version="1.0.0", description="API for the AI Smart Education Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Accept Live Server, Vite, and other local frontend ports during development.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(materials.router, prefix="/api")
app.include_router(quiz.router, prefix="/api")
