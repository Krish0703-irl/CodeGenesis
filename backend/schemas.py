from typing import Literal

from pydantic import BaseModel, Field

from config import MAX_CODE_CHARS

Language = Literal["cpp", "c", "python", "java", "javascript", "other"]


class LessonRequest(BaseModel):
    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)
    language: Language = "cpp"


class Quiz(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str = ""


class Step(BaseModel):
    title: str
    explanation: str
    code: str
    start_line: int
    end_line: int
    quiz: Quiz | None = None


class Lesson(BaseModel):
    title: str
    summary: str
    language: Language
    source: Literal["ai", "offline"]
    provider: str | None = None
    warning: str | None = None
    steps: list[Step]


RunLanguage = Literal["cpp", "c", "python"]


class RunRequest(BaseModel):
    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)
    language: RunLanguage = "cpp"
    stdin: str = Field(default="", max_length=10_000)


class RunResult(BaseModel):
    compile_output: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False
