"""
Utility helpers for the human technique deduction layer.
"""

from typing import List, Tuple, Dict, Set
from src.board import ROWS, COLS, SQUARE_TO_COORD, SQUARES, PEERS, UNITS


def get_unit_description(unit: List[str]) -> Tuple[str, str]:
    """
    Given a unit of 9 squares, return its type ('row', 'column', 'box') and human label.
    """
    # Row: all have same first char
    if all(s[0] == unit[0][0] for s in unit):
        row_letter = unit[0][0]
        row_num = ROWS.index(row_letter) + 1
        return "row", f"Row {row_letter}"
    # Column: all have same second char
    if all(s[1] == unit[0][1] for s in unit):
        col_char = unit[0][1]
        return "column", f"Column {col_char}"
    # Box
    first = unit[0]
    box_r = ROWS.index(first[0]) // 3
    box_c = (int(first[1]) - 1) // 3
    box_num = box_r * 3 + box_c + 1
    return "box", f"Box {box_num}"


def format_unit_friendly(unit: List[str]) -> str:
    """Return friendly name like 'Row D' or 'Box 5 (the center 3x3 block)'."""
    utype, ulabel = get_unit_description(unit)
    if utype == "row":
        return f"{ulabel}"
    if utype == "column":
        return f"{ulabel}"
    if utype == "box":
        num = int(ulabel.split()[1])
        positions = {
            1: "top-left", 2: "top-middle", 3: "top-right",
            4: "middle-left", 5: "center", 6: "middle-right",
            7: "bottom-left", 8: "bottom-middle", 9: "bottom-right"
        }
        pos = positions.get(num, "")
        return f"{ulabel} ({pos} 3x3 block)"
    return ulabel


def get_cell_friendly_name(cell: str) -> str:
    """Return friendly name for a cell, e.g. 'D5'."""
    return cell


def compute_live_candidates(grid: List[List[int]]) -> Dict[str, Set[int]]:
    """
    Computes candidate sets for all cells directly from current grid digits.
    Filled cells get an empty set.
    """
    candidates: Dict[str, Set[int]] = {}
    for s in SQUARES:
        r, c = SQUARE_TO_COORD[s]
        val = grid[r][c]
        if val != 0:
            candidates[s] = set()
        else:
            used_peers = set()
            for p in PEERS[s]:
                pr, pc = SQUARE_TO_COORD[p]
                pval = grid[pr][pc]
                if pval != 0:
                    used_peers.add(pval)
            candidates[s] = set(range(1, 10)) - used_peers
    return candidates
