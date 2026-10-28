# CodeGenesis

AI-powered code reconstruction and interactive learning platform.

## Vision

CodeGenesis takes completed source code and transforms it into an
interactive step-by-step learning experience.

It explains why each part of the program is created while progressively
typing the code and providing voice narration.

## Features

- **Code-to-learning-plan generation** – an AI teacher (NVIDIA or Gemini)
  splits your program into the steps a programmer would naturally write it in
- **Step-by-step code reconstruction** – the steps always rebuild your exact
  original code, line for line
- **Live code typing** – each step's code types itself into the editor, with
  the new lines highlighted
- **Voice explanations** – each step is read aloud using your browser's
  built-in speech
- **Interactive questions** – a multiple-choice question after every step
- **Code execution** – run C++, C or Python programs from the home page or
  at the end of a lesson, with optional input, and see the output or errors
- **Progress tracking** – your current step, completed steps and quiz answers
  are saved in the browser, so you can resume any lesson later
- **Offline mode** – with no API key, a built-in rule-based teacher still
  builds a basic lesson

## Tech Stack

### Frontend
- React
- TypeScript
- Monaco Editor

### Backend
- Python
- FastAPI
- g++ / gcc (for running C/C++ code)

### AI
- NVIDIA API (default model `meta/llama-3.3-70b-instruct`)
- Google Gemini API (default model `gemini-2.5-flash`)

### Infrastructure
- Git
- GitHub
- Docker

## Getting started

### 1. Get an AI key (optional but recommended)

Use either one:

- **NVIDIA:** create a free key at https://build.nvidia.com (starts with `nvapi-`)
- **Gemini:** create a free key at https://aistudio.google.com/apikey

Then copy the example settings file and paste your key in:

```bash
cp backend/.env.example backend/.env
```

`.env` is ignored by git, so your key is never committed.

### 2. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload
```

The API runs at http://127.0.0.1:8000 (interactive docs at `/docs`).

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, paste some code (or load a sample) and press
**Teach Me This**.

### Run with Docker

```bash
docker compose up --build
```

Then open http://localhost:5173. The backend reads your key from
`backend/.env`.

## Configuration

All settings live in `backend/.env`:

| Variable | Default | What it does |
| --- | --- | --- |
| `LLM_PROVIDER` | `auto` | `auto` uses NVIDIA if its key is set, else Gemini. Also `nvidia`, `gemini`, `offline` |
| `NVIDIA_API_KEY` | | Your NVIDIA API key |
| `NVIDIA_MODEL` | `meta/llama-3.3-70b-instruct` | Any chat model from build.nvidia.com |
| `GEMINI_API_KEY` | | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Any Gemini model |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Frontend URLs allowed to call the API |

The frontend reads `VITE_API_URL` (default `http://127.0.0.1:8000`).

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Whether an AI provider is configured |
| `POST` | `/generate-lesson` | Body `{ "code": "...", "language": "cpp" }`, returns the lesson steps |
| `POST` | `/run` | Body `{ "code": "...", "language": "cpp", "stdin": "" }`, compiles and runs the code |

## Code execution safety

`/run` compiles and runs whatever code it receives **on the machine running
the backend**. Each run gets a temporary folder that is deleted afterwards,
a 5 second CPU/time limit, a 512 MB memory limit and capped output, but it
is not a full sandbox.

That is fine for running CodeGenesis on your own computer. If anyone else
can reach the backend, run it in Docker (`docker compose up`), which runs
the code as a non-root user inside a container, and never expose port 8000
to the internet.

## Tests

```bash
cd backend
pytest
```

```bash
cd frontend
npm run lint
npm run build
```
