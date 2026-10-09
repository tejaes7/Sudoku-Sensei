"""
Unit tests for Hint Ladder and Mistake Detection.
"""

import unittest
from src.board import parse_grid
from sudoku_ai_coach.api.hint_ladder import generate_hint_ladder, find_user_mistakes


class TestHintLadder(unittest.TestCase):

    def setUp(self):
        self.puzzle = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        self.grid = parse_grid(self.puzzle)

    def test_stage_1_nudge(self):
        res = generate_hint_ladder(self.grid, self.puzzle, stage=1)
        self.assertEqual(res["stage"], 1)
        self.assertFalse(res["has_user_mistake"])
        self.assertIn("nudge", res)
        # Stage 1 should NOT reveal the value or technique card
        self.assertIsNone(res.get("technique_card"))
        self.assertIsNone(res.get("reveal"))

    def test_stage_2_technique(self):
        res = generate_hint_ladder(self.grid, self.puzzle, stage=2)
        self.assertEqual(res["stage"], 2)
        self.assertIn("technique_card", res)
        self.assertIsNotNone(res["technique_card"]["name"])
        self.assertIsNotNone(res["technique_card"]["definition"])
        # Stage 2 should NOT reveal target value
        self.assertIsNone(res.get("reveal"))

    def test_stage_3_reveal(self):
        res = generate_hint_ladder(self.grid, self.puzzle, stage=3)
        self.assertEqual(res["stage"], 3)
        self.assertIn("reveal", res)
        self.assertIsNotNone(res["reveal"]["target_value"])
        self.assertGreater(len(res["reveal"]["walkthrough_steps"]), 0)

    def test_immediate_conflict_mistake_detection(self):
        # Introduce duplicate 3 in Row A
        bad_grid = [row[:] for row in self.grid]
        bad_grid[0][0] = 3  # Cell A1 = 3, while A3 is already 3!

        res = generate_hint_ladder(bad_grid, self.puzzle, stage=1)
        self.assertTrue(res["has_user_mistake"])
        self.assertIn("mistake", res)
        self.assertEqual(res["mistake"]["mistake_cell"], "A1")
        self.assertEqual(res["mistake"]["mistake_type"], "rule_violation")

    def test_solution_divergence_mistake_detection(self):
        # Introduce a legal-looking digit that contradicts the true solution
        bad_grid = [row[:] for row in self.grid]
        # In this puzzle, A1 is actually 4. Set it to 1 (which doesn't immediately clash with A row)
        bad_grid[0][0] = 1

        res = generate_hint_ladder(bad_grid, self.puzzle, stage=1)
        self.assertTrue(res["has_user_mistake"])
        self.assertEqual(res["mistake"]["mistake_cell"], "A1")


if __name__ == "__main__":
    unittest.main()
