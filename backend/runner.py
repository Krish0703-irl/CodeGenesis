"""Compile and run learner code locally with time, memory and output limits.

This runs untrusted code on the machine hosting the backend. It is meant for
local use; run the backend in Docker for isolation if others can reach it.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from schemas import RunResult

COMPILE_TIMEOUT = 15
RUN_TIMEOUT = 5
MAX_OUTPUT = 64_000
MEMORY_LIMIT = 512 * 1024 * 1024

COMPILERS = {
    "cpp": ("g++", "main.cpp", ["-std=c++17", "-O0", "-Wall"]),
    "c": ("gcc", "main.c", ["-std=c11", "-O0", "-Wall", "-lm"]),
}


def _limit_resources():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (RUN_TIMEOUT, RUN_TIMEOUT))
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))
    except (ImportError, ValueError, OSError):
        pass


def _trim(text: str) -> str:
    if len(text) > MAX_OUTPUT:
        return text[:MAX_OUTPUT] + "\n... output truncated ..."
    return text


def _run(command: list[str], cwd: str, stdin: str, timeout: int, limit: bool) -> tuple[subprocess.CompletedProcess | None, bool]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            preexec_fn=_limit_resources if limit and os.name == "posix" else None,
        )
        return completed, False
    except subprocess.TimeoutExpired:
        return None, True


def run_code(code: str, language: str, stdin: str = "") -> RunResult:
    with tempfile.TemporaryDirectory(prefix="codegenesis-") as workdir:
        if language == "python":
            source = os.path.join(workdir, "main.py")
            command = [sys.executable, "-I", "main.py"]
        else:
            compiler, filename, flags = COMPILERS[language]
            if shutil.which(compiler) is None:
                return RunResult(compile_output=f"{compiler} is not installed on the server.", exit_code=None)
            source = os.path.join(workdir, filename)
            command = [os.path.join(workdir, "program")]

        with open(source, "w", encoding="utf-8") as f:
            f.write(code)

        compile_output = ""
        if language in COMPILERS:
            compiler, filename, flags = COMPILERS[language]
            # Relative paths so errors read "main.cpp:3:5" instead of a temp path
            compiled, timed_out = _run(
                [compiler, filename, "-o", "program", *flags], workdir, "", COMPILE_TIMEOUT, limit=False
            )
            if timed_out:
                return RunResult(compile_output="Compilation timed out.", timed_out=True)
            compile_output = _trim(compiled.stderr)
            if compiled.returncode != 0:
                return RunResult(compile_output=compile_output, exit_code=compiled.returncode)

        completed, timed_out = _run(command, workdir, stdin, RUN_TIMEOUT, limit=True)
        if timed_out:
            return RunResult(
                compile_output=compile_output,
                stderr=f"Program stopped after {RUN_TIMEOUT} seconds (infinite loop or waiting for input?).",
                timed_out=True,
            )
        return RunResult(
            compile_output=compile_output,
            stdout=_trim(completed.stdout),
            stderr=_trim(completed.stderr.replace(workdir + os.sep, "")),
            exit_code=completed.returncode,
        )
