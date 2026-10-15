"""
FastAPI Application Module - Milestone 4.
Serves the Explainable Adaptive Sudoku AI Coach REST API and mounts static web assets.
"""

import sys
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, parse_grid, grid_to_string
from src.csp_solver import CSPSolver
from src.validator import SudokuValidator

from .board_state import BoardState
from .analyze import analyze_board
from .coach_session import CoachSession
from .move_checker import check_move, generate_why_it_works
from .what_if import simulate_move
from .lesson_engine import LessonEngine
from .skill_check import SKILL_CHECK_QUESTIONS, evaluate_skill_check
from .hint_ladder import generate_hint_ladder
from .puzzle_bank import get_puzzles_by_tier, get_puzzle_by_id, load_puzzle_bank
from .puzzle_generator import get_fresh_puzzle, start_background_pool
from .ai_teacher import teacher_chat, teacher_status

# Default benchmark easy puzzle
DEFAULT_PUZZLE = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"

app = FastAPI(
    title="Explainable Adaptive Sudoku AI Coach",
    description="Interactive CSP-based Sudoku AI coach explaining deductions at 3 adaptive levels.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cache_control_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Shared in-memory board state and coach session
board_state = BoardState(DEFAULT_PUZZLE)
sessions: Dict[str, CoachSession] = {"default": CoachSession("default")}


def get_session(session_id: str = "default") -> CoachSession:
    if session_id not in sessions:
        sessions[session_id] = CoachSession(session_id)
    return sessions[session_id]


# --------------------------------------------------------------------------
# Request & Response Schemas
# --------------------------------------------------------------------------
class MoveRequest(BaseModel):
    cell: str = Field(..., example="A1")
    value: int = Field(..., ge=0, le=9, example=4)
    session_id: str = "default"


class WhatIfRequest(BaseModel):
    cell: str = Field(..., example="D7")
    value: int = Field(..., ge=1, le=9, example=7)


class LoadPuzzleRequest(BaseModel):
    puzzle: str
    difficulty: Optional[str] = "custom"
    session_id: str = "default"


class SkillCheckAnswerRequest(BaseModel):
    answers: Dict[str, str]


class LessonVerifyRequest(BaseModel):
    lesson_id: str
    cell: str
    value: Optional[int] = None


class HintLadderRequest(BaseModel):
    stage: int = 1
    user_level: str = "intermediate"
    session_id: str = "default"


class TeacherCheckMoveRequest(BaseModel):
    cell: str
    value: int


class WhyItWorksRequest(BaseModel):
    cell: str
    value: int


class LoadBankedPuzzleRequest(BaseModel):
    puzzle_id: str
    session_id: str = "default"


class TeacherChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    history: List[Dict[str, str]] = []
    selected_cell: Optional[str] = None
    user_level: str = "intermediate"


class GeneratePuzzleRequest(BaseModel):
    level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    session_id: str = "default"


# --------------------------------------------------------------------------
# API Endpoints (§7 Contract)
# --------------------------------------------------------------------------
@app.get("/api/board")
def get_board():
    """Return current board state, cell assignments, clue flags, and counts."""
    return board_state.to_dict()


@app.post("/api/move")
def apply_move(req: MoveRequest):
    """
    Apply a player move.
    If value == 0, clears the cell (if not a clue).
    Otherwise, checks constraints and sets the value.
    """
    if req.cell not in SQUARES:
        raise HTTPException(status_code=400, detail=f"Invalid cell: {req.cell}")

    if board_state.is_clue(req.cell):
        raise HTTPException(status_code=400, detail=f"Cell {req.cell} is an initial clue and cannot be modified.")

    if req.value == 0:
        # Clearing cell
        board_state.set_cell_value(req.cell, 0)
        session = get_session(req.session_id)
        session.reset_session()
        return {
            "success": True,
            "action": "cleared",
            "cell": req.cell,
            "board": board_state.to_dict(),
            "analysis": analyze_board(board_state)
        }

    # Validate move
    check_res = check_move(board_state, req.cell, req.value)
    if not check_res["valid"]:
        return {
            "success": False,
            "check_result": check_res,
            "message": check_res["message"]
        }

    applied = board_state.set_cell_value(req.cell, req.value)
    session = get_session(req.session_id)
    session.reset_session()

    return {
        "success": applied,
        "action": "placed",
        "cell": req.cell,
        "value": req.value,
        "check_result": check_res,
        "board": board_state.to_dict(),
        "analysis": analyze_board(board_state)
    }


@app.get("/api/analyze")
def get_analysis():
    """Return live constraint metrics, domain sets, MRV cell, and contradiction status."""
    return analyze_board(board_state)


@app.get("/api/hint")
def get_hint(
    level: Optional[int] = Query(None, ge=1, le=3, description="1: Socratic, 2: Focused, 3: Full"),
    escalate: bool = Query(False, description="Whether to escalate from previous hint level"),
    session_id: str = "default"
):
    """
    Generate an adaptive hint for the current board state at the requested level.
    """
    session = get_session(session_id)
    hint_data = session.get_hint(board_state, requested_level=level, escalate=escalate)
    return hint_data


@app.get("/api/explain")
def explain_cell_endpoint(
    cell: str = Query(..., description="Norvig cell coordinate, e.g. D7"),
    session_id: str = "default"
):
    """Return detailed constraint and candidate explanation for a specific cell."""
    if cell not in SQUARES:
        raise HTTPException(status_code=400, detail=f"Invalid cell: {cell}")
    session = get_session(session_id)
    return session.explain_cell(board_state, cell)


@app.post("/api/check-move")
def check_move_endpoint(req: MoveRequest):
    """
    Evaluate a move against immediate peer constraints (Case A)
    and forward-checking future wipeouts (Case B), or confirm consistency (Case C).
    """
    return check_move(board_state, req.cell, req.value)


@app.post("/api/what-if")
def what_if_endpoint(req: WhatIfRequest):
    """
    Simulate a hypothetical move on a clone of the board and return the resulting cascade.
    Guarantees the actual board is never mutated.
    """
    return simulate_move(board_state, req.cell, req.value)


@app.post("/api/undo")
def undo_move(session_id: str = "default"):
    """Undo the most recent user move."""
    undone = board_state.undo()
    session = get_session(session_id)
    session.reset_session()
    return {
        "success": undone is not None,
        "undone_move": undone,
        "board": board_state.to_dict(),
        "analysis": analyze_board(board_state)
    }


@app.post("/api/reset")
def reset_board(session_id: str = "default"):
    """Reset the current puzzle back to initial clues."""
    board_state.reset()
    session = get_session(session_id)
    session.reset_session()
    return {
        "success": True,
        "message": "Board reset to initial clues.",
        "board": board_state.to_dict(),
        "analysis": analyze_board(board_state)
    }


@app.post("/api/solve")
def solve_board():
    """
    Solve the active board using the existing CSPSolver (Norvig dual-rule propagation + search).
    Validates final solution with SudokuValidator before applying.
    """
    current_str = board_state.get_current_string()
    initial_str = board_state.get_initial_string()

    solver = CSPSolver(propagation="norvig", timeout_sec=5.0)
    telemetry = solver.solve(current_str)

    if not telemetry.solved or not telemetry.solution:
        # Fallback to solving from initial clues if current user entries caused conflict
        telemetry = solver.solve(initial_str)

    if telemetry.solved and telemetry.solution:
        # Verify correctness with mathematical validator
        is_valid, msg = SudokuValidator.is_valid_grid(telemetry.solution, initial_str)
        if not is_valid:
            return {"success": False, "message": f"Solver produced invalid solution: {msg}"}

        # Apply solution to board_state
        for s in SQUARES:
            if not board_state.is_clue(s):
                from src.board import SQUARE_TO_COORD
                r, c = SQUARE_TO_COORD[s]
                sol_val = int(telemetry.solution[r * 9 + c])
                board_state.board.grid[r][c] = sol_val

        return {
            "success": True,
            "solution": telemetry.solution,
            "runtime_ms": telemetry.runtime_ms,
            "nodes_expanded": telemetry.nodes_expanded,
            "board": board_state.to_dict(),
            "analysis": analyze_board(board_state)
        }

    return {
        "success": False,
        "message": telemetry.error_message or "CSP Solver could not find a valid solution."
    }


@app.get("/api/puzzles")
def list_sample_puzzles():
    """Return curated sample puzzles across difficulty tiers."""
    samples = [
        {
            "id": "easy_1",
            "name": "Classic Easy",
            "difficulty": "easy",
            "clues": 38,
            "puzzle": "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        },
        {
            "id": "medium_1",
            "name": "Balanced Medium",
            "difficulty": "medium",
            "clues": 32,
            "puzzle": "200080300060070084030500209000105408000000000402706000301007040720040060004010003"
        },
        {
            "id": "hard_1",
            "name": "Challenging Hard",
            "difficulty": "hard",
            "clues": 26,
            "puzzle": "000000012000000003002300400001800005060070800000009000008500000900040500470006000"
        },
        {
            "id": "extreme_1",
            "name": "Arto Inkala Extreme (Escargot)",
            "difficulty": "extreme",
            "clues": 21,
            "puzzle": "100007090030020008009600500005300900010080002600004000300000010040000007007000300"
        }
    ]
    return {"puzzles": samples}


@app.post("/api/load-puzzle")
def load_puzzle_endpoint(req: LoadPuzzleRequest):
    """Load a new puzzle string into the board state."""
    try:
        parsed = parse_grid(req.puzzle)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid 81-character puzzle string: {e}")

    board_state.load_puzzle(req.puzzle)
    session = get_session(req.session_id)
    session.reset_session()

    return {
        "success": True,
        "difficulty": req.difficulty,
        "board": board_state.to_dict(),
        "analysis": analyze_board(board_state)
    }


# --------------------------------------------------------------------------
# Teacher & Pedagogy Endpoints
# --------------------------------------------------------------------------
@app.get("/api/teacher/skill-check")
def get_skill_check():
    """Return the 4 quick skill-check assessment questions."""
    return {"questions": SKILL_CHECK_QUESTIONS}


@app.post("/api/teacher/skill-check")
def post_skill_check(req: SkillCheckAnswerRequest):
    """Evaluate skill-check quiz answers and return level recommendation."""
    result = evaluate_skill_check(req.answers)
    return result


@app.get("/api/teacher/lessons")
def get_lessons_catalog():
    """Return the complete interactive beginner curriculum (Lessons a–g)."""
    return {"lessons": LessonEngine.get_all_lessons()}


@app.get("/api/teacher/lesson/{lesson_id}")
def get_lesson_detail(lesson_id: str):
    """Return a single lesson's configuration and tasks."""
    lesson = LessonEngine.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")
    return {"lesson": lesson}


@app.post("/api/teacher/lesson/verify")
def verify_lesson_task(req: LessonVerifyRequest):
    """Verify user interaction inside a guided lesson."""
    return LessonEngine.verify_lesson_action(req.lesson_id, req.cell, req.value)


@app.post("/api/teacher/hint-ladder")
def get_hint_ladder_endpoint(req: HintLadderRequest):
    """
    Produce progressive 3-stage hint (Nudge -> Technique -> Reveal) with mistake detection.
    Always checks board for mistakes first.
    """
    res = generate_hint_ladder(
        grid=board_state.board.grid,
        initial_puzzle=board_state.initial_puzzle,
        stage=req.stage,
        user_level=req.user_level
    )
    return res


@app.post("/api/teacher/check-move")
def teacher_check_move(req: TeacherCheckMoveRequest):
    """
    Teacher move validation:
    Case 1: Direct rule violation (Row/Col/Box duplicate)
    Case 2: Legal but contradicts unique solution
    Case 3: Correct move with 'Why does this work?' explanation
    """
    return check_move(board_state, req.cell, req.value)


@app.post("/api/teacher/why-it-works")
def teacher_why_it_works(req: WhyItWorksRequest):
    """Return structured explanation for why a move works."""
    return generate_why_it_works(board_state, req.cell, req.value)


@app.get("/api/teacher/puzzles")
def get_graded_puzzles(level: str = Query("beginner", pattern="^(beginner|intermediate|advanced)$")):
    """Return verified graded puzzles from the puzzle bank."""
    puzzles = get_puzzles_by_tier(level)
    return {"level": level, "puzzles": puzzles}


@app.post("/api/teacher/load-banked-puzzle")
def load_banked_puzzle(req: LoadBankedPuzzleRequest):
    """Load a specific graded puzzle from the puzzle bank."""
    puzzle_data = get_puzzle_by_id(req.puzzle_id)
    if not puzzle_data:
        raise HTTPException(status_code=404, detail="Puzzle not found in bank.")

    board_state.load_puzzle(puzzle_data["puzzle"])
    session = get_session(req.session_id)
    session.reset_session()

    return {
        "success": True,
        "puzzle_id": req.puzzle_id,
        "difficulty": puzzle_data.get("difficulty"),
        "title": puzzle_data.get("title"),
        "board": board_state.to_dict(),
        "analysis": analyze_board(board_state)
    }


@app.post("/api/teacher/generate-puzzle")
def generate_puzzle_endpoint(req: GeneratePuzzleRequest):
    """
    Generate a brand-new puzzle graded to the learner's level and load it.
    Every generated puzzle has a unique solution reachable without guessing; if an exact
    tier match isn't found in time, the closest harder-available puzzle is returned with
    meets_level=False.
    """
    try:
        record = get_fresh_puzzle(req.level)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"Could not generate a puzzle: {e}")

    board_state.load_puzzle(record["puzzle"])
    session = get_session(req.session_id)
    session.reset_session()

    meta = {k: v for k, v in record.items() if k != "solution"}
    return {
        "success": True,
        "puzzle_meta": meta,
        "puzzle_id": record["puzzle_id"],
        "title": record["title"],
        "difficulty": record["difficulty"],
        "board": board_state.to_dict(),
        "analysis": analyze_board(board_state)
    }


@app.get("/api/teacher/ai-status")
def ai_teacher_status():
    """Report whether the AI Teacher has an LLM connected or is running on the CSP engine alone."""
    return teacher_status()


@app.post("/api/teacher/chat")
def ai_teacher_chat(req: TeacherChatRequest):
    """
    Neuro-symbolic AI Teacher: the CSP engine grounds and verifies, an LLM (if configured) explains.
    Falls back to the engine's own explanation when no LLM is available or its reply fails verification.
    """
    selected = req.selected_cell if req.selected_cell in SQUARES else None
    return teacher_chat(board_state, req.message, req.history, selected, req.user_level)


@app.on_event("startup")
def warm_generator_pool():
    """Keep a few pre-generated puzzles per level ready in the background."""
    start_background_pool()


# --------------------------------------------------------------------------
# Static File Mount
# --------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    """Serve the single static HTML page."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {"message": "Sudoku AI Coach API active. Static index.html not found yet."}
