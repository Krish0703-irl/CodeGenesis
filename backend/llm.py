"""Lesson planning with an LLM (NVIDIA NIM or Google Gemini) over plain HTTP."""

import json
import re

import httpx

import config

SYSTEM_PROMPT = """You are CodeGenesis, a patient programming teacher.
You receive a finished program with numbered lines. Teach it by rebuilding it
from scratch in the order a programmer would naturally write it.

Split the program into 3 to 12 consecutive steps that together cover every line,
top to bottom. For each step give:
- "title": a short imperative title (e.g. "Create the Node struct")
- "explanation": 2-4 sentences explaining WHY this code is needed and how it
  works, written for a beginner, in plain spoken English (it is read aloud,
  so avoid markdown and code symbols where possible)
- "start_line": the line number where this step begins (the first step starts
  at line 1, and each step starts after the previous one)
- "quiz": one multiple-choice question that checks understanding of this step,
  with "question", 4 "options", "answer_index" (0-based) and a one-sentence
  "explanation" of the correct answer

Reply with ONLY a JSON object, no markdown fences, in this exact shape:
{"title": "...", "summary": "...", "steps": [{"title": "...", "explanation": "...",
"start_line": 1, "quiz": {"question": "...", "options": ["...", "...", "...", "..."],
"answer_index": 0, "explanation": "..."}}]}"""


class LLMError(Exception):
    pass


def _numbered(code: str) -> str:
    return "\n".join(f"{i:>4} | {line}" for i, line in enumerate(code.splitlines(), start=1))


def _user_prompt(code: str, language: str) -> str:
    return f"Language: {language}\n\nProgram:\n{_numbered(code)}"


def extract_json(text: str) -> dict:
    """Parse a JSON object out of a model reply, tolerating fences and extra prose."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMError("The AI reply did not contain JSON.")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"The AI reply was not valid JSON: {exc}") from exc


def _call_nvidia(client: httpx.Client, code: str, language: str) -> str:
    response = client.post(
        f"{config.NVIDIA_BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {config.NVIDIA_API_KEY}"},
        json={
            "model": config.NVIDIA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(code, language)},
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    )
    response.raise_for_status()
    choices = response.json().get("choices") or []
    if not choices:
        raise LLMError("NVIDIA returned no choices.")
    return choices[0]["message"]["content"] or ""


def _call_gemini(client: httpx.Client, code: str, language: str) -> str:
    response = client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": config.GEMINI_API_KEY},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": _user_prompt(code, language)}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
            },
        },
    )
    response.raise_for_status()
    candidates = response.json().get("candidates") or []
    if not candidates:
        raise LLMError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts") or []
    return "".join(part.get("text", "") for part in parts)


PROVIDERS = {"nvidia": _call_nvidia, "gemini": _call_gemini}


def plan_lesson(provider: str, code: str, language: str) -> dict:
    """Ask the provider for a lesson plan. Raises LLMError on any failure."""
    try:
        with httpx.Client(timeout=config.LLM_TIMEOUT_SECONDS) as client:
            reply = PROVIDERS[provider](client, code, language)
    except httpx.HTTPStatusError as exc:
        raise LLMError(
            f"{provider} API returned {exc.response.status_code}: {exc.response.text[:200]}"
        ) from exc
    except httpx.HTTPError as exc:
        raise LLMError(f"Could not reach the {provider} API: {exc}") from exc

    plan = extract_json(reply)
    if not isinstance(plan.get("steps"), list) or not plan["steps"]:
        raise LLMError("The AI reply had no steps.")
    return plan
