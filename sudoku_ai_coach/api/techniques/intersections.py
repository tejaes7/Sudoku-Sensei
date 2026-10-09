"""
Intersection deduction techniques:
1. Pointing Pair / Triple (Box-to-Line Reduction):
   In a 3x3 box, all occurrences of a candidate digit lie along a single row or column.
   Therefore, that digit can be eliminated from the rest of that row or column outside the box.
2. Box/Line Reduction (Line-to-Box Reduction):
   In a row or column, all occurrences of a candidate digit lie within a single 3x3 box.
   Therefore, that digit can be eliminated from the rest of that box outside the line.
"""

from typing import List, Dict, Optional, Tuple, Set
from src.board import SQUARES, UNITS, UNIT_LIST, SQUARE_TO_COORD, ROWS, COLS
from .utils import get_unit_description, format_unit_friendly, compute_live_candidates


def find_pointing_pair(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds a Pointing Pair or Triple inside a 3x3 box that prunes a row or column.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    boxes = [u for u in UNIT_LIST if len(set(s[0] for s in u)) == 3 and len(set(s[1] for s in u)) == 3]

    for box in boxes:
        friendly_box = format_unit_friendly(box)
        empty_in_box = [sq for sq in box if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0]

        for digit in range(1, 10):
            matches = [sq for sq in empty_in_box if digit in candidates[sq]]
            if 2 <= len(matches) <= 3:
                # Check if all matches share same row
                same_row = all(sq[0] == matches[0][0] for sq in matches)
                if same_row:
                    row_char = matches[0][0]
                    # Row unit
                    row_unit = [s for s in SQUARES if s[0] == row_char]
                    # Cells in row outside box that have digit
                    eliminations: Dict[str, List[int]] = {}
                    for r_sq in row_unit:
                        if r_sq not in box and grid[SQUARE_TO_COORD[r_sq][0]][SQUARE_TO_COORD[r_sq][1]] == 0:
                            if digit in candidates[r_sq]:
                                eliminations[r_sq] = [digit]

                    if eliminations:
                        row_name = f"Row {row_char}"
                        return {
                            "technique_id": "pointing_pair",
                            "technique_name": "Pointing Pair",
                            "difficulty_tier": "intermediate",
                            "definition": "When a candidate in a box is confined to a single row or column, it cannot appear anywhere else in that row or column.",
                            "unit_type": "box",
                            "unit_name": friendly_box,
                            "target_cells": list(eliminations.keys()),
                            "target_value": None,
                            "cause_cells": matches,
                            "eliminations": eliminations,
                            "nudge_text": f"Look at how number {digit} is aligned within {friendly_box}.",
                            "technique_text": f"In {friendly_box}, all possible locations for number {digit} lie along {row_name}. They point down the row.",
                            "walkthrough_steps": [
                                f"Look at {friendly_box}.",
                                f"Notice that all spots where {digit} can go lie strictly on {row_name}.",
                                f"Because {digit} must be in one of those spots in this box, it cannot appear anywhere else in {row_name}."
                            ]
                        }

                # Check if all matches share same col
                same_col = all(sq[1] == matches[0][1] for sq in matches)
                if same_col:
                    col_char = matches[0][1]
                    col_unit = [s for s in SQUARES if s[1] == col_char]
                    eliminations = {}
                    for c_sq in col_unit:
                        if c_sq not in box and grid[SQUARE_TO_COORD[c_sq][0]][SQUARE_TO_COORD[c_sq][1]] == 0:
                            if digit in candidates[c_sq]:
                                eliminations[c_sq] = [digit]

                    if eliminations:
                        col_name = f"Column {col_char}"
                        return {
                            "technique_id": "pointing_pair",
                            "technique_name": "Pointing Pair",
                            "difficulty_tier": "intermediate",
                            "definition": "When a candidate in a box is confined to a single column, it cannot appear anywhere else in that column.",
                            "unit_type": "box",
                            "unit_name": friendly_box,
                            "target_cells": list(eliminations.keys()),
                            "target_value": None,
                            "cause_cells": matches,
                            "eliminations": eliminations,
                            "nudge_text": f"Look at how number {digit} is aligned within {friendly_box}.",
                            "technique_text": f"In {friendly_box}, all possible locations for number {digit} lie along {col_name}. They point along the column.",
                            "walkthrough_steps": [
                                f"Look at {friendly_box}.",
                                f"Notice that all spots where {digit} can go lie strictly on {col_name}.",
                                f"Because {digit} must be in one of those spots in this box, it cannot appear anywhere else in {col_name}."
                            ]
                        }

    return None


def find_box_line_reduction(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds Box/Line Reduction (Line-to-Box Reduction):
    In a row or column, all candidates for a digit lie within a single box.
    Prunes that digit from the rest of that box.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    # Check rows and columns
    lines = [u for u in UNIT_LIST if len(set(s[0] for s in u)) == 1 or len(set(s[1] for s in u)) == 1]

    for line in lines:
        unit_type, unit_label = get_unit_description(line)
        empty_in_line = [sq for sq in line if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0]

        for digit in range(1, 10):
            matches = [sq for sq in empty_in_line if digit in candidates[sq]]
            if 2 <= len(matches) <= 3:
                # Find the box for the first match
                first_box = UNITS[matches[0]][2]
                # Check if all matches are in the same box
                if all(sq in first_box for sq in matches):
                    friendly_box = format_unit_friendly(first_box)
                    # Cells in box outside line that have digit
                    eliminations: Dict[str, List[int]] = {}
                    for b_sq in first_box:
                        if b_sq not in line and grid[SQUARE_TO_COORD[b_sq][0]][SQUARE_TO_COORD[b_sq][1]] == 0:
                            if digit in candidates[b_sq]:
                                eliminations[b_sq] = [digit]

                    if eliminations:
                        return {
                            "technique_id": "box_line_reduction",
                            "technique_name": "Box/Line Reduction",
                            "difficulty_tier": "intermediate",
                            "definition": "When a candidate in a row or column is confined to a single box, it cannot appear anywhere else in that box.",
                            "unit_type": unit_type,
                            "unit_name": unit_label,
                            "target_cells": list(eliminations.keys()),
                            "target_value": None,
                            "cause_cells": matches,
                            "eliminations": eliminations,
                            "nudge_text": f"Look at where number {digit} can fit in {unit_label}.",
                            "technique_text": f"In {unit_label}, all options for {digit} lie within {friendly_box}. This reduces the box candidates.",
                            "walkthrough_steps": [
                                f"Look at {unit_label}.",
                                f"Notice that all possible places for {digit} fall inside {friendly_box}.",
                                f"Therefore, {digit} cannot appear anywhere else in {friendly_box}."
                            ]
                        }

    return None
