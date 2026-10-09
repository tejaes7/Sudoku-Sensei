"""
Baseline Solver Module - Phase 2.
Implements an intentionally unoptimized, standard recursive Depth-First Search
(Backtracking) solver with fixed variable ordering, fixed value ordering, and no constraint propagation.
"""

import time
from typing import List, Optional, Tuple, Union
from .board import parse_grid, grid_to_string
from .telemetry import Telemetry
from .validator import SudokuValidator


class BaselineSolver:
    """
    Standard unoptimized recursive backtracking Sudoku solver.
    Characteristics:
      - Variable Ordering: Static row-major order (top-left to bottom-right).
      - Value Ordering: Static sequential order (1 to 9).
      - Pruning: None (no Forward Checking, no AC-3).
      - Constraint Checking: Evaluated on-the-fly at candidate assignment time.
    """

    def __init__(self, timeout_sec: Optional[float] = None):
        self.timeout_sec = timeout_sec
        self.nodes_expanded = 0
        self.max_depth = 0
        self.start_time = 0.0
        self.timed_out = False

    def is_safe(self, grid: List[List[int]], r: int, c: int, val: int) -> bool:
        """Check if placing val at grid[r][c] violates row, column, or 3x3 box constraints."""
        # 1. Row check
        for j in range(9):
            if grid[r][j] == val:
                return False

        # 2. Column check
        for i in range(9):
            if grid[i][c] == val:
                return False

        # 3. 3x3 Box check
        start_r = (r // 3) * 3
        start_c = (c // 3) * 3
        for i in range(3):
            for j in range(3):
                if grid[start_r + i][start_c + j] == val:
                    return False

        return True

    def find_empty_cell(self, grid: List[List[int]]) -> Optional[Tuple[int, int]]:
        """Static variable selection: finds the first empty cell in standard row-major order."""
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    return r, c
        return None

    def _backtrack(self, grid: List[List[int]], depth: int) -> bool:
        """Recursive backtracking search routine."""
        # Check timeout
        if self.timeout_sec is not None:
            if (time.perf_counter() - self.start_time) > self.timeout_sec:
                self.timed_out = True
                return False

        if depth > self.max_depth:
            self.max_depth = depth

        empty_cell = self.find_empty_cell(grid)
        if empty_cell is None:
            # All cells are successfully assigned
            return True

        r, c = empty_cell

        # Fixed value ordering: strictly try 1 through 9
        for val in range(1, 10):
            if self.is_safe(grid, r, c, val):
                # Make assignment
                grid[r][c] = val
                self.nodes_expanded += 1

                if self._backtrack(grid, depth + 1):
                    return True

                if self.timed_out:
                    return False

                # Backtrack
                grid[r][c] = 0

        return False

    def solve(
        self,
        puzzle: Union[str, List[List[int]]],
        puzzle_id: str = "0",
        difficulty: str = "unknown"
    ) -> Telemetry:
        """
        Solve the given Sudoku puzzle using pure recursive backtracking.

        Returns:
            Telemetry object containing runtime, node expansions, max depth, and solution.
        """
        grid = parse_grid(puzzle) if isinstance(puzzle, str) else [row[:] for row in puzzle]
        orig_str = grid_to_string(grid)

        # Reset telemetry counters
        self.nodes_expanded = 0
        self.max_depth = 0
        self.timed_out = False
        self.start_time = time.perf_counter()

        solved = self._backtrack(grid, depth=0)
        end_time = time.perf_counter()
        runtime_ms = (end_time - self.start_time) * 1000.0

        sol_str = grid_to_string(grid) if solved else None
        error_msg = "Timeout exceeded" if self.timed_out else (None if solved else "Unsatisfiable or search exhausted")

        # Validate solution if claimed solved
        if solved and sol_str:
            is_valid, reason = SudokuValidator.is_valid_grid(sol_str, orig_str)
            if not is_valid:
                solved = False
                error_msg = f"Validation failed: {reason}"

        return Telemetry(
            solver_name="baseline_dfs",
            puzzle_id=str(puzzle_id),
            difficulty=difficulty,
            solved=solved,
            runtime_ms=runtime_ms,
            nodes_expanded=self.nodes_expanded,
            max_depth=self.max_depth,
            solution=sol_str,
            error_message=error_msg,
        )
