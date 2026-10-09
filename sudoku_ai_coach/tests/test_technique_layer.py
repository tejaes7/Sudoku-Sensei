"""
Unit tests for deterministic human technique deduction layer.
"""

import unittest
from src.board import parse_grid, grid_to_string, SQUARES
from sudoku_ai_coach.api.techniques.technique_engine import TechniqueEngine
from sudoku_ai_coach.api.techniques.full_house import find_full_house
from sudoku_ai_coach.api.techniques.singles import find_naked_single, find_hidden_single
from sudoku_ai_coach.api.techniques.subsets import find_naked_pair
from sudoku_ai_coach.api.techniques.intersections import find_pointing_pair


class TestTechniqueLayer(unittest.TestCase):

    def test_full_house_detection(self):
        # Row A has 8 digits filled: 1 2 3 4 5 6 7 8 0
        grid = [[0]*9 for _ in range(9)]
        for c in range(8):
            grid[0][c] = c + 1
        grid[0][8] = 0

        res = find_full_house(grid)
        self.assertIsNotNone(res)
        self.assertEqual(res["technique_id"], "full_house")
        self.assertEqual(res["target_cells"], ["A9"])
        self.assertEqual(res["target_value"], 9)

    def test_naked_single_detection(self):
        # Cell E5 sees 1,2,3,4,6,7,8,9 from peers -> must be 5
        grid = [[0]*9 for _ in range(9)]
        grid[0][4] = 1  # Col 5
        grid[1][4] = 2
        grid[2][4] = 3
        grid[4][0] = 4  # Row E
        grid[4][1] = 6
        grid[4][2] = 7
        grid[3][3] = 8  # Box 5
        grid[5][5] = 9

        res = find_naked_single(grid)
        self.assertIsNotNone(res)
        self.assertEqual(res["technique_id"], "naked_single")
        self.assertIn("E5", res["target_cells"])
        self.assertEqual(res["target_value"], 5)

    def test_hidden_single_detection(self):
        # In Box 1, 5 can only go in A1 because other cells are blocked or filled
        grid = [[0]*9 for _ in range(9)]
        grid[1][0] = 1
        grid[2][0] = 2
        # Row B and C have 5s elsewhere
        grid[1][8] = 5
        grid[2][8] = 5
        # Col 2 and 3 have 5s
        grid[8][1] = 5
        grid[8][2] = 5

        res = find_hidden_single(grid)
        self.assertIsNotNone(res)
        self.assertEqual(res["technique_id"], "hidden_single")
        self.assertEqual(res["target_cells"], ["A1"])
        self.assertEqual(res["target_value"], 5)

    def test_technique_engine_step_priority(self):
        # A grid with a Full House should prioritize Full House over other techniques
        grid = [[0]*9 for _ in range(9)]
        for c in range(8):
            grid[0][c] = c + 1
        grid[0][8] = 0

        step = TechniqueEngine.get_next_step(grid)
        self.assertIsNotNone(step)
        self.assertEqual(step.technique_id, "full_house")

    def test_solve_puzzle_with_techniques(self):
        # Standard easy puzzle solves with zero guessing
        p_easy = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        solved, steps, final_str, hardest = TechniqueEngine.solve_puzzle_with_techniques(p_easy)
        self.assertTrue(solved)
        self.assertGreater(len(steps), 0)
        self.assertIn("0", p_easy)
        self.assertNotIn("0", final_str)


if __name__ == "__main__":
    unittest.main()
