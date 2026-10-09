"""
Subsets deduction techniques:
1. Naked Pair: Two cells in a unit share the exact same two candidates {X, Y}.
   Therefore, X and Y can be eliminated from all other cells in that unit.
2. Hidden Pair: Two digits X and Y appear in only two cells in a unit.
   Therefore, all other candidates in those two cells can be eliminated.
3. Naked Triple: Three cells in a unit share candidates drawn from only three digits {X, Y, Z}.
"""

from typing import List, Dict, Optional, Tuple, Set
from itertools import combinations
from src.board import SQUARES, UNITS, UNIT_LIST, SQUARE_TO_COORD
from .utils import get_unit_description, format_unit_friendly, compute_live_candidates


def find_naked_pair(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds a Naked Pair in any unit that eliminates candidates from other cells.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    for unit in UNIT_LIST:
        empty_cells = [sq for sq in unit if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0]
        # Look for pairs of cells with exactly 2 candidates that match
        pair_candidates = [sq for sq in empty_cells if len(candidates[sq]) == 2]

        for sq1, sq2 in combinations(pair_candidates, 2):
            if candidates[sq1] == candidates[sq2]:
                pair_vals = candidates[sq1]
                # Check if this pair eliminates anything from other cells in this unit
                eliminations: Dict[str, List[int]] = {}
                for other_sq in empty_cells:
                    if other_sq != sq1 and other_sq != sq2:
                        to_remove = [v for v in pair_vals if v in candidates[other_sq]]
                        if to_remove:
                            eliminations[other_sq] = sorted(to_remove)

                if eliminations:
                    unit_type, unit_label = get_unit_description(unit)
                    friendly_unit = format_unit_friendly(unit)
                    vals_str = " and ".join(str(v) for v in sorted(pair_vals))

                    return {
                        "technique_id": "naked_pair",
                        "technique_name": "Naked Pair",
                        "difficulty_tier": "intermediate",
                        "definition": "When two cells in the same unit can only contain the same two numbers, those numbers cannot appear anywhere else in that unit.",
                        "unit_type": unit_type,
                        "unit_name": unit_label,
                        "target_cells": list(eliminations.keys()),
                        "target_value": None,
                        "cause_cells": [sq1, sq2],
                        "eliminations": eliminations,
                        "nudge_text": f"Look closely at the candidates across {friendly_unit}. Two squares are locked together.",
                        "technique_text": f"Cells {sq1} and {sq2} form a Naked Pair with candidates {vals_str}. They lock those numbers in {friendly_unit}.",
                        "walkthrough_steps": [
                            f"Look at {friendly_unit}.",
                            f"Notice that cells {sq1} and {sq2} can only contain the numbers {vals_str}.",
                            f"Because {vals_str} must go into these two cells, we can eliminate them from all other cells in {friendly_unit}."
                        ]
                    }

    return None


def find_hidden_pair(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds a Hidden Pair in any unit that eliminates other candidates.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    for unit in UNIT_LIST:
        empty_cells = [sq for sq in unit if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0]
        # Map each digit to the cells that can hold it
        digit_to_cells: Dict[int, List[str]] = {}
        for d in range(1, 10):
            matches = [sq for sq in empty_cells if d in candidates[sq]]
            if len(matches) == 2:
                digit_to_cells[d] = matches

        # Check if two digits have the exact same 2 cells
        for d1, d2 in combinations(digit_to_cells.keys(), 2):
            if digit_to_cells[d1] == digit_to_cells[d2]:
                sq1, sq2 = digit_to_cells[d1]
                # Check if there are other candidates in sq1 or sq2 to eliminate
                extra_sq1 = candidates[sq1] - {d1, d2}
                extra_sq2 = candidates[sq2] - {d1, d2}

                eliminations: Dict[str, List[int]] = {}
                if extra_sq1:
                    eliminations[sq1] = sorted(list(extra_sq1))
                if extra_sq2:
                    eliminations[sq2] = sorted(list(extra_sq2))

                if eliminations:
                    unit_type, unit_label = get_unit_description(unit)
                    friendly_unit = format_unit_friendly(unit)

                    return {
                        "technique_id": "hidden_pair",
                        "technique_name": "Hidden Pair",
                        "difficulty_tier": "intermediate",
                        "definition": "When two digits only fit into the same two cells within a unit, all other candidate numbers can be eliminated from those two cells.",
                        "unit_type": unit_type,
                        "unit_name": unit_label,
                        "target_cells": [sq1, sq2],
                        "target_value": None,
                        "cause_cells": [sq1, sq2],
                        "eliminations": eliminations,
                        "nudge_text": f"In {friendly_unit}, examine which cells can hold numbers {d1} and {d2}.",
                        "technique_text": f"Numbers {d1} and {d2} only appear in cells {sq1} and {sq2} within {friendly_unit}. They form a Hidden Pair.",
                        "walkthrough_steps": [
                            f"Look at {friendly_unit}.",
                            f"Notice that digits {d1} and {d2} can only fit in cells {sq1} and {sq2}.",
                            f"Therefore, no other numbers can go in these two cells — we can eliminate all other candidates from them."
                        ]
                    }

    return None


def find_naked_triple(grid: List[List[int]], candidates: Optional[Dict[str, Set[int]]] = None) -> Optional[Dict]:
    """
    Finds a Naked Triple in any unit that eliminates candidates from other cells.
    """
    if candidates is None:
        candidates = compute_live_candidates(grid)

    for unit in UNIT_LIST:
        empty_cells = [sq for sq in unit if grid[SQUARE_TO_COORD[sq][0]][SQUARE_TO_COORD[sq][1]] == 0]
        # Subset candidates with 2 or 3 candidates
        triple_pool = [sq for sq in empty_cells if 2 <= len(candidates[sq]) <= 3]

        for trio in combinations(triple_pool, 3):
            union_vals = set().union(*(candidates[sq] for sq in trio))
            if len(union_vals) == 3:
                # Check eliminations
                eliminations: Dict[str, List[int]] = {}
                for other_sq in empty_cells:
                    if other_sq not in trio:
                        to_remove = [v for v in union_vals if v in candidates[other_sq]]
                        if to_remove:
                            eliminations[other_sq] = sorted(to_remove)

                if eliminations:
                    unit_type, unit_label = get_unit_description(unit)
                    friendly_unit = format_unit_friendly(unit)
                    vals_str = ", ".join(str(v) for v in sorted(union_vals))

                    return {
                        "technique_id": "naked_triple",
                        "technique_name": "Naked Triple",
                        "difficulty_tier": "advanced",
                        "definition": "Three cells in a unit share candidates drawn from only three numbers, locking those numbers away from the rest of the unit.",
                        "unit_type": unit_type,
                        "unit_name": unit_label,
                        "target_cells": list(eliminations.keys()),
                        "target_value": None,
                        "cause_cells": list(trio),
                        "eliminations": eliminations,
                        "nudge_text": f"Examine three constrained squares in {friendly_unit}.",
                        "technique_text": f"Cells {', '.join(trio)} form a Naked Triple for {{{vals_str}}} in {friendly_unit}.",
                        "walkthrough_steps": [
                            f"Look at {friendly_unit}.",
                            f"Notice cells {', '.join(trio)} can only take digits from {{{vals_str}}}.",
                            f"Since these 3 digits are locked into these 3 cells, we eliminate them from the rest of {friendly_unit}."
                        ]
                    }

    return None
