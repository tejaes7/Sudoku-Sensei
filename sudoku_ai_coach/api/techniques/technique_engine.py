"""
Technique Engine:
Orchestrates human-style deterministic deductions in ascending order of difficulty.
Provides full solving with zero backtracking to verify puzzle bank grading.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Set, Tuple
from copy import deepcopy

from src.board import SQUARES, SQUARE_TO_COORD, parse_grid, grid_to_string
from .utils import compute_live_candidates
from .full_house import find_full_house
from .singles import find_naked_single, find_hidden_single
from .subsets import find_naked_pair, find_hidden_pair, find_naked_triple
from .intersections import find_pointing_pair, find_box_line_reduction
from .fish import find_x_wing


@dataclass
class TechniqueStep:
    technique_id: str
    technique_name: str
    difficulty_tier: str  # "beginner" | "intermediate" | "advanced"
    definition: str
    unit_type: str
    unit_name: str
    target_cells: List[str]
    target_value: Optional[int]
    cause_cells: List[str]
    eliminations: Dict[str, List[int]]
    nudge_text: str
    technique_text: str
    walkthrough_steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Ranked list of technique detector functions
TECHNIQUE_DETECTORS = [
    ("full_house", find_full_house),
    ("naked_single", find_naked_single),
    ("hidden_single", find_hidden_single),
    ("naked_pair", find_naked_pair),
    ("hidden_pair", find_hidden_pair),
    ("pointing_pair", find_pointing_pair),
    ("box_line_reduction", find_box_line_reduction),
    ("naked_triple", find_naked_triple),
    ("x_wing", find_x_wing),
]

TIER_ORDER = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}

TECHNIQUE_TIERS = {
    "full_house": "beginner",
    "naked_single": "beginner",
    "hidden_single": "beginner",
    "naked_pair": "intermediate",
    "hidden_pair": "intermediate",
    "pointing_pair": "intermediate",
    "box_line_reduction": "intermediate",
    "naked_triple": "advanced",
    "x_wing": "advanced",
}


class TechniqueEngine:
    """
    Evaluates boards using the human technique hierarchy.
    """

    @staticmethod
    def get_next_step(
        grid: List[List[int]],
        candidates: Optional[Dict[str, Set[int]]] = None,
        max_tier: str = "advanced"
    ) -> Optional[TechniqueStep]:
        """
        Scans for the simplest available technique on the current grid.
        Respects max_tier ("beginner", "intermediate", "advanced").
        """
        if candidates is None:
            candidates = compute_live_candidates(grid)

        # Check if puzzle is already solved
        all_filled = all(grid[SQUARE_TO_COORD[s][0]][SQUARE_TO_COORD[s][1]] != 0 for s in SQUARES)
        if all_filled:
            return None

        max_tier_rank = TIER_ORDER.get(max_tier, 3)

        for tech_id, detector_fn in TECHNIQUE_DETECTORS:
            tech_tier = TECHNIQUE_TIERS[tech_id]
            if TIER_ORDER[tech_tier] > max_tier_rank:
                continue

            result = detector_fn(grid, candidates) if tech_id != "full_house" else detector_fn(grid)
            if result:
                return TechniqueStep(**result)

        return None

    @staticmethod
    def solve_puzzle_with_techniques(
        puzzle: str,
        max_tier: str = "advanced",
        max_steps: int = 150
    ) -> Tuple[bool, List[TechniqueStep], str, str]:
        """
        Solves puzzle exclusively using deterministic techniques.
        Returns: (is_solved, steps_applied, final_grid_str, hardest_technique_used).
        """
        grid = parse_grid(puzzle)
        candidates = compute_live_candidates(grid)
        steps: List[TechniqueStep] = []
        hardest_rank = 1
        hardest_name = "full_house"

        for _ in range(max_steps):
            # Check if grid is full
            empty_count = sum(1 for s in SQUARES if grid[SQUARE_TO_COORD[s][0]][SQUARE_TO_COORD[s][1]] == 0)
            if empty_count == 0:
                return True, steps, grid_to_string(grid), hardest_name

            step = TechniqueEngine.get_next_step(grid, candidates, max_tier=max_tier)
            if not step:
                # No technique at this tier can make progress without branching
                return False, steps, grid_to_string(grid), hardest_name

            steps.append(step)
            step_tier_rank = TIER_ORDER[step.difficulty_tier]
            if step_tier_rank > hardest_rank:
                hardest_rank = step_tier_rank
                hardest_name = step.technique_id

            # Apply step to grid or candidates
            if step.target_value is not None and len(step.target_cells) == 1:
                # Placing a digit
                sq = step.target_cells[0]
                val = step.target_value
                r, c = SQUARE_TO_COORD[sq]
                grid[r][c] = val
                candidates[sq] = set()
                # Recompute candidates directly
                candidates = compute_live_candidates(grid)
            elif step.eliminations:
                # Elimination technique
                for elim_sq, elim_vals in step.eliminations.items():
                    for ev in elim_vals:
                        candidates[elim_sq].discard(ev)

        empty_count = sum(1 for s in SQUARES if grid[SQUARE_TO_COORD[s][0]][SQUARE_TO_COORD[s][1]] == 0)
        return empty_count == 0, steps, grid_to_string(grid), hardest_name
