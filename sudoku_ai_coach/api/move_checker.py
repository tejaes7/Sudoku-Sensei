"""
Move Checker Module:
Evaluates tentative player moves with calm, encouraging teacher feedback:
  Case 1: Direct rule violation (conflict in row, column, or box).
  Case 2: Legal but contradicts the unique puzzle solution (leads to a dead end).
  Case 3: Correct move with structured "Why does this work?" explanation.
"""

import sys
import os
from typing import Dict, Any, Optional, List

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, PEERS, UNITS, SQUARE_TO_COORD, ROWS, COLS, parse_grid
from src.csp_solver import CSPSolver
from .board_state import BoardState
from .analyze import compute_domains
from .techniques.utils import get_unit_description, format_unit_friendly, compute_live_candidates


def check_move(
    board_state: BoardState,
    cell: str,
    value: int,
    unique_solution: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if placing value in cell is valid, breaks a rule, or diverges from solution.
    """
    if cell not in SQUARES:
        return {
            "status": "error",
            "valid": False,
            "message": f"Invalid cell coordinate '{cell}'."
        }

    if board_state.is_clue(cell):
        return {
            "status": "locked_clue",
            "valid": False,
            "message": f"Cell {cell} is a starting clue and cannot be modified."
        }

    if value not in range(1, 10):
        return {
            "status": "invalid_value",
            "valid": False,
            "message": f"Invalid value {value}. Sudoku digits must be 1 through 9."
        }

    grid = board_state.board.grid

    # --------------------------------------------------------------------------
    # CASE 1: Immediate Rule Violation (Duplicate in row, col, or box) -> Case A
    # --------------------------------------------------------------------------
    for peer in PEERS[cell]:
        peer_r, peer_c = SQUARE_TO_COORD[peer]
        peer_val = grid[peer_r][peer_c]
        if peer_val == value:
            shared_units = [u for u in UNITS[cell] if peer in u]
            unit_name = format_unit_friendly(shared_units[0]) if shared_units else "the same group"

            return {
                "case": "A",
                "status": "immediate_violation",
                "valid": False,
                "cell": cell,
                "value": value,
                "conflict_cell": peer,
                "conflict_unit": unit_name,
                "title": "Rule Conflict",
                "message": f"Immediate conflict: {cell} cannot be {value} because peer {peer} in {unit_name} already contains {value}."
            }

    # --------------------------------------------------------------------------
    # CASE 2 & 3: Compare against Unique Solution (Backtracking ground truth)
    # --------------------------------------------------------------------------
    if not unique_solution:
        solver = CSPSolver(propagation="norvig", timeout_sec=2.0)
        tel = solver.solve(board_state.initial_puzzle)
        if tel.solved:
            unique_solution = tel.solution

    if unique_solution:
        sol_grid = parse_grid(unique_solution)
        r, c = SQUARE_TO_COORD[cell]
        correct_val = sol_grid[r][c]

        if value != correct_val:
            # Legal now, but wrong path
            return {
                "case": "B",
                "status": "wrong_path",
                "valid": False,
                "cell": cell,
                "value": value,
                "title": "A Gentle Dead End",
                "message": f"Placing {value} in {cell} doesn't clash immediately, but it leads to a contradiction later. Take your time — would you like a hint instead?"
            }

    # --------------------------------------------------------------------------
    # CASE 3: Correct Move — Case C
    # --------------------------------------------------------------------------
    why_explanation = generate_why_it_works(board_state, cell, value)

    return {
        "case": "C",
        "status": "valid",
        "valid": True,
        "cell": cell,
        "value": value,
        "title": "Spot on!",
        "message": f"Great move! {cell} is indeed {value}.",
        "why_it_works": why_explanation
    }


def generate_why_it_works(board_state: BoardState, cell: str, value: int) -> Dict[str, Any]:
    """
    Explains, from the current board, why `value` belongs in `cell`:
      - Naked Single: every other digit is already seen by the cell's row, column, or box.
      - Hidden Single: in some row/column/box, `value` has no other legal square.
      - Otherwise the move is correct but not yet forced by a single rule — say so honestly.
    """
    grid = board_state.board.grid
    candidates = compute_live_candidates(grid)
    cell_cands = candidates.get(cell, set())

    def digits_in(unit: List[str]) -> List[int]:
        out = []
        for sq in unit:
            if sq == cell:
                continue
            r, c = SQUARE_TO_COORD[sq]
            if grid[r][c]:
                out.append(grid[r][c])
        return sorted(set(out))

    row_unit, col_unit, box_unit = UNITS[cell][0], UNITS[cell][1], UNITS[cell][2]
    labels = [(format_unit_friendly(u), u) for u in (row_unit, col_unit, box_unit)]

    # 1. Naked Single
    if cell_cands == {value}:
        steps = [f"Look at everything {cell} can see:"]
        for label, unit in labels:
            ds = digits_in(unit)
            if ds:
                steps.append(f"{label} already contains {', '.join(map(str, ds))}.")
        steps.append(f"That rules out every digit except {value}, so {cell} must be {value}. This is a Naked Single.")
        cause = [p for p in PEERS[cell] if grid[SQUARE_TO_COORD[p][0]][SQUARE_TO_COORD[p][1]] != 0]
        return {"cell": cell, "value": value, "technique": "Naked Single", "forced": True,
                "steps": steps, "cause_cells": cause[:12]}

    # 2. Hidden Single (value has nowhere else to go in some unit)
    for label, unit in labels:
        others = [sq for sq in unit if sq != cell and value in candidates.get(sq, set())]
        if value in cell_cands and not others:
            blocked = []
            blockers = []
            for sq in unit:
                if sq == cell:
                    continue
                r, c = SQUARE_TO_COORD[sq]
                if grid[r][c]:
                    continue
                blocker = next((p for p in PEERS[sq] if grid[SQUARE_TO_COORD[p][0]][SQUARE_TO_COORD[p][1]] == value), None)
                if blocker:
                    blocked.append(f"{sq} (sees the {value} in {blocker})")
                    if blocker not in blockers:
                        blockers.append(blocker)
            steps = [f"Ask: where can {value} go in {label}?"]
            if blocked:
                steps.append(f"The other empty squares are blocked: {'; '.join(blocked[:5])}{'…' if len(blocked) > 5 else ''}.")
            steps.append(f"{cell} is the only square left for {value} in {label} — a Hidden Single.")
            return {"cell": cell, "value": value, "technique": "Hidden Single", "forced": True,
                    "steps": steps, "cause_cells": blockers}

    # 3. Correct, but not forced by a single rule yet
    others = sorted(d for d in cell_cands if d != value)
    steps = [
        f"{value} is the right number for {cell} — it matches the puzzle's unique solution.",
        f"But it isn't forced by a simple rule yet: right now {cell} could still be {', '.join(map(str, sorted(cell_cands)))}.",
        "Proving it takes a deeper deduction (such as a pair or pointing elimination). Try pencil-marking the candidates — or ask for a hint to see the logical route."
    ]
    if not others:
        steps = [f"{value} is the right number for {cell}."]
    return {"cell": cell, "value": value, "technique": None, "forced": False,
            "steps": steps, "cause_cells": []}
