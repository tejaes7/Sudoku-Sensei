"""
Unit tests to verify that every puzzle in data/puzzle_bank.json
is uniquely solvable with human techniques and zero guessing.
"""

import unittest
from src.validator import SudokuValidator
from sudoku_ai_coach.api.puzzle_bank import load_puzzle_bank
from sudoku_ai_coach.api.techniques.technique_engine import TechniqueEngine


class TestPuzzleBank(unittest.TestCase):

    def setUp(self):
        self.bank = load_puzzle_bank()

    def test_bank_has_all_tiers(self):
        self.assertIn("beginner", self.bank)
        self.assertIn("intermediate", self.bank)
        self.assertIn("advanced", self.bank)
        self.assertGreater(len(self.bank["beginner"]), 0)
        self.assertGreater(len(self.bank["intermediate"]), 0)
        self.assertGreater(len(self.bank["advanced"]), 0)

    def test_beginner_puzzles_solve_with_beginner_techniques(self):
        for pdata in self.bank["beginner"]:
            puzzle = pdata["puzzle"]
            solved, steps, final_str, hardest = TechniqueEngine.solve_puzzle_with_techniques(puzzle, max_tier="beginner")
            self.assertTrue(solved, f"Beginner puzzle {pdata['puzzle_id']} failed to solve with beginner techniques")
            is_valid, msg = SudokuValidator.is_valid_grid(final_str, puzzle)
            self.assertTrue(is_valid, f"Solution invalid for {pdata['puzzle_id']}: {msg}")

    def test_intermediate_puzzles_solve_with_intermediate_techniques(self):
        for pdata in self.bank["intermediate"]:
            puzzle = pdata["puzzle"]
            solved, steps, final_str, hardest = TechniqueEngine.solve_puzzle_with_techniques(puzzle, max_tier="intermediate")
            self.assertTrue(solved, f"Intermediate puzzle {pdata['puzzle_id']} failed to solve with intermediate techniques")
            is_valid, msg = SudokuValidator.is_valid_grid(final_str, puzzle)
            self.assertTrue(is_valid, f"Solution invalid for {pdata['puzzle_id']}: {msg}")


if __name__ == "__main__":
    unittest.main()
