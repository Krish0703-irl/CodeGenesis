import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# "nvidia", "gemini", or "auto" (use whichever key is set, NVIDIA first)
LLM_PROVIDER = _env("LLM_PROVIDER", "auto").lower()

NVIDIA_API_KEY = _env("NVIDIA_API_KEY")
NVIDIA_MODEL = _env("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
NVIDIA_BASE_URL = _env("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-2.5-flash")

LLM_TIMEOUT_SECONDS = float(_env("LLM_TIMEOUT_SECONDS", "90"))

CORS_ORIGINS = [
    origin.strip()
    for origin in _env(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

MAX_CODE_CHARS = 20_000


def active_provider() -> str | None:
    """Return the LLM provider to use, or None to fall back to offline mode."""
    if LLM_PROVIDER == "nvidia":
        return "nvidia" if NVIDIA_API_KEY else None
    if LLM_PROVIDER == "gemini":
        return "gemini" if GEMINI_API_KEY else None
    if LLM_PROVIDER == "offline":
        return None
    if NVIDIA_API_KEY:
        return "nvidia"
    if GEMINI_API_KEY:
        return "gemini"
    return None
