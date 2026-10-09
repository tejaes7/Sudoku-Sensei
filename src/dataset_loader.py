"""
Dataset Loader Module - Phase 1.
Supports loading and parsing Kaggle-style CSV datasets as well as synthetic benchmarks.
Preserves and assigns difficulty ratings: easy, medium, hard, extreme.
"""

import os
import csv
from typing import List, Dict, Any, Optional, Tuple


class DatasetLoader:
    """
    Loads, normalizes, and filters Sudoku puzzle datasets from CSV files.

    Supported CSV Schemas:
      1. Kaggle standard (e.g., 'quizzes', 'solutions')
      2. Generic ('puzzle', 'solution', optional 'difficulty')
      3. Synthetic benchmark ('id', 'puzzle', 'solution', 'difficulty', 'clue_count', 'is_synthetic')
    """

    @staticmethod
    def infer_difficulty_from_clues(clue_count: int) -> str:
        """
        Heuristic difficulty estimator based on the number of given clues:
          - Easy: 36 or more clues
          - Medium: 30 to 35 clues
          - Hard: 25 to 29 clues
          - Extreme: 24 or fewer clues (minimum theoretical standard is 17)
        """
        if clue_count >= 36:
            return "easy"
        elif clue_count >= 30:
            return "medium"
        elif clue_count >= 25:
            return "hard"
        else:
            return "extreme"

    @classmethod
    def load_csv(
        cls,
        filepath: str,
        max_puzzles: Optional[int] = None,
        filter_difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load puzzles from a CSV file.

        Args:
            filepath: Path to the CSV file.
            max_puzzles: Optional upper limit on the number of puzzles to load.
            filter_difficulty: Optional filter ('easy', 'medium', 'hard', 'extreme').

        Returns:
            List of normalized puzzle dictionaries:
            [{'puzzle_id': str, 'puzzle': str, 'solution': str, 'difficulty': str,
              'clue_count': int, 'is_synthetic': bool}]
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Dataset file not found: {filepath}")

        puzzles = []

        with open(filepath, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            fieldnames = [col.strip().lower() for col in (reader.fieldnames or [])]

            # Detect puzzle column
            puzzle_col = None
            for candidate in ["quizzes", "puzzle", "puzzles", "sudoku", "problem", "quiz"]:
                if candidate in fieldnames:
                    puzzle_col = [col for col in reader.fieldnames if col.strip().lower() == candidate][0]
                    break

            # Detect solution column
            sol_col = None
            for candidate in ["solutions", "solution", "sol"]:
                if candidate in fieldnames:
                    sol_col = [col for col in reader.fieldnames if col.strip().lower() == candidate][0]
                    break

            # Detect difficulty column
            diff_col = None
            for candidate in ["difficulty", "level", "rating", "diff"]:
                if candidate in fieldnames:
                    diff_col = [col for col in reader.fieldnames if col.strip().lower() == candidate][0]
                    break

            # Detect ID column
            id_col = None
            for candidate in ["id", "puzzle_id", "index"]:
                if candidate in fieldnames:
                    id_col = [col for col in reader.fieldnames if col.strip().lower() == candidate][0]
                    break

            # Detect synthetic tag
            synth_col = None
            for candidate in ["is_synthetic", "synthetic"]:
                if candidate in fieldnames:
                    synth_col = [col for col in reader.fieldnames if col.strip().lower() == candidate][0]
                    break

            if puzzle_col is None:
                raise ValueError(
                    f"Could not identify a puzzle column in CSV header: {reader.fieldnames}. "
                    f"Expected one of: 'quizzes', 'puzzle', 'sudoku', etc."
                )

            for idx, row in enumerate(reader):
                raw_puzzle = row[puzzle_col].strip()
                # Clean characters to digits/dots
                clean_puzzle = "".join(ch if ch in "123456789" else "0" for ch in raw_puzzle)
                if len(clean_puzzle) != 81:
                    continue  # Skip malformed lines

                clue_count = sum(1 for ch in clean_puzzle if ch != "0")

                # Determine difficulty
                if diff_col and row[diff_col].strip():
                    raw_diff = row[diff_col].strip().lower()
                    # Map standard terms
                    if "easy" in raw_diff:
                        diff = "easy"
                    elif "med" in raw_diff:
                        diff = "medium"
                    elif "ext" in raw_diff or "evil" in raw_diff or "master" in raw_diff:
                        diff = "extreme"
                    elif "hard" in raw_diff:
                        diff = "hard"
                    else:
                        diff = cls.infer_difficulty_from_clues(clue_count)
                else:
                    diff = cls.infer_difficulty_from_clues(clue_count)

                # Filter if requested
                if filter_difficulty and diff != filter_difficulty.lower():
                    continue

                puzzle_id = row[id_col].strip() if id_col else str(idx + 1)
                sol = row[sol_col].strip() if sol_col else None
                is_synthetic = (
                    row[synth_col].strip().lower() in ("true", "1", "yes")
                    if synth_col
                    else ("synthetic" in filepath.lower())
                )

                puzzles.append({
                    "puzzle_id": puzzle_id,
                    "puzzle": clean_puzzle,
                    "solution": sol,
                    "difficulty": diff,
                    "clue_count": clue_count,
                    "is_synthetic": is_synthetic,
                })

                if max_puzzles is not None and len(puzzles) >= max_puzzles:
                    break

        return puzzles
