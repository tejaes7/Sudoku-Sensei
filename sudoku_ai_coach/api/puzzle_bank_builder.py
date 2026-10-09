"""
Puzzle Bank Builder:
Generates, verifies, and stores graded puzzles in data/puzzle_bank.json.
Guarantees:
  1. Every puzzle has a unique verified solution.
  2. Beginner puzzles solve purely with Full House, Naked Single, and Hidden Single.
  3. Intermediate puzzles genuinely require intermediate techniques (Naked Pair, Hidden Pair, Pointing, Box-Line).
  4. Advanced puzzles feature advanced techniques (Triples, X-Wing) or harder multi-step deductions.
  5. Every banked puzzle is verified 100% solvable with deterministic human techniques (no guessing).
"""

import os
import json
import random
from typing import Dict, Any, List
from generate_dataset import generate_valid_solution, remove_clues
from src.board import grid_to_string
from src.validator import SudokuValidator
from src.csp_solver import CSPSolver
from .techniques.technique_engine import TechniqueEngine


BANK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "puzzle_bank.json"))


def build_puzzle_bank(output_path: str = BANK_PATH) -> Dict[str, List[Dict[str, Any]]]:
    bank: Dict[str, List[Dict[str, Any]]] = {
        "beginner": [],
        "intermediate": [],
        "advanced": []
    }

    # --------------------------------------------------------------------------
    # 1. BEGINNER PUZZLES (Fully solvable with Full House & Singles)
    # --------------------------------------------------------------------------
    # Foundational classic easy
    p_beg_1 = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
    sb, steps_b, fin_b, hard_b = TechniqueEngine.solve_puzzle_with_techniques(p_beg_1, max_tier="beginner")
    if sb:
        bank["beginner"].append({
            "puzzle_id": "beg_1",
            "title": "Gentle Warmup",
            "difficulty": "beginner",
            "clue_count": sum(1 for c in p_beg_1 if c not in "0."),
            "puzzle": p_beg_1,
            "solution": fin_b,
            "hardest_technique": hard_b,
            "techniques_used": list(set(s.technique_id for s in steps_b)),
            "description": "A classic intro grid that yields smoothly to Full House and singles."
        })

    # Generate more beginner puzzles
    for _ in range(50):
        if len(bank["beginner"]) >= 6:
            break
        sol = generate_valid_solution()
        puz = remove_clues(sol, target_clues=38)
        p_str = grid_to_string(puz)
        solved, steps, fin, hard = TechniqueEngine.solve_puzzle_with_techniques(p_str, max_tier="beginner")
        if solved:
            num = len(bank["beginner"]) + 1
            bank["beginner"].append({
                "puzzle_id": f"beg_{num}",
                "title": f"Beginner Puzzle #{num}",
                "difficulty": "beginner",
                "clue_count": sum(1 for ch in p_str if ch != "0"),
                "puzzle": p_str,
                "solution": fin,
                "hardest_technique": hard,
                "techniques_used": list(set(s.technique_id for s in steps)),
                "description": "Focus on row scanning and finding full house cells."
            })

    # --------------------------------------------------------------------------
    # 2. INTERMEDIATE PUZZLES (Requires Pairs / Intersections)
    # --------------------------------------------------------------------------
    inter_attempts = 0
    while len(bank["intermediate"]) < 6 and inter_attempts < 100:
        inter_attempts += 1
        sol = generate_valid_solution()
        grid = [row[:] for row in sol]
        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)
        for r, c in cells:
            val = grid[r][c]
            grid[r][c] = 0
            p_str = grid_to_string(grid)
            solved, steps, fin, hard = TechniqueEngine.solve_puzzle_with_techniques(p_str, max_tier="intermediate")
            if not solved:
                grid[r][c] = val

        p_str = grid_to_string(grid)
        beg_sol, _, _, _ = TechniqueEngine.solve_puzzle_with_techniques(p_str, max_tier="beginner")
        int_sol, steps, fin, hard = TechniqueEngine.solve_puzzle_with_techniques(p_str, max_tier="intermediate")
        if not beg_sol and int_sol:
            techs = list(set(s.technique_id for s in steps))
            num = len(bank["intermediate"]) + 1
            bank["intermediate"].append({
                "puzzle_id": f"inter_{num}",
                "title": f"Intermediate Challenge #{num}",
                "difficulty": "intermediate",
                "clue_count": sum(1 for ch in p_str if ch != "0"),
                "puzzle": p_str,
                "solution": fin,
                "hardest_technique": hard,
                "techniques_used": techs,
                "description": f"Requires {hard.replace('_', ' ').title()} to unlock the grid without guessing."
            })

    # --------------------------------------------------------------------------
    # 3. ADVANCED PUZZLES (Requires Advanced Deductions)
    # --------------------------------------------------------------------------
    # Generated puzzles that genuinely require Naked Triple / X-Wing and solve with zero guessing
    from .puzzle_generator import generate_puzzle
    seed = 100
    while len(bank["advanced"]) < 5 and seed < 400:
        rec = generate_puzzle("advanced", seed=seed, time_budget=60)
        seed += 1
        if not rec["meets_level"]:
            continue
        num = len(bank["advanced"]) + 1
        bank["advanced"].append({
            "puzzle_id": f"adv_{num}",
            "title": f"Mastery Grid #{num}",
            "difficulty": "advanced",
            "clue_count": rec["clue_count"],
            "puzzle": rec["puzzle"],
            "solution": rec["solution"],
            "hardest_technique": rec["hardest_technique"],
            "techniques_used": rec["techniques_used"],
            "description": f"Needs {rec['hardest_technique_label']} to finish without guessing."
        })

    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2)

    return bank


if __name__ == "__main__":
    b = build_puzzle_bank()
    print(f"Bank generated: Beginner={len(b['beginner'])}, Intermediate={len(b['intermediate'])}, Advanced={len(b['advanced'])}")
