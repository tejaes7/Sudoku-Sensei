"""
What-If Simulation Engine - Milestone 3.
Allows players to test hypothetical moves and inspect the resulting deductive cascade
without mutating the real board state.

The cascade starts from the board exactly as the player sees it, places the hypothetical digit, then applies
only Naked and Hidden Singles one step at a time (following cause and effect) until a cell or a unit becomes
impossible, or nothing more is forced. If singles alone can't expose a wrong digit, the full CSP search
(forward checking + MRV) proves it instead.
"""

import sys
import os
from typing import Dict, Any, List, Optional

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, PEERS, UNIT_LIST, SQUARE_TO_COORD
from src.csp_solver import CSPSolver
from .board_state import BoardState
from .move_checker import check_move
from .techniques.utils import compute_live_candidates, format_unit_friendly

MAX_CASCADE_STEPS = 40


def _value(grid: List[List[int]], sq: str) -> int:
    r, c = SQUARE_TO_COORD[sq]
    return grid[r][c]


def singles_cascade(grid: List[List[int]], cell: str, value: int,
                    max_steps: int = MAX_CASCADE_STEPS) -> Dict[str, Any]:
    """
    Suppose cell = value on a copy of grid, then apply Naked / Hidden Singles until a contradiction or a stall.
    Returns {"steps": [...], "contradiction": bool, "culprit_cell": str|None, "culprit_unit": str|None}.
    """
    g = [row[:] for row in grid]
    r, c = SQUARE_TO_COORD[cell]
    g[r][c] = value
    steps: List[Dict[str, Any]] = []

    def stop(reason: str, culprit_cell: Optional[str] = None, culprit_unit: Optional[str] = None) -> Dict[str, Any]:
        steps.append({"step_type": "contradiction", "cell": culprit_cell, "value": None, "reason": reason,
                      "explanation": reason, "contradiction": True})
        return {"steps": steps, "contradiction": True, "culprit_cell": culprit_cell, "culprit_unit": culprit_unit}

    for _ in range(max_steps):
        cands = compute_live_candidates(g)
        empty = [s for s in SQUARES if not _value(g, s)]

        for s in empty:
            if not cands[s]:
                return stop(f"{s} has no legal digit left: its row, column and box already contain all of 1-9.", s)
        for unit in UNIT_LIST:
            placed = {_value(g, s) for s in unit}
            for d in range(1, 10):
                if d not in placed and not any(d in cands[s] for s in unit if not _value(g, s)):
                    name = format_unit_friendly(unit)
                    return stop(f"{name} still needs a {d}, but no empty square in it can take {d}.", None, name)

        # Follow cause and effect: prefer squares that see something placed in this cascade
        touched = {cell} | {st["cell"] for st in steps}
        near = set().union(*(PEERS[t] for t in touched))
        step = None
        for s in sorted((s for s in empty if len(cands[s]) == 1), key=lambda s: s not in near):
            v = next(iter(cands[s]))
            step = {"step_type": "naked_single", "cell": s, "value": v,
                    "reason": f"{s} has only one candidate left",
                    "explanation": f"{s} would have to be {v}: it is its only remaining candidate (Naked Single).",
                    "contradiction": False}
            break
        if not step:
            for unit in sorted(UNIT_LIST, key=lambda u: not touched.intersection(u)):
                for d in range(1, 10):
                    spots = [s for s in unit if not _value(g, s) and d in cands[s]]
                    if len(spots) == 1:
                        name = format_unit_friendly(unit)
                        step = {"step_type": "hidden_single", "cell": spots[0], "value": d,
                                "reason": f"{spots[0]} is the only place for {d} in {name}",
                                "explanation": f"{spots[0]} would have to be {d}: it is the only place for {d} in "
                                               f"{name} (Hidden Single).",
                                "contradiction": False}
                        break
                if step:
                    break
        if not step:
            break
        sr, sc = SQUARE_TO_COORD[step["cell"]]
        g[sr][sc] = step["value"]
        steps.append(step)

    return {"steps": steps, "contradiction": False, "culprit_cell": None, "culprit_unit": None}


def search_proof(grid: List[List[int]], cell: str, value: int) -> Dict[str, Any]:
    """Fix cell = value and let the full CSP search (forward checking + MRV) try to finish the puzzle.
    No solution means every branch ends in a contradiction: a proof that the digit is wrong."""
    g = [row[:] for row in grid]
    r, c = SQUARE_TO_COORD[cell]
    g[r][c] = value
    tel = CSPSolver(propagation="fc", use_mrv=True, timeout_sec=3.0).solve(g)
    if tel.solved:
        return {"proved_impossible": False, "solvable": True}
    if tel.error_message == "Timeout exceeded":
        return {"proved_impossible": False, "solvable": None}
    return {
        "proved_impossible": True,
        "solvable": False,
        "branches_explored": tel.nodes_expanded,
        "explanation": (f"Simple singles don't expose the contradiction, so the CSP solver searched with "
                        f"{cell} = {value} fixed: it explored {tel.nodes_expanded} branches (backtracking with "
                        f"forward checking and MRV, max depth {tel.max_depth}) and every branch ended with some "
                        f"cell having no legal digit. So the puzzle has no solution with {value} in {cell}."),
    }


def simulate_move(board_state: BoardState, cell: str, value: int) -> Dict[str, Any]:
    """
    Simulate placing value into cell on a copy of the current board and report the cascade of forced moves.
    Guarantees the actual board_state is NEVER mutated.
    """
    # 1. Immediate rule violation
    pre_check = check_move(board_state, cell, value)
    if pre_check["status"] == "immediate_violation":
        return {
            "success": False,
            "contradiction": True,
            "cell": cell,
            "value": value,
            "cascade_steps": [],
            "conclusion": f"{value} cannot be assigned to {cell} — {pre_check['message']}",
            "culprit_cell": pre_check.get("conflict_cell"),
            "board_mutated": False
        }

    grid = [row[:] for row in board_state.board.grid]

    # 2. Follow the forced singles from the hypothetical move
    cascade = singles_cascade(grid, cell, value)
    steps = cascade["steps"]
    forced = sum(1 for s in steps if not s["contradiction"])

    if cascade["contradiction"]:
        where = cascade["culprit_cell"] or cascade["culprit_unit"]
        return {
            "success": False,
            "contradiction": True,
            "cell": cell,
            "value": value,
            "cascade_count": len(steps),
            "cascade_steps": steps,
            "conclusion": (f"If {cell} were {value}, "
                           + (f"{forced} forced move{'s follow' if forced > 1 else ' follows'}, and then " if forced
                              else "then immediately ")
                           + f"{where} becomes impossible. So {value} cannot go in {cell}."),
            "culprit_cell": cascade["culprit_cell"],
            "board_mutated": False
        }

    # 3. Singles didn't break it: ask the full CSP search
    proof = search_proof(grid, cell, value)
    if proof["proved_impossible"]:
        return {
            "success": False,
            "contradiction": True,
            "cell": cell,
            "value": value,
            "cascade_count": len(steps),
            "cascade_steps": steps,
            "conclusion": proof["explanation"],
            "culprit_cell": None,
            "search_proof": proof,
            "board_mutated": False
        }

    conclusion = (f"{value} in {cell} is consistent: it forces {forced} more move{'s' if forced != 1 else ''} "
                  f"with no contradiction")
    conclusion += ", and the CSP solver can finish the puzzle from there." if proof.get("solvable") else "."
    return {
        "success": True,
        "contradiction": False,
        "cell": cell,
        "value": value,
        "cascade_count": len(steps),
        "cascade_steps": steps,
        "conclusion": conclusion,
        "board_mutated": False
    }
