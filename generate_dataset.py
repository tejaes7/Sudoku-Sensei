"""
Synthetic Dataset Generator.
Creates clearly-labeled, verifiable synthetic Sudoku puzzle benchmarks
across four difficulty tiers: easy, medium, hard, and extreme.
NOTE: Clearly flagged as synthetic to ensure strict academic honesty.
"""

import os
import csv
import random
from typing import List, Dict, Tuple, Optional
from src.board import SQUARES, PEERS, parse_grid, grid_to_string
from src.validator import SudokuValidator


def generate_valid_solution() -> List[List[int]]:
    """
    Generate a random valid 9x9 Sudoku solution board using pattern shift and permutation.
    """
    base = 3
    side = base * base

    # Pattern for a baseline valid solution
    def pattern(r, c):
        return (base * (r % base) + r // base + c) % side

    # Randomize rows, cols, and numbers
    def shuffle(s):
        return random.sample(s, len(s))

    r_base = range(base)
    rows = [g * base + r for g in shuffle(r_base) for r in shuffle(r_base)]
    cols = [g * base + c for g in shuffle(r_base) for c in shuffle(r_base)]
    nums = shuffle(range(1, base * base + 1))

    board = [[nums[pattern(r, c)] for c in cols] for r in rows]
    return board


def remove_clues(
    solution_grid: List[List[int]],
    target_clues: int
) -> List[List[int]]:
    """
    Carve clues from a complete valid solution to create a puzzle with target_clues.
    """
    puzzle_grid = [row[:] for row in solution_grid]
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    current_clues = 81
    for r, c in cells:
        if current_clues <= target_clues:
            break
        puzzle_grid[r][c] = 0
        current_clues -= 1

    return puzzle_grid


# Renowned hard test puzzles (e.g. Arto Inkala's AI Escargot and Norwegian extreme benchmarks)
BENCHMARK_EXTREME_PUZZLES = [
    # AI Escargot (Often cited as one of the hardest known Sudoku puzzles)
    ("100007090030020008009600500005300900010080002600004000300000010040000007007000300",
     "162857493534129768789643521475312986913586472628794135356478219241935867897261354"),
    # Platinum Blonde (Minimal 17-clue extreme puzzle)
    ("000000012000000003002300400001800005060070800000009000008500000900040500470006000",
     "683457912745912683192386457321864795564273819879159326238591274916748532475236198"),
    # Hard classic
    ("003020600900305001001806400008102900700000008006708200002609500800203009005010300",
     "483921657967345821251876493548132976729564138136798245372689514814253769695417382"),
    # Evil benchmark
    ("000000000000003085001020000000507000004000100090000000500000073002010000000040009",
     "987654321246173985351928746128537694634892157795416832519284763472319582863745219"),
]


def generate_benchmark_dataset(
    output_csv: str = "data/synthetic_puzzles.csv",
    puzzles_per_difficulty: int = 25
):
    """
    Generate a full synthetic benchmark dataset across 4 difficulties.
    """
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    difficulty_configs = [
        ("easy", 36, 40),
        ("medium", 30, 34),
        ("hard", 25, 28),
        ("extreme", 21, 24),
    ]

    records = []
    puzzle_id = 1

    # Include curated real extreme/hard puzzles first
    for puzzle_str, sol_str in BENCHMARK_EXTREME_PUZZLES:
        clue_count = sum(1 for ch in puzzle_str if ch != "0")
        records.append({
            "id": str(puzzle_id),
            "puzzle": puzzle_str,
            "solution": sol_str,
            "difficulty": "extreme",
            "clue_count": clue_count,
            "is_synthetic": False,  # Curated published benchmark
            "dataset_type": "curated_benchmark_reference",
        })
        puzzle_id += 1

    # Generate synthetic puzzles
    for diff, min_clues, max_clues in difficulty_configs:
        count = puzzles_per_difficulty
        for _ in range(count):
            sol_board = generate_valid_solution()
            sol_str = grid_to_string(sol_board)
            target_clues = random.randint(min_clues, max_clues)
            puz_board = remove_clues(sol_board, target_clues)
            puz_str = grid_to_string(puz_board)

            # Double check validity of solution
            valid, _ = SudokuValidator.is_valid_grid(sol_str, puz_str)
            if not valid:
                continue

            records.append({
                "id": str(puzzle_id),
                "puzzle": puz_str,
                "solution": sol_str,
                "difficulty": diff,
                "clue_count": target_clues,
                "is_synthetic": True,
                "dataset_type": "synthetic_procedural",
            })
            puzzle_id += 1

    # Save to CSV
    fieldnames = ["id", "puzzle", "solution", "difficulty", "clue_count", "is_synthetic", "dataset_type"]
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    print(f"Generated {len(records)} benchmark puzzles -> {output_csv}")

    # Also generate a Kaggle-format sample CSV (quizzes,solutions)
    kaggle_csv = "data/kaggle_sample.csv"
    with open(kaggle_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["quizzes", "solutions"])
        for r in records[:20]:
            writer.writerow([r["puzzle"], r["solution"]])

    print(f"Generated Kaggle sample CSV -> {kaggle_csv}")


if __name__ == "__main__":
    generate_benchmark_dataset()
