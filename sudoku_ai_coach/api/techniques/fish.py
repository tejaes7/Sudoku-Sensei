"""
Fish deduction techniques:
1. X-Wing:
   A candidate digit appears in exactly two cells in two different rows, and those cells share the same two columns.
   Therefore, that candidate can be eliminated from all other cells in those two columns.
   (And vice versa, swapping rows and columns).
"""

from typing import List, Dict, Optional, Tuple, Set
from itertools import combinations
from src.board import SQUARES, UNITS, UNIT_LIST, SQUARE_TO_COORD, ROWS, COLS
from .utils import compute_live_candidates


def find_x_wing(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds an X-Wing pattern in rows (eliminating from columns) or in columns (eliminating from rows).
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    # 1. Row-based X-Wing
    for digit in range(1, 10):
        row_candidates: Dict[str, List[str]] = {}
        for r_char in ROWS:
            row_cells = [f"{r_char}{c_char}" for c_char in COLS]
            matches = [
                sq for sq in row_cells
                if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0 and digit in candidates[sq]
            ]
            if len(matches) == 2:
                # Store columns
                cols_str = tuple(sorted(sq[1] for sq in matches))
                row_candidates[r_char] = (matches, cols_str)

        # Check all pairs of rows
        for r1, r2 in combinations(row_candidates.keys(), 2):
            cells1, cols1 = row_candidates[r1]
            cells2, cols2 = row_candidates[r2]
            if cols1 == cols2:
                # Found row X-Wing on columns cols1[0] and cols1[1]
                c1, c2 = cols1
                eliminations: Dict[str, List[int]] = {}
                for check_r in ROWS:
                    if check_r != r1 and check_r != r2:
                        for check_c in (c1, c2):
                            sq = f"{check_r}{check_c}"
                            if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0:
                                if digit in candidates[sq]:
                                    eliminations[sq] = [digit]

                if eliminations:
                    cause_cells = cells1 + cells2
                    return {
                        "technique_id": "x_wing",
                        "technique_name": "X-Wing",
                        "difficulty_tier": "advanced",
                        "definition": "When a digit appears in only two cells in two rows, and those cells share the same two columns, the digit cannot appear anywhere else in those columns.",
                        "unit_type": "fish",
                        "unit_name": f"Rows {r1} and {r2}",
                        "target_cells": list(eliminations.keys()),
                        "target_value": None,
                        "cause_cells": cause_cells,
                        "eliminations": eliminations,
                        "nudge_text": f"Look at how candidate {digit} appears across Rows {r1} and {r2}.",
                        "technique_text": f"Candidate {digit} forms an X-Wing in Rows {r1} & {r2} along Columns {c1} & {c2}.",
                        "walkthrough_steps": [
                            f"Observe Rows {r1} and {r2}.",
                            f"Notice that in both rows, number {digit} can only go in Columns {c1} and {c2}.",
                            f"Because {digit} must occupy opposite corners of this rectangle, it is ruled out from all other cells in Columns {c1} and {c2}."
                        ]
                    }

    # 2. Column-based X-Wing
    for digit in range(1, 10):
        col_candidates: Dict[str, Tuple[List[str], Tuple[str, ...]]] = {}
        for c_char in COLS:
            col_cells = [f"{r_char}{c_char}" for r_char in ROWS]
            matches = [
                sq for sq in col_cells
                if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0 and digit in candidates[sq]
            ]
            if len(matches) == 2:
                rows_str = tuple(sorted(sq[0] for sq in matches))
                col_candidates[c_char] = (matches, rows_str)

        for c1, c2 in combinations(col_candidates.keys(), 2):
            cells1, rows1 = col_candidates[c1]
            cells2, rows2 = col_candidates[c2]
            if rows1 == rows2:
                r1, r2 = rows1
                eliminations = {}
                for check_c in COLS:
                    if check_c != c1 and check_c != c2:
                        for check_r in (r1, r2):
                            sq = f"{check_r}{check_c}"
                            if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0:
                                if digit in candidates[sq]:
                                    eliminations[sq] = [digit]

                if eliminations:
                    cause_cells = cells1 + cells2
                    return {
                        "technique_id": "x_wing",
                        "technique_name": "X-Wing",
                        "difficulty_tier": "advanced",
                        "definition": "When a digit appears in only two cells in two columns, and those cells share the same two rows, the digit cannot appear anywhere else in those rows.",
                        "unit_type": "fish",
                        "unit_name": f"Columns {c1} and {c2}",
                        "target_cells": list(eliminations.keys()),
                        "target_value": None,
                        "cause_cells": cause_cells,
                        "eliminations": eliminations,
                        "nudge_text": f"Look at how candidate {digit} appears across Columns {c1} and {c2}.",
                        "technique_text": f"Candidate {digit} forms an X-Wing in Columns {c1} & {c2} along Rows {r1} & {r2}.",
                        "walkthrough_steps": [
                            f"Observe Columns {c1} and {c2}.",
                            f"Notice that in both columns, number {digit} can only go in Rows {r1} and {r2}.",
                            f"Because {digit} must occupy opposite corners of this rectangle, it is ruled out from all other cells in Rows {r1} and {r2}."
                        ]
                    }

    return None
