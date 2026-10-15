"""
Sudoku Solver Package - CSP engine for the Sudoku AI Coach
"""

from .telemetry import Telemetry
from .board import SudokuBoard, parse_grid, format_grid
from .validator import SudokuValidator
from .csp_solver import CSPSolver

__all__ = [
    "Telemetry",
    "SudokuBoard",
    "parse_grid",
    "format_grid",
    "SudokuValidator",
    "CSPSolver",
]
