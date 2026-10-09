"""
Telemetry module for Sudoku Solvers.
Provides a unified dataclass for tracking performance metrics across all solver variants.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class Telemetry:
    """
    Standardized performance telemetry recorded during puzzle solving.

    Attributes:
        solver_name: Identifier for the solver configuration (e.g. 'plain_dfs', 'dfs_fc', etc.).
        puzzle_id: Identifier or index of the puzzle in the dataset.
        difficulty: Difficulty label ('easy', 'medium', 'hard', 'extreme').
        solved: True if a valid complete solution was found, False otherwise.
        runtime_ms: High-resolution wall-clock runtime in milliseconds.
        nodes_expanded: Number of variable assignment attempts / search states explored.
        max_depth: Maximum recursion depth reached in the search tree.
        solution: 81-character string representing the solved grid (or None if unsolved).
        error_message: Optional error or timeout description if solving failed.
    """
    solver_name: str
    puzzle_id: str
    difficulty: str
    solved: bool
    runtime_ms: float
    nodes_expanded: int
    max_depth: int
    solution: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert telemetry instance to a dictionary for CSV/JSON serialization."""
        return asdict(self)
