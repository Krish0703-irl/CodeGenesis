"""Turn a lesson plan (from the AI or the offline planner) into exact code steps."""

import logging

import config
import llm
import offline
from schemas import Lesson, Quiz, Step

logger = logging.getLogger(__name__)


def _clean_quiz(raw) -> Quiz | None:
    if not isinstance(raw, dict):
        return None
    options = [str(o) for o in raw.get("options") or [] if str(o).strip()]
    try:
        answer = int(raw.get("answer_index", -1))
    except (TypeError, ValueError):
        return None
    if len(options) < 2 or not 0 <= answer < len(options) or not raw.get("question"):
        return None
    return Quiz(
        question=str(raw["question"]),
        options=options,
        answer_index=answer,
        explanation=str(raw.get("explanation", "")),
    )


def build_steps(code: str, plan_steps: list[dict]) -> list[Step]:
    """Slice the original code by each step's start line.

    Only start lines are trusted from the plan, and they are sorted and
    de-duplicated, so the steps always rebuild the program exactly.
    """
    lines = code.splitlines()
    total = len(lines)

    by_start: dict[int, dict] = {}
    for raw in plan_steps:
        if not isinstance(raw, dict):
            continue
        try:
            start = int(raw.get("start_line", 0))
        except (TypeError, ValueError):
            continue
        start = min(max(start, 1), total)
        by_start.setdefault(start, raw)

    if not by_start:
        by_start[1] = {"title": "Write the program", "explanation": ""}
    if 1 not in by_start:
        first = min(by_start)
        by_start[1] = by_start.pop(first)

    starts = sorted(by_start)
    bounds = starts + [total + 1]
    steps: list[Step] = []
    for start, next_start in zip(bounds, bounds[1:]):
        raw = by_start[start]
        steps.append(
            Step(
                title=str(raw.get("title") or f"Step {len(steps) + 1}"),
                explanation=str(raw.get("explanation") or ""),
                code="\n".join(lines[start - 1 : next_start - 1]),
                start_line=start,
                end_line=next_start - 1,
                quiz=_clean_quiz(raw.get("quiz")),
            )
        )
    return steps


def generate_lesson(code: str, language: str) -> Lesson:
    code = code.replace("\r\n", "\n").rstrip("\n")
    provider = config.active_provider()
    warning = None

    if provider:
        try:
            plan = llm.plan_lesson(provider, code, language)
            return Lesson(
                title=str(plan.get("title") or "Rebuilding your program"),
                summary=str(plan.get("summary") or ""),
                language=language,
                source="ai",
                provider=provider,
                steps=build_steps(code, plan["steps"]),
            )
        except llm.LLMError as exc:
            logger.warning("AI lesson generation failed, using offline planner: %s", exc)
            warning = f"The AI lesson failed ({exc}), so this is a basic offline lesson."
    else:
        warning = "No AI key is set (NVIDIA_API_KEY or GEMINI_API_KEY), so this is a basic offline lesson."

    plan = offline.plan_lesson(code, language)
    return Lesson(
        title=plan["title"],
        summary=plan["summary"],
        language=language,
        source="offline",
        warning=warning,
        steps=build_steps(code, plan["steps"]),
    )
