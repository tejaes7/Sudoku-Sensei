"""
Validation module for Sudoku solutions.
Ensures that all solutions satisfy row, column, box, and initial clue constraints.
"""

from typing import Tuple, Optional, Union, List
from .board import parse_grid, grid_to_string


class SudokuValidator:
    """
    Validates complete Sudoku solutions against the formal rules of Sudoku
    and checks consistency with original clues.
    """

    @staticmethod
    def is_valid_grid(
        solution: Union[str, List[List[int]]],
        original_puzzle: Optional[Union[str, List[List[int]]]] = None
    ) -> Tuple[bool, str]:
        """
        Validate a proposed Sudoku solution.

        Args:
            solution: 81-character string or 9x9 int grid representing the proposed solution.
            original_puzzle: Optional 81-character string or 9x9 int grid of the starting puzzle.

        Returns:
            Tuple[bool, str]: (True, "Valid solution") if correct, or (False, error_reason).
        """
        try:
            sol_grid = parse_grid(solution) if isinstance(solution, str) else solution
        except Exception as e:
            return False, f"Invalid solution format: {str(e)}"

        # 1. Check all cells are filled with digits 1-9
        for r in range(9):
            for c in range(9):
                val = sol_grid[r][c]
                if not (1 <= val <= 9):
                    return False, f"Cell ({r},{c}) has invalid value {val}. Must be 1-9."

        # 2. Check clue preservation if original puzzle is provided
        if original_puzzle is not None:
            try:
                orig_grid = parse_grid(original_puzzle) if isinstance(original_puzzle, str) else original_puzzle
                for r in range(9):
                    for c in range(9):
                        orig_val = orig_grid[r][c]
                        if orig_val != 0 and orig_val != sol_grid[r][c]:
                            return False, (
                                f"Clue mismatch at ({r},{c}): original clue was {orig_val}, "
                                f"solution has {sol_grid[r][c]}."
                            )
            except Exception as e:
                return False, f"Failed to check clue preservation: {str(e)}"

        # 3. Check Row uniqueness
        for r in range(9):
            row_vals = sol_grid[r]
            if len(set(row_vals)) != 9:
                return False, f"Row {r} violates AllDifferent constraint: contains duplicates."

        # 4. Check Column uniqueness
        for c in range(9):
            col_vals = [sol_grid[r][c] for r in range(9)]
            if len(set(col_vals)) != 9:
                return False, f"Column {c} violates AllDifferent constraint: contains duplicates."

        # 5. Check 3x3 Box uniqueness
        for box_row in range(3):
            for box_col in range(3):
                box_vals = [
                    sol_grid[box_row * 3 + r][box_col * 3 + c]
                    for r in range(3)
                    for c in range(3)
                ]
                if len(set(box_vals)) != 9:
                    return False, (
                        f"3x3 Box at ({box_row},{box_col}) violates AllDifferent constraint: "
                        f"contains duplicates."
                    )

        return True, "Valid solution"

    @classmethod
    def assert_valid(
        cls,
        solution: Union[str, List[List[int]]],
        original_puzzle: Optional[Union[str, List[List[int]]]] = None
    ):
        """Raises ValueError if the solution is invalid."""
        valid, reason = cls.is_valid_grid(solution, original_puzzle)
        if not valid:
            raise ValueError(f"Solution Validation Failed: {reason}")
