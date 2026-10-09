"""
Full House deduction technique.
Identifies any row, column, or 3x3 box that has exactly 8 cells filled and only 1 empty cell.
The empty cell must contain the only missing digit.
"""

from typing import List, Dict, Optional, Tuple, Set
from src.board import SQUARES, UNITS, UNIT_LIST, SQUARE_TO_COORD, ROWS, COLS
from .utils import get_unit_description, format_unit_friendly


def find_full_house(grid: List[List[int]]) -> Optional[Dict]:
    """
    Scans all 27 units. If a unit has exactly one empty cell,
    returns a structured deduction.
    """
    for unit in UNIT_LIST:
        empty_cells = []
        filled_vals = set()
        filled_cells = []

        for sq in unit:
            r, c = SQUARE_TO_COORD[sq]
            val = grid[r][c]
            if val == 0:
                empty_cells.append(sq)
            else:
                filled_vals.add(val)
                filled_cells.append(sq)

        if len(empty_cells) == 1:
            target_cell = empty_cells[0]
            missing_vals = set(range(1, 10)) - filled_vals
            if len(missing_vals) == 1:
                digit = next(iter(missing_vals))
                unit_type, unit_label = get_unit_description(unit)
                friendly_unit = format_unit_friendly(unit)

                return {
                    "technique_id": "full_house",
                    "technique_name": "Full House",
                    "difficulty_tier": "beginner",
                    "definition": "When 8 of the 9 cells in a row, column, or box are filled, the last cell must be the missing number.",
                    "unit_type": unit_type,
                    "unit_name": unit_label,
                    "target_cells": [target_cell],
                    "target_value": digit,
                    "cause_cells": filled_cells,
                    "eliminations": {},
                    "nudge_text": f"Take a close look at {friendly_unit}. Almost every square is already filled in.",
                    "technique_text": f"In {friendly_unit}, 8 cells are already solved. This is a Full House — only one number is missing.",
                    "walkthrough_steps": [
                        f"Look at {friendly_unit}.",
                        f"Notice that 8 numbers (1 through 9) are already placed here: only {digit} has not been used yet.",
                        f"Therefore, cell {target_cell} must be {digit}."
                    ]
                }

    return None
