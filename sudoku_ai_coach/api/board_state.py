"""
BoardState Module - Milestone 0.
Wraps SudokuBoard from src.board with move tracking, undo/redo, and serialization for API consumption.
"""

import sys
import os
from typing import List, Dict, Any, Optional, Tuple, Union

# Ensure parent directory is in sys.path to import from src
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SudokuBoard, SQUARES, COORD_TO_SQUARE, SQUARE_TO_COORD, parse_grid, grid_to_string


class BoardState:
    """
    Stateful wrapper around SudokuBoard supporting user moves, undo, and reset.
    """

    def __init__(self, puzzle: str):
        self.raw_initial = puzzle
        self.board = SudokuBoard(puzzle)
        self.move_history: List[Dict[str, Any]] = []

    @property
    def initial_puzzle(self) -> str:
        return self.raw_initial

    def load_puzzle(self, puzzle: str) -> None:
        """Load a new puzzle string and clear history."""
        self.raw_initial = puzzle
        self.board = SudokuBoard(puzzle)
        self.move_history.clear()

    def is_clue(self, cell: str) -> bool:
        """Return True if the given cell was part of the initial clues."""
        r, c = SQUARE_TO_COORD[cell]
        return self.board.initial_grid[r][c] != 0

    def get_cell_value(self, cell: str) -> int:
        """Get the current integer value in cell ('A1'-'I9')."""
        r, c = SQUARE_TO_COORD[cell]
        return self.board.grid[r][c]

    def set_cell_value(self, cell: str, val: int) -> bool:
        """
        Apply a user move to cell if it is not a clue.
        Appends to move_history.
        Returns True if successful, False if cell is a locked clue.
        """
        if self.is_clue(cell):
            return False

        r, c = SQUARE_TO_COORD[cell]
        old_val = self.board.grid[r][c]
        if old_val == val:
            return True  # No change

        self.board.grid[r][c] = val
        self.move_history.append({
            "cell": cell,
            "row": r,
            "col": c,
            "old_val": old_val,
            "new_val": val,
        })
        return True

    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Undo the most recent user move.
        Returns the undone move metadata, or None if history is empty.
        """
        if not self.move_history:
            return None

        last_move = self.move_history.pop()
        r, c = last_move["row"], last_move["col"]
        self.board.grid[r][c] = last_move["old_val"]
        return last_move

    def reset(self) -> None:
        """Reset the grid back to its initial clue configuration."""
        self.board.grid = [row[:] for row in self.board.initial_grid]
        self.move_history.clear()

    def get_current_string(self) -> str:
        """Return 81-character string of the current grid."""
        return self.board.to_string()

    def get_initial_string(self) -> str:
        """Return 81-character string of the initial grid."""
        return grid_to_string(self.board.initial_grid)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize current board state for API response."""
        cells = []
        for s in SQUARES:
            r, c = SQUARE_TO_COORD[s]
            val = self.board.grid[r][c]
            clue = self.board.initial_grid[r][c] != 0
            cells.append({
                "cell": s,
                "row": r,
                "col": c,
                "value": val,
                "is_clue": clue,
            })

        unassigned = sum(1 for c in cells if c["value"] == 0)
        return {
            "cells": cells,
            "grid": [row[:] for row in self.board.grid],
            "clues": [[val != 0 for val in row] for row in self.board.initial_grid],
            "current_string": self.get_current_string(),
            "initial_string": self.get_initial_string(),
            "clue_count": self.board.clue_count,
            "unassigned_count": unassigned,
            "empty_count": unassigned,
            "move_count": len(self.move_history),
            "is_complete": unassigned == 0,
        }
