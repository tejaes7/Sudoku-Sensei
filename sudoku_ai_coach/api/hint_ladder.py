"""
Hint Ladder Module:
Provides progressive 3-stage hints (Nudge -> Technique -> Reveal) with full mistake detection.
Always prioritizes mistakes on the board before giving forward hints.
"""

from typing import Dict, Any, Optional, List, Tuple
from src.board import SQUARES, SQUARE_TO_COORD, PEERS, UNITS, parse_grid, grid_to_string
from src.csp_solver import CSPSolver
from .techniques.technique_engine import TechniqueEngine, TechniqueStep
from .techniques.utils import compute_live_candidates, format_unit_friendly, get_unit_description


def find_user_mistakes(grid: List[List[int]], initial_puzzle: str, unique_solution: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Checks if the user has made any mistakes:
    1. Immediate peer conflicts (e.g. duplicate in same row/col/box).
    2. Divergence from the true unique puzzle solution.
    """
    orig_grid = parse_grid(initial_puzzle)

    # 1. Immediate peer conflicts
    for sq in SQUARES:
        r, c = SQUARE_TO_COORD[sq]
        val = grid[r][c]
        if val != 0:
            for p in PEERS[sq]:
                pr, pc = SQUARE_TO_COORD[p]
                if grid[pr][pc] == val:
                    # Found duplicate!
                    is_user_move = (orig_grid[r][c] == 0)
                    culprit_cell = sq if is_user_move else p
                    other_cell = p if is_user_move else sq
                    shared_units = [u for u in UNITS[culprit_cell] if other_cell in u]
                    unit_name = format_unit_friendly(shared_units[0]) if shared_units else "the grid"

                    return {
                        "has_user_mistake": True,
                        "mistake_cell": culprit_cell,
                        "conflicting_cell": other_cell,
                        "value": val,
                        "mistake_type": "rule_violation",
                        "title": "Rule Conflict Detected",
                        "explanation": f"Cell {culprit_cell} contains {val}, but {other_cell} in {unit_name} already contains {val}. Sudoku allows each number only once per row, column, and box.",
                        "action_prompt": f"Clear or change cell {culprit_cell} to continue."
                    }

    # 2. Divergence from the unique solution (if available or computable)
    if not unique_solution:
        solver = CSPSolver(propagation="norvig", timeout_sec=2.0)
        tel = solver.solve(initial_puzzle)
        if tel.solved:
            unique_solution = tel.solution

    if unique_solution:
        sol_grid = parse_grid(unique_solution)
        for sq in SQUARES:
            r, c = SQUARE_TO_COORD[sq]
            val = grid[r][c]
            # Check user-filled cells against true solution
            if orig_grid[r][c] == 0 and val != 0 and val != sol_grid[r][c]:
                return {
                    "has_user_mistake": True,
                    "mistake_cell": sq,
                    "conflicting_cell": None,
                    "value": val,
                    "mistake_type": "contradiction",
                    "title": "Unsolvable Placement",
                    "explanation": f"The number {val} in cell {sq} doesn't violate any immediate neighbors yet, but it leads to a contradiction and prevents completing the puzzle.",
                    "action_prompt": f"Erasing cell {sq} will put you back on track."
                }

    return None


TIER_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3}


def build_deduction_chain(grid: List[List[int]], user_level: str = "intermediate", max_links: int = 40) -> List[TechniqueStep]:
    """
    Return the sequence of technique steps from the current board up to (and including) the
    first step that places a digit. Eliminations are carried forward in a candidate map.
    """
    candidates = compute_live_candidates(grid)
    chain: List[TechniqueStep] = []
    for _ in range(max_links):
        step = TechniqueEngine.get_next_step(grid, candidates, max_tier=user_level)
        if not step:
            step = TechniqueEngine.get_next_step(grid, candidates, max_tier="advanced")
        if not step:
            break
        chain.append(step)
        if step.target_value is not None and len(step.target_cells) == 1:
            break
        progressed = False
        for sq, vals in (step.eliminations or {}).items():
            for v in vals:
                if v in candidates[sq]:
                    candidates[sq].discard(v)
                    progressed = True
        if not progressed:
            break
    return chain


def generate_hint_ladder(
    grid: List[List[int]],
    initial_puzzle: str,
    stage: int = 1,
    user_level: str = "intermediate",
    unique_solution: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a 3-stage hint response:
      Stage 1: Nudge (where to look, no technique name, no answer)
      Stage 2: Technique (name, definition, key cells highlighted, no answer)
      Stage 3: Reveal (target cell, target value, full 3-step walkthrough)
    If a mistake is present on the board, immediately returns a Mistake Hint regardless of requested stage.
    """
    # 1. Mistake check
    mistake = find_user_mistakes(grid, initial_puzzle, unique_solution)
    if mistake:
        return {
            "stage": 0,
            "has_user_mistake": True,
            "mistake": mistake,
            "nudge": {
                "message": f"Notice an issue at cell {mistake['mistake_cell']}.",
                "highlight_cells": [mistake['mistake_cell']] + ([mistake['conflicting_cell']] if mistake.get('conflicting_cell') else [])
            },
            "technique_card": None,
            "reveal": None,
        }

    # 2. Check if puzzle is solved
    all_filled = all(grid[SQUARE_TO_COORD[s][0]][SQUARE_TO_COORD[s][1]] != 0 for s in SQUARES)
    if all_filled:
        return {
            "stage": 0,
            "has_user_mistake": False,
            "is_solved": True,
            "message": "The puzzle is already solved! Excellent job."
        }

    # 3. Compute the deterministic human deduction chain.
    # Elimination techniques (pairs, pointing, X-Wing) don't place a digit by themselves, and the
    # board alone can't remember them — so follow the chain forward, carrying eliminations, until
    # it unlocks a placement. The learner is taught the key technique and shown what it unlocks.
    chain = build_deduction_chain(grid, user_level)

    if not chain:
        return {
            "stage": 0,
            "has_user_mistake": False,
            "message": "All standard logical techniques exhausted. You might test a speculative move with 'What If?' mode."
        }

    key = max(chain, key=lambda st: TIER_RANK[st.difficulty_tier])
    final = chain[-1]
    places_digit = final.target_value is not None and len(final.target_cells) == 1
    unlock_note = ""
    if places_digit and final is not key:
        unlock_note = f" Once you apply it, {final.target_cells[0]} can be filled in."

    # Build response for requested stage (1, 2, or 3)
    response: Dict[str, Any] = {
        "stage": stage,
        "has_user_mistake": False,
        "technique_id": key.technique_id,
        "technique_name": key.technique_name,
        "difficulty_tier": key.difficulty_tier,
        "definition": key.definition,
        "unit_name": key.unit_name,
        "chain_length": len(chain),
    }

    # STAGE 1: NUDGE
    # Only points where to look. No technique name, no value.
    response["nudge"] = {
        "message": key.nudge_text,
        "highlight_cells": key.cause_cells[:6],
        "target_cells": key.target_cells,
    }

    # STAGE 2: TECHNIQUE
    # Names technique, gives definition, highlights key cells, but DOES NOT reveal value.
    if stage >= 2:
        response["technique_card"] = {
            "name": key.technique_name,
            "definition": key.definition,
            "message": key.technique_text + unlock_note,
            "highlight_cause_cells": key.cause_cells,
            "highlight_target_cells": key.target_cells,
        }

    # STAGE 3: REVEAL
    # Reveals the placement the chain unlocks (or the eliminations), with a step-by-step walkthrough.
    if stage >= 3:
        eliminations: Dict[str, List[int]] = {}
        cause_cells: List[str] = []
        walkthrough: List[str] = []
        multi = len(chain) > 1
        for i, st in enumerate(chain, start=1):
            for sq, vals in (st.eliminations or {}).items():
                eliminations.setdefault(sq, [])
                eliminations[sq] += [v for v in vals if v not in eliminations[sq]]
            for c in st.cause_cells:
                if c not in cause_cells:
                    cause_cells.append(c)
            prefix = f"[{st.technique_name}] " if multi else ""
            walkthrough += [prefix + w for w in st.walkthrough_steps]

        response["reveal"] = {
            "target_cells": final.target_cells if places_digit else key.target_cells,
            "target_value": final.target_value if places_digit else None,
            "eliminations": eliminations,
            "walkthrough_steps": walkthrough,
            "cause_cells": cause_cells,
            "chain": [
                {"technique_name": st.technique_name, "target_cells": st.target_cells,
                 "target_value": st.target_value, "eliminations": st.eliminations}
                for st in chain
            ],
        }

    return response
