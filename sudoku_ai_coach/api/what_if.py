"""
What-If Simulation Engine - Milestone 3.
Allows players to test hypothetical moves and inspect the resulting deductive cascade
without mutating the real board state.
"""

import sys
import os
from typing import Dict, Any, List, Optional

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, PEERS, SQUARE_TO_COORD
from .board_state import BoardState
from .reasoning_trace import ReasoningStep, assign_trace, build_propagated_state
from .analyze import compute_domains
from .move_checker import check_move


def simulate_move(board_state: BoardState, cell: str, value: int) -> Dict[str, Any]:
    """
    Simulate placing value into cell on a clone of the current board.
    Runs constraint propagation, collects all cascade steps, and reports conclusion.
    Guarantees the actual board_state is NEVER mutated.
    """
    # 1. First check immediate violation using move_checker
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

    # 2. Build Norvig candidate map from current board state
    grid = [row[:] for row in board_state.board.grid]
    values, _ = build_propagated_state(grid, record_initial_clues=False)

    if values is None:
        return {
            "success": False,
            "contradiction": True,
            "cell": cell,
            "value": value,
            "cascade_steps": [],
            "conclusion": "Board is already in an impossible contradiction state.",
            "board_mutated": False
        }

    # 3. Speculatively assign on the copy and capture trace
    cascade_trace: List[ReasoningStep] = []
    # Mark certainty as 'deduced' if forced or 'guessed' if tentative what-if
    ok = assign_trace(values, cell, str(value), cascade_trace, certainty="guessed")

    serialized_steps = [step.to_dict() for step in cascade_trace]

    # 4. Synthesize conclusion
    if not ok or any(s.contradiction for s in cascade_trace):
        # Identify contradiction step
        contra_step = next((s for s in reversed(cascade_trace) if s.contradiction), None)
        culprit = contra_step.cell if contra_step else cell
        reason = contra_step.reason if contra_step else "Eliminated all candidate options."

        conclusion = (
            f"{value} cannot be safely assigned to {cell} — "
            f"it creates a downstream contradiction at {culprit} ({reason})."
        )
        return {
            "success": False,
            "contradiction": True,
            "cell": cell,
            "value": value,
            "cascade_count": len(cascade_trace),
            "cascade_steps": serialized_steps,
            "conclusion": conclusion,
            "culprit_cell": culprit,
            "board_mutated": False
        }

    # 5. Successful speculative branch without contradiction
    singletons_produced = sum(1 for s in cascade_trace if s.step_type in ("naked_single", "hidden_single"))
    conclusion = (
        f"Tentatively assigning {cell} = {value} is consistent. "
        f"It triggers {len(cascade_trace)} deduction steps ({singletons_produced} singletons forced) "
        f"with zero contradictions."
    )

    return {
        "success": True,
        "contradiction": False,
        "cell": cell,
        "value": value,
        "cascade_count": len(cascade_trace),
        "cascade_steps": serialized_steps,
        "conclusion": conclusion,
        "board_mutated": False
    }
