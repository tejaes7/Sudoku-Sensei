"""
Human-style deterministic technique deduction layer for Sudoku.
Applies techniques in order of difficulty with structured explanations and no guessing.
"""

from .technique_engine import TechniqueEngine, TechniqueStep
from .full_house import find_full_house
from .singles import find_naked_single, find_hidden_single
from .subsets import find_naked_pair, find_hidden_pair, find_naked_triple
from .intersections import find_pointing_pair, find_box_line_reduction
from .fish import find_x_wing

__all__ = [
    "TechniqueEngine",
    "TechniqueStep",
    "find_full_house",
    "find_naked_single",
    "find_hidden_single",
    "find_naked_pair",
    "find_hidden_pair",
    "find_naked_triple",
    "find_pointing_pair",
    "find_box_line_reduction",
    "find_x_wing",
]
