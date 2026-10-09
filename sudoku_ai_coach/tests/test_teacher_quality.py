"""
Teaching-quality tests:
  - Following the hint ladder alone must solve every banked puzzle (no hint loops).
  - "Why does this work?" must name the real reason, or honestly say the move isn't forced yet.
  - The pencil-mark lesson must accept real candidates and explain rejected ones.
"""

import unittest

from src.board import parse_grid, SQUARE_TO_COORD
from sudoku_ai_coach.api.board_state import BoardState
from sudoku_ai_coach.api.hint_ladder import generate_hint_ladder
from sudoku_ai_coach.api.lesson_engine import LessonEngine
from sudoku_ai_coach.api.move_checker import generate_why_it_works
from sudoku_ai_coach.api.puzzle_bank import load_puzzle_bank

EASY = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"


class TestHintLadderSolvesBank(unittest.TestCase):

    def test_following_hints_solves_every_bank_puzzle(self):
        bank = load_puzzle_bank()
        for tier, puzzles in bank.items():
            for pdata in puzzles:
                grid = parse_grid(pdata["puzzle"])
                for _ in range(81):
                    hint = generate_hint_ladder(grid, pdata["puzzle"], stage=3, user_level=tier)
                    if hint.get("is_solved"):
                        break
                    reveal = hint.get("reveal")
                    self.assertTrue(reveal and reveal["target_value"],
                                    f"{pdata['puzzle_id']}: hint ladder stalled ({hint.get('message')})")
                    r, c = SQUARE_TO_COORD[reveal["target_cells"][0]]
                    self.assertEqual(int(pdata["solution"][r * 9 + c]), reveal["target_value"])
                    grid[r][c] = reveal["target_value"]
                self.assertTrue(hint.get("is_solved"), f"{pdata['puzzle_id']} was not solved by following hints")

    def test_elimination_hint_reveals_the_placement_it_unlocks(self):
        pdata = load_puzzle_bank()["intermediate"][0]
        grid = parse_grid(pdata["puzzle"])
        for _ in range(81):
            hint = generate_hint_ladder(grid, pdata["puzzle"], stage=3, user_level="intermediate")
            if hint["difficulty_tier"] == "intermediate":
                break
            r, c = SQUARE_TO_COORD[hint["reveal"]["target_cells"][0]]
            grid[r][c] = hint["reveal"]["target_value"]
        self.assertEqual(hint["difficulty_tier"], "intermediate")
        self.assertGreater(hint["chain_length"], 1)
        self.assertIsNotNone(hint["reveal"]["target_value"])
        self.assertTrue(hint["reveal"]["eliminations"])


class TestWhyItWorks(unittest.TestCase):

    def test_naked_single_explanation(self):
        why = generate_why_it_works(BoardState(EASY), "E6", 4)
        self.assertEqual(why["technique"], "Naked Single")
        self.assertTrue(why["forced"])

    def test_unforced_correct_move_is_honest(self):
        why = generate_why_it_works(BoardState(EASY), "A1", 4)
        self.assertFalse(why["forced"])
        self.assertIn("isn't forced", " ".join(why["steps"]))


class TestPencilMarkLesson(unittest.TestCase):

    def test_candidates_accepted_and_non_candidates_explained(self):
        ok = LessonEngine.verify_lesson_action("lesson_6_pencil_marks", "A1", 4)
        self.assertTrue(ok["is_candidate"])
        self.assertEqual(ok["candidates"], [4, 5])
        bad = LessonEngine.verify_lesson_action("lesson_6_pencil_marks", "A1", 3)
        self.assertFalse(bad["is_candidate"])
        self.assertIn("A3", bad["message"])
        self.assertFalse(bad["completed"])


if __name__ == "__main__":
    unittest.main()
