"""
Reasoning Trace Module - Milestone 1.
Implements the ReasoningStep dataclass and trace-instrumented Norvig constraint propagation rules.
Zero modifications to src/ - reuses SQUARES, UNITS, PEERS, UNIT_LIST from src.board.
"""

import sys
import os
from dataclasses import dataclass, asdict
from typing import Literal, Optional, List, Dict, Tuple, Set

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, PEERS, UNITS, UNIT_LIST, SQUARE_TO_COORD, ROWS, COLS


@dataclass
class ReasoningStep:
    step_type: str                # "naked_single" | "hidden_single" | "elimination" | "contradiction" | "mrv_focus"
    cell: str                     # Norvig square, e.g. "D7"
    candidates_before: str
    candidates_after: str
    value: Optional[str]
    related_cells: List[str]      # peers/unit members that caused this step
    reason: str                   # short machine-readable reason
    certainty: Literal["deduced", "guessed"]   # Exact logic vs speculative branch
    contradiction: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_unit_description(unit: List[str]) -> Tuple[str, str]:
    """
    Given a unit of 9 squares, return its type ('row', 'column', 'box') and human label.
    """
    # Row: all have same first char
    if all(s[0] == unit[0][0] for s in unit):
        row_letter = unit[0][0]
        row_num = ROWS.index(row_letter) + 1
        return "row", f"Row {row_letter} (Row {row_num})"
    # Column: all have same second char
    if all(s[1] == unit[0][1] for s in unit):
        col_char = unit[0][1]
        return "column", f"Column {col_char}"
    # Box
    first = unit[0]
    box_r = ROWS.index(first[0]) // 3
    box_c = (int(first[1]) - 1) // 3
    box_num = box_r * 3 + box_c + 1
    return "box", f"Box {box_num} (3x3 block)"


def eliminate_trace(
    vals: Dict[str, str],
    s: str,
    d: str,
    trace: List[ReasoningStep],
    certainty: Literal["deduced", "guessed"] = "deduced",
) -> bool:
    """
    Eliminate digit d from vals[s]; record each logical step into trace.
    Propagates Rule 1 (naked singles) and Rule 2 (hidden singles).
    Returns False upon contradiction, True otherwise.
    """
    if d not in vals[s]:
        return True  # Already eliminated

    before = vals[s]
    vals[s] = vals[s].replace(d, "")
    after = vals[s]

    if len(after) == 0:
        # Contradiction: eliminated last candidate
        trace.append(ReasoningStep(
            step_type="contradiction",
            cell=s,
            candidates_before=before,
            candidates_after="",
            value=d,
            related_cells=list(PEERS[s]),
            reason=f"Cell {s} has no remaining legal values after eliminating {d}.",
            certainty=certainty,
            contradiction=True
        ))
        return False

    elif len(after) == 1:
        # Rule 1: Cell is now a Naked Single
        single_val = after
        causing_peers = [p for p in PEERS[s] if vals[p] == single_val]
        trace.append(ReasoningStep(
            step_type="naked_single",
            cell=s,
            candidates_before=before,
            candidates_after=after,
            value=single_val,
            related_cells=causing_peers or list(PEERS[s])[:3],
            reason=f"Cell {s} has only one remaining candidate: {single_val}.",
            certainty=certainty,
            contradiction=False
        ))

        # Eliminate single_val from all peers of s
        for s2 in PEERS[s]:
            if not eliminate_trace(vals, s2, single_val, trace, certainty):
                return False

    # Rule 2: If a unit is reduced to only 1 place for d, assign it (Hidden Single)
    for u in UNITS[s]:
        dplaces = [s2 for s2 in u if d in vals[s2]]
        if len(dplaces) == 0:
            unit_type, unit_name = get_unit_description(u)
            trace.append(ReasoningStep(
                step_type="contradiction",
                cell=s,
                candidates_before=before,
                candidates_after=after,
                value=d,
                related_cells=[c for c in u if c != s],
                reason=f"Contradiction: {unit_name} has no remaining cell that can accept value {d}.",
                certainty=certainty,
                contradiction=True
            ))
            return False
        elif len(dplaces) == 1:
            target = dplaces[0]
            # If target has more than 1 candidate, assigning it is a new deduction!
            if len(vals[target]) > 1:
                unit_type, unit_name = get_unit_description(u)
                trace.append(ReasoningStep(
                    step_type="hidden_single",
                    cell=target,
                    candidates_before=vals[target],
                    candidates_after=d,
                    value=d,
                    related_cells=[c for c in u if c != target],
                    reason=f"{target} is the only remaining cell in {unit_name} that can accept value {d}.",
                    certainty=certainty,
                    contradiction=False
                ))
                if not assign_trace(vals, target, d, trace, certainty):
                    return False

    return True


def assign_trace(
    vals: Dict[str, str],
    s: str,
    d: str,
    trace: List[ReasoningStep],
    certainty: Literal["deduced", "guessed"] = "deduced",
) -> bool:
    """
    Eliminate all values other than d from vals[s]; propagate consequences.
    Returns False upon contradiction, True otherwise.
    """
    other_values = vals[s].replace(d, "")
    for d2 in other_values:
        if not eliminate_trace(vals, s, d2, trace, certainty):
            return False
    return True


def build_propagated_state(
    grid: List[List[int]],
    record_initial_clues: bool = False
) -> Tuple[Optional[Dict[str, str]], List[ReasoningStep]]:
    """
    Build initial Norvig candidate map from grid and run propagation.
    If record_initial_clues is False, only deductions triggered beyond the clues are in trace.
    """
    digits = "123456789"
    values = {s: digits for s in SQUARES}
    trace: List[ReasoningStep] = []

    # Assign clues
    for r in range(9):
        for c in range(9):
            val = grid[r][c]
            if val != 0:
                sq = ROWS[r] + COLS[c]
                target_trace = trace if record_initial_clues else []
                if not assign_trace(values, sq, str(val), target_trace, certainty="deduced"):
                    return None, trace

    return values, trace
