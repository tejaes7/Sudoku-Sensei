"""
Singles deduction techniques:
1. Naked Single: A cell has only one legal number remaining because its peers eliminate all other 8 digits.
2. Hidden Single: A digit appears as a legal candidate in only one cell within a row, column, or box.
"""

from typing import List, Dict, Optional, Tuple, Set
from src.board import SQUARES, UNITS, UNIT_LIST, SQUARE_TO_COORD, PEERS, ROWS, COLS
from .utils import get_unit_description, format_unit_friendly, compute_live_candidates


def find_naked_single(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds a cell with exactly 1 candidate remaining.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    for sq in SQUARES:
        r, c = SQUARE_TO_COORD[sq]
        if grid[r][c] == 0 and len(candidates[sq]) == 1:
            digit = next(iter(candidates[sq]))

            # Find peer cells that eliminate the other 8 digits
            ruling_peers = []
            eliminated_digits = set(range(1, 10)) - {digit}
            for p in PEERS[sq]:
                pr, pc = SQUARE_TO_COORD[p]
                pval = grid[pr][pc]
                if pval in eliminated_digits:
                    ruling_peers.append(p)

            # Get units for friendly description
            box_unit = UNITS[sq][2]
            friendly_box = format_unit_friendly(box_unit)

            return {
                "technique_id": "naked_single",
                "technique_name": "Naked Single",
                "difficulty_tier": "beginner",
                "definition": "A cell has only one possible number remaining because its row, column, and box already contain the other 8 numbers.",
                "unit_type": "cell",
                "unit_name": f"Cell {sq}",
                "target_cells": [sq],
                "target_value": digit,
                "cause_cells": ruling_peers,
                "eliminations": {},
                "nudge_text": f"Focus on cell {sq} and look at its immediate neighbors in {friendly_box}.",
                "technique_text": f"Cell {sq} can only take one number. Its neighbors rule out almost everything.",
                "walkthrough_steps": [
                    f"Look at cell {sq} and observe all numbers in its row, column, and box.",
                    f"Notice that its neighbors already contain all digits from 1 to 9, except {digit}.",
                    f"Therefore, cell {sq} must be {digit}."
                ]
            }

    return None


def find_hidden_single(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds a unit where a digit can only go in one cell.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    for unit in UNIT_LIST:
        unit_type, unit_label = get_unit_description(unit)
        friendly_unit = format_unit_friendly(unit)

        for digit in range(1, 10):
            # Check if digit is already placed in this unit
            already_placed = any(grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == digit for sq in unit)
            if already_placed:
                continue

            # Which empty cells in this unit can take this digit?
            possible_cells = [
                sq for sq in unit
                if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0 and digit in candidates[sq]
            ]

            if len(possible_cells) == 1:
                target_cell = possible_cells[0]

                # Find the peers that eliminate this digit from the other empty cells in the unit
                other_empty = [
                    sq for sq in unit
                    if sq != target_cell and grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0
                ]
                blocking_peers = []
                for o_sq in other_empty:
                    for p in PEERS[o_sq]:
                        if p not in unit and grid[SQUARE_TO_COORD[p][0]][SQUARE_TO_COORD[p][1]] == digit:
                            blocking_peers.append(p)

                return {
                    "technique_id": "hidden_single",
                    "technique_name": "Hidden Single",
                    "difficulty_tier": "beginner",
                    "definition": "Within a row, column, or box, a digit can only legally fit into one specific cell.",
                    "unit_type": unit_type,
                    "unit_name": unit_label,
                    "target_cells": [target_cell],
                    "target_value": digit,
                    "cause_cells": blocking_peers + [sq for sq in unit if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] != 0],
                    "eliminations": {},
                    "nudge_text": f"Scan for where the number {digit} can fit in {friendly_unit}.",
                    "technique_text": f"In {friendly_unit}, the number {digit} is forced into a single cell. Look at where other {digit}s block cells.",
                    "walkthrough_steps": [
                        f"Look at {friendly_unit} and search for where number {digit} can go.",
                        f"Notice that other {digit}s in intersecting rows/columns eliminate all other empty spaces in this unit.",
                        f"Therefore, cell {target_cell} is the only spot left for {digit}."
                    ]
                }

    return None
