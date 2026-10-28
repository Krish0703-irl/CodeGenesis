import logging

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

import config
from lessons import generate_lesson
from runner import run_code
from schemas import Lesson, LessonRequest, RunRequest, RunResult

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


@app.post("/run", response_model=RunResult)
async def run(request: RunRequest):
    return await run_in_threadpool(run_code, request.code, request.language, request.stdin)
