import shutil

import pytest
from fastapi.testclient import TestClient

from main import app
from runner import run_code

needs_gpp = pytest.mark.skipif(shutil.which("g++") is None, reason="g++ not installed")


@needs_gpp
def test_cpp_program_runs_with_stdin():
    code = "#include <iostream>\nint main() { int n; std::cin >> n; std::cout << n * 2; return 0; }"
    result = run_code(code, "cpp", "21")

    assert result.exit_code == 0
    assert result.stdout == "42"


@needs_gpp
def test_cpp_compile_error_is_reported():
    result = run_code("int main() { return x; }", "cpp")

    assert result.exit_code != 0
    assert "was not declared" in result.compile_output
    assert result.compile_output.startswith("main.cpp")
    assert result.stdout == ""


@needs_gpp
def test_infinite_loop_is_stopped():
    result = run_code("int main() { while (true) {} }", "cpp")

    assert result.timed_out or result.exit_code != 0


def test_python_program_runs_with_stdin():
    result = run_code("print(input()[::-1])", "python", "abc")

    assert result.exit_code == 0
    assert result.stdout.strip() == "cba"


def test_python_runtime_error_is_reported():
    result = run_code("raise ValueError('nope')", "python")

    assert result.exit_code == 1
    assert "ValueError" in result.stderr


def test_huge_output_is_truncated():
    result = run_code("print('x' * 200000)", "python")

    assert result.stdout.endswith("... output truncated ...")


def test_run_endpoint():
    client = TestClient(app)
    response = client.post("/run", json={"code": "print(1 + 1)", "language": "python"})

    assert response.status_code == 200
    assert response.json()["stdout"].strip() == "2"


def test_run_endpoint_rejects_unsupported_language():
    client = TestClient(app)
    assert client.post("/run", json={"code": "x", "language": "rust"}).status_code == 422
