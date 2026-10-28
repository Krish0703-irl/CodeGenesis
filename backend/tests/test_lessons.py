import pytest
from fastapi.testclient import TestClient

import config
import lessons
import llm
from main import app

BINARY_TREE = """#include <iostream>
using namespace std;

struct Node {
    int data;
    Node* left;
    Node* right;
    Node(int value) : data(value), left(nullptr), right(nullptr) {}
};

// Insert a value into the tree
Node* insert(Node* root, int value) {
    if (root == nullptr) {
        return new Node(value);
    }

    if (value < root->data) {
        root->left = insert(root->left, value);
    } else {
        root->right = insert(root->right, value);
    }
    return root;
}

int main() {
    Node* root = nullptr;
    root = insert(root, 5);
    cout << root->data << endl;
    return 0;
}"""


@pytest.fixture(autouse=True)
def no_ai_keys(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")
    monkeypatch.setattr(config, "NVIDIA_API_KEY", "")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")


def rebuilt(lesson) -> str:
    return "\n".join(step.code for step in lesson.steps)


def test_offline_lesson_rebuilds_code_exactly():
    lesson = lessons.generate_lesson(BINARY_TREE, "cpp")

    assert lesson.source == "offline"
    assert rebuilt(lesson) == BINARY_TREE
    titles = [step.title for step in lesson.steps]
    assert titles[0] == "Bring in the libraries we need"
    assert "Define the Node type" in titles
    assert "Write the insert function" in titles
    assert "Write the main entry point" in titles


def test_offline_quiz_answers_are_valid():
    lesson = lessons.generate_lesson(BINARY_TREE, "cpp")

    for step in lesson.steps:
        assert step.quiz is not None
        assert step.quiz.options[step.quiz.answer_index] == step.title


def test_offline_python_lesson():
    code = "import math\n\ndef area(r):\n    return math.pi * r * r\n\nprint(area(2))"
    lesson = lessons.generate_lesson(code, "python")

    assert rebuilt(lesson) == code
    assert [s.title for s in lesson.steps][:2] == [
        "Bring in the libraries we need",
        "Write the area function",
    ]


def test_build_steps_repairs_bad_ai_line_numbers():
    code = "a\nb\nc\nd\ne"
    plan = [
        {"title": "Third", "start_line": 4},
        {"title": "First", "start_line": 2},
        {"title": "Duplicate", "start_line": 2},
        {"title": "Too far", "start_line": 99},
        {"title": "Bad", "start_line": "x"},
    ]
    steps = lessons.build_steps(code, plan)

    assert [s.code for s in steps] == ["a\nb\nc", "d", "e"]
    assert [s.title for s in steps] == ["First", "Third", "Too far"]
    assert [(s.start_line, s.end_line) for s in steps] == [(1, 3), (4, 4), (5, 5)]


def test_ai_lesson_used_when_provider_works(monkeypatch):
    monkeypatch.setattr(config, "NVIDIA_API_KEY", "nvapi-test")
    plan = {
        "title": "Binary trees",
        "summary": "Build a BST",
        "steps": [
            {"title": "Includes", "explanation": "x", "start_line": 1,
             "quiz": {"question": "q", "options": ["a", "b", "c", "d"], "answer_index": 2}},
            {"title": "Node", "explanation": "y", "start_line": 4,
             "quiz": {"question": "q", "options": ["a"], "answer_index": 5}},
        ],
    }
    monkeypatch.setattr(llm, "plan_lesson", lambda provider, code, language: plan)

    lesson = lessons.generate_lesson(BINARY_TREE, "cpp")

    assert lesson.source == "ai"
    assert lesson.provider == "nvidia"
    assert rebuilt(lesson) == BINARY_TREE
    assert lesson.steps[0].quiz.answer_index == 2
    assert lesson.steps[1].quiz is None  # invalid quiz dropped


def test_ai_failure_falls_back_to_offline(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "key")

    def fail(provider, code, language):
        raise llm.LLMError("boom")

    monkeypatch.setattr(llm, "plan_lesson", fail)
    lesson = lessons.generate_lesson(BINARY_TREE, "cpp")

    assert lesson.source == "offline"
    assert "boom" in lesson.warning


@pytest.mark.parametrize(
    "reply",
    [
        '{"steps": [1]}',
        '```json\n{"steps": [1]}\n```',
        'Sure! Here is the lesson:\n{"steps": [1]}\nEnjoy.',
        '<think>Maybe {"steps": []}? No.</think>\n{"steps": [1]}',
    ],
)
def test_extract_json_tolerates_wrapping(reply):
    assert llm.extract_json(reply) == {"steps": [1]}


def test_generate_lesson_endpoint():
    client = TestClient(app)
    response = client.post("/generate-lesson", json={"code": BINARY_TREE, "language": "cpp"})

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "offline"
    assert "\n".join(s["code"] for s in body["steps"]) == BINARY_TREE


def test_generate_lesson_rejects_empty_code():
    client = TestClient(app)
    assert client.post("/generate-lesson", json={"code": ""}).status_code == 422
