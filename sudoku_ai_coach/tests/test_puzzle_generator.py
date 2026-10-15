"""
Tests for the level-aware puzzle generator:
every generated puzzle must be uniquely solvable, guess-free, and graded to the requested level.
"""

import os
import unittest

os.environ.setdefault("SUDOKU_GENERATOR_POOL", "0")

from fastapi.testclient import TestClient
from src.validator import SudokuValidator
from sudoku_ai_coach.api.app import app
from sudoku_ai_coach.api.puzzle_generator import count_solutions, generate_puzzle, random_solution
from sudoku_ai_coach.api.techniques.technique_engine import TechniqueEngine
import random


class TestPuzzleGenerator(unittest.TestCase):

    def assert_valid_puzzle(self, record):
        puzzle = record["puzzle"]
        self.assertEqual(len(puzzle), 81)
        self.assertEqual(count_solutions(puzzle), 1, "Generated puzzle must have exactly one solution")
        solved, _, final, _ = TechniqueEngine.solve_puzzle_with_techniques(puzzle, max_tier=record["required_tier"], max_steps=400)
        self.assertTrue(solved, "Generated puzzle must be solvable without guessing at its graded tier")
        is_valid, msg = SudokuValidator.is_valid_grid(final, puzzle)
        self.assertTrue(is_valid, msg)
        self.assertEqual(final, record["solution"])

    def test_random_solution_is_valid(self):
        grid = random_solution(random.Random(7))
        is_valid, msg = SudokuValidator.is_valid_grid("".join(map(str, grid)), "0" * 81)
        self.assertTrue(is_valid, msg)

    def test_count_solutions(self):
        self.assertEqual(count_solutions("0" * 81, limit=2), 2)
        self.assertEqual(count_solutions("003020600900305001001806400008102900700000008006708200002609500800203009005010300"), 1)
        self.assertEqual(count_solutions("11" + "0" * 79), 0)

    def test_beginner_puzzle(self):
        record = generate_puzzle("beginner", seed=1)
        self.assert_valid_puzzle(record)
        self.assertEqual(record["required_tier"], "beginner")
        self.assertTrue(record["meets_level"])
        self.assertGreaterEqual(record["clue_count"], 30)

    def test_intermediate_puzzle_requires_intermediate(self):
        record = generate_puzzle("intermediate", seed=2, time_budget=30.0)
        self.assert_valid_puzzle(record)
        self.assertTrue(record["meets_level"])
        self.assertEqual(record["required_tier"], "intermediate")
        solved_with_singles = TechniqueEngine.solve_puzzle_with_techniques(record["puzzle"], max_tier="beginner")[0]
        self.assertFalse(solved_with_singles, "Intermediate puzzle must not be solvable with singles alone")

    def test_advanced_puzzle_is_valid_even_on_fallback(self):
        record = generate_puzzle("advanced", seed=3, time_budget=1.0)
        self.assert_valid_puzzle(record)
        self.assertIn(record["required_tier"], ("intermediate", "advanced"))
        self.assertEqual(record["meets_level"], record["required_tier"] == "advanced")

    def test_rejects_unknown_level(self):
        with self.assertRaises(ValueError):
            generate_puzzle("expert")

    def test_generate_endpoint_loads_board(self):
        client = TestClient(app)
        res = client.post("/api/teacher/generate-puzzle", json={"level": "beginner"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertNotIn("solution", data["puzzle_meta"])
        self.assertEqual(data["board"]["initial_string"], data["puzzle_meta"]["puzzle"])
        self.assertEqual(client.post("/api/teacher/generate-puzzle", json={"level": "expert"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
