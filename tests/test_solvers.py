"""
Comprehensive Unit Tests for Sudoku Solvers, Board, Validator, and Telemetry.
"""

import unittest
from src.board import SQUARES, PEERS, UNITS, parse_grid, grid_to_string
from src.validator import SudokuValidator
from src.csp_solver import CSPSolver


class TestSudokuSuite(unittest.TestCase):

    def setUp(self):
        # Sample standard easy puzzle
        self.easy_puzzle = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        self.easy_solution = "483921657967345821251876493548132976729564138136798245372689514814253769695417382"

    def test_board_geometry_and_norvig_invariants(self):
        """Verify Norvig representation invariants: 81 squares, 27 units, exactly 20 peers per square."""
        self.assertEqual(len(SQUARES), 81)
        self.assertEqual(len(UNITS), 81)
        for s in SQUARES:
            self.assertEqual(len(PEERS[s]), 20, f"Square {s} does not have exactly 20 peers")
            self.assertEqual(len(UNITS[s]), 3, f"Square {s} does not belong to exactly 3 units")

    def test_grid_parsing_and_formatting(self):
        """Verify round-trip parsing of 81-character puzzle strings."""
        grid = parse_grid(self.easy_puzzle)
        self.assertEqual(len(grid), 9)
        self.assertEqual(len(grid[0]), 9)
        reconstructed = grid_to_string(grid)
        self.assertEqual(reconstructed, self.easy_puzzle)

    def test_validator_with_valid_and_invalid_grids(self):
        """Verify SudokuValidator correctly accepts valid grids and rejects invalid ones."""
        # 1. Valid solution
        valid, msg = SudokuValidator.is_valid_grid(self.easy_solution, self.easy_puzzle)
        self.assertTrue(valid, msg)

        # 2. Row duplicate
        bad_sol = list(self.easy_solution)
        bad_sol[0] = bad_sol[1]  # duplicate first two cells in row 0
        valid, msg = SudokuValidator.is_valid_grid("".join(bad_sol))
        self.assertFalse(valid)
        self.assertIn("Row 0 violates AllDifferent", msg)

        # 3. Clue mutation
        mutated_sol = list(self.easy_solution)
        # Find a clue cell in easy_puzzle (e.g. index 2 is '3')
        mutated_sol[2] = "7"
        valid, msg = SudokuValidator.is_valid_grid("".join(mutated_sol), self.easy_puzzle)
        self.assertFalse(valid)
        self.assertIn("Clue mismatch", msg)

    def test_csp_solver_configurations(self):
        """Verify all 4 incremental CSP configurations solve the puzzle correctly."""
        configs = [
            # Config B: DFS + Forward Checking (no MRV, no LCV)
            CSPSolver(propagation="fc", use_mrv=False, use_lcv=False, timeout_sec=5.0),
            # Config C: DFS + FC + MRV (no LCV)
            CSPSolver(propagation="fc", use_mrv=True, use_lcv=False, timeout_sec=5.0),
            # Config D: DFS + FC + MRV + LCV
            CSPSolver(propagation="fc", use_mrv=True, use_lcv=True, timeout_sec=5.0),
            # Norvig's agent
            CSPSolver(propagation="norvig", timeout_sec=5.0),
        ]

        for solver in configs:
            tel = solver.solve(self.easy_puzzle, puzzle_id="easy_1", difficulty="easy")
            self.assertTrue(tel.solved, f"{solver.name} failed to solve easy puzzle")
            self.assertEqual(tel.solution, self.easy_solution, f"{solver.name} produced incorrect solution")
            self.assertGreaterEqual(tel.nodes_expanded, 0)
            self.assertGreater(tel.runtime_ms, 0)


if __name__ == "__main__":
    unittest.main()
