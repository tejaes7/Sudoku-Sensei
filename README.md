# Explainable Sudoku AI Coach

CSE 311 Artificial Intelligence project. An interactive web app that teaches Sudoku and the AI behind it.
It uses a Constraint Satisfaction Problem (CSP) engine (forward checking, AC-3, MRV, LCV and Norvig's
constraint propagation) to explain each deduction, check moves and simulate "what if" moves.
The **AI Teacher** chat is neuro-symbolic: the CSP engine reasons and verifies, and an optional LLM
(any OpenAI-compatible API) phrases the explanation. It works offline without a key.

## Run

```bash
pip install fastapi uvicorn httpx
python -m uvicorn sudoku_ai_coach.api.app:app --host 127.0.0.1 --port 8000
```

Then open http://localhost:8000.

Optional, to let an LLM phrase the AI Teacher's answers: copy `.env.example` to `.env` and set `AI_TEACHER_API_KEY`
(plus `AI_TEACHER_BASE_URL` / `AI_TEACHER_MODEL` for Groq, Gemini, OpenRouter, ...).

## Test

```bash
python -m unittest discover -s tests -t .
python -m unittest discover -s sudoku_ai_coach/tests -t .
```

## Layout

```
src/                CSP engine: board geometry, solver (FC/AC-3/MRV/LCV/Norvig), validator
generate_dataset.py Random valid grid + clue removal (used by the puzzle bank builder)
sudoku_ai_coach/    FastAPI backend (api/), human-technique engine (api/techniques/), web UI (static/)
data/               puzzle_bank.json and generated_pool.json used by the coach
```

See [sudoku_ai_coach/README.md](sudoku_ai_coach/README.md) for the full design.
