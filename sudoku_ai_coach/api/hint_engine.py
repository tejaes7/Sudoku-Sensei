"""
Hint Engine Module - Milestones 1, 2, 3.
Identifies the next logical deduction from the live board state (Naked Single -> Hidden Single -> MRV Fail-First)
and produces a ReasoningStep for the Explanation Engine.
"""

import sys
import os
from typing import Dict, Any, Optional, List, Tuple

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, PEERS, UNITS, UNIT_LIST, SQUARE_TO_COORD, ROWS, COLS
from .board_state import BoardState
from .reasoning_trace import ReasoningStep, get_unit_description
from .analyze import compute_domains
from .explanation_engine import explain_step


def find_next_reasoning_step(board_state: BoardState) -> Optional[ReasoningStep]:
    """
    Scan the current board state and extract the most informative next deduction:
    Priority:
      1. Contradiction detection (if board is already in invalid state)
      2. Naked Singles (|Domain| == 1 among unassigned cells)
      3. Hidden Singles (digit appears exactly once across an unassigned unit)
      4. MRV Variable Focus (unassigned cell with minimum domain size, e.g. 2 candidates)
    """
    grid = board_state.board.grid
    domains_set, has_contradiction = compute_domains(grid)

    # 1. Contradiction Check
    if has_contradiction:
        for s in SQUARES:
            r, c = SQUARE_TO_COORD[s]
            if grid[r][c] == 0 and len(domains_set[s]) == 0:
                return ReasoningStep(
                    step_type="contradiction",
                    cell=s,
                    candidates_before="",
                    candidates_after="",
                    value=None,
                    related_cells=list(PEERS[s])[:4],
                    reason="No legal candidate digits remain for this square.",
                    certainty="deduced",
                    contradiction=True
                )

    # 2. Naked Singles Check
    unassigned_cells = [s for s in SQUARES if board_state.get_cell_value(s) == 0]
    if not unassigned_cells:
        return None  # Puzzle already solved

    for s in unassigned_cells:
        if len(domains_set[s]) == 1:
            val = str(next(iter(domains_set[s])))
            peers_with_info = [p for p in PEERS[s] if board_state.get_cell_value(p) != 0]
            return ReasoningStep(
                step_type="naked_single",
                cell=s,
                candidates_before=val,
                candidates_after=val,
                value=val,
                related_cells=peers_with_info[:4],
                reason=f"Cell {s} has only one remaining legal value: {val} (Naked Single).",
                certainty="deduced",
                contradiction=False
            )

    # 3. Hidden Singles Check across all 27 units
    for u in UNIT_LIST:
        for digit in range(1, 10):
            d_str = str(digit)
            # Find which cells in this unit could hold this digit
            matching_cells = [
                s for s in u
                if board_state.get_cell_value(s) == 0 and digit in domains_set[s]
            ]
            if len(matching_cells) == 1:
                target = matching_cells[0]
                unit_type, unit_name = get_unit_description(u)
                cands_before = "".join(str(d) for d in sorted(domains_set[target]))
                return ReasoningStep(
                    step_type="hidden_single",
                    cell=target,
                    candidates_before=cands_before,
                    candidates_after=d_str,
                    value=d_str,
                    related_cells=[s for s in u if s != target],
                    reason=f"Digit {d_str} can only appear in cell {target} within its {unit_name} (Hidden Single).",
                    certainty="deduced",
                    contradiction=False
                )

    # 4. MRV Cell Focus (Fail-First Heuristic)
    # Pick unassigned cell with minimum remaining candidates
    min_size = min(len(domains_set[s]) for s in unassigned_cells)
    mrv_candidates = [s for s in unassigned_cells if len(domains_set[s]) == min_size]

    # Degree heuristic tiebreak
    def unassigned_peers(sq: str) -> int:
        return sum(1 for p in PEERS[sq] if board_state.get_cell_value(p) == 0)

    best_cell = max(mrv_candidates, key=unassigned_peers)
    cands_str = "".join(str(d) for d in sorted(domains_set[best_cell]))

    return ReasoningStep(
        step_type="mrv_focus",
        cell=best_cell,
        candidates_before=cands_str,
        candidates_after=cands_str,
        value=cands_str[0] if cands_str else None,
        related_cells=list(PEERS[best_cell])[:4],
        reason=f"Cell {best_cell} is the most constrained variable with only {min_size} choices: {{{', '.join(cands_str)}}}.",
        certainty="deduced",
        contradiction=False
    )
