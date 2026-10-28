import logging

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

import config
from lessons import generate_lesson
from schemas import Lesson, LessonRequest

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="CodeGenesis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to CodeGenesis API"
    }


@app.get("/health")
def health():
    provider = config.active_provider()
    return {
        "status": "ok",
        "ai_enabled": provider is not None,
        "provider": provider,
    }


@app.post("/generate-lesson", response_model=Lesson)
async def create_lesson(request: LessonRequest):
    return await run_in_threadpool(generate_lesson, request.code, request.language)
