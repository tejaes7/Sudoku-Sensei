"""
Board representation and coordinate mapping for Sudoku.
Follows Peter Norvig's conventions and standard 9x9 matrix representations.
"""

from typing import List, Dict, Set, Tuple

# Norvig notation: Rows 'A'-'I', Columns '1'-'9'
ROWS = "ABCDEFGHI"
COLS = "123456789"

def cross(a: str, b: str) -> List[str]:
    """Cross product of elements in a and elements in b."""
    return [s + t for s in a for t in b]

SQUARES: List[str] = cross(ROWS, COLS)

# 27 units: 9 rows, 9 columns, 9 3x3 boxes
UNIT_LIST: List[List[str]] = (
    [cross(r, COLS) for r in ROWS] +
    [cross(ROWS, c) for c in COLS] +
    [cross(rs, cs) for rs in ("ABC", "DEF", "GHI") for cs in ("123", "456", "789")]
)

# Map each square to the 3 units it belongs to
UNITS: Dict[str, List[List[str]]] = {
    s: [u for u in UNIT_LIST if s in u] for s in SQUARES
}

# Map each square to its 20 distinct peers
PEERS: Dict[str, Set[str]] = {
    s: set(sum(UNITS[s], [])) - {s} for s in SQUARES
}

# Coordinate mapping between (row_idx, col_idx) and Norvig square string ('A1'..'I9')
COORD_TO_SQUARE: Dict[Tuple[int, int], str] = {
    (r, c): ROWS[r] + COLS[c] for r in range(9) for c in range(9)
}
SQUARE_TO_COORD: Dict[str, Tuple[int, int]] = {
    ROWS[r] + COLS[c]: (r, c) for r in range(9) for c in range(9)
}


def parse_grid(grid_input: str) -> List[List[int]]:
    """
    Parse an 81-character string, multi-line string, or 9x9 grid into a 9x9 int matrix.
    0, '.', or ' ' represent empty cells. Digits '1'-'9' represent clues.
    """
    cleaned = "".join(ch for ch in grid_input if ch in "0123456789.")
    if len(cleaned) != 81:
        raise ValueError(f"Input puzzle must contain exactly 81 cells, found {len(cleaned)} characters.")
    
    grid = []
    for r in range(9):
        row = []
        for c in range(9):
            ch = cleaned[r * 9 + c]
            row.append(int(ch) if ch.isdigit() and ch != '0' else 0)
        grid.append(row)
    return grid


def grid_to_string(grid: List[List[int]]) -> str:
    """Convert a 9x9 int matrix into an 81-character string (empty cells as '0')."""
    return "".join(str(grid[r][c]) for r in range(9) for c in range(9))


def format_grid(grid: List[List[int]]) -> str:
    """
    Return a visually formatted, aesthetic ASCII representation of a 9x9 Sudoku grid.
    """
    lines = []
    horizontal_border = "+-------+-------+-------+"
    for r in range(9):
        if r % 3 == 0:
            lines.append(horizontal_border)
        row_str = "| "
        for c in range(9):
            val = grid[r][c]
            cell_char = str(val) if val != 0 else "."
            row_str += cell_char + " "
            if (c + 1) % 3 == 0:
                row_str += "| "
        lines.append(row_str)
    lines.append(horizontal_border)
    return "\n".join(lines)


class SudokuBoard:
    """
    Sudoku board wrapper supporting both coordinate (r, c) access
    and Norvig-style string representations.
    """
    def __init__(self, puzzle: str):
        self.raw_puzzle = puzzle
        self.grid = parse_grid(puzzle)
        self.initial_grid = [row[:] for row in self.grid]
        self.clue_count = sum(1 for r in range(9) for c in range(9) if self.grid[r][c] != 0)

    def get(self, r: int, c: int) -> int:
        return self.grid[r][c]

    def set(self, r: int, c: int, val: int):
        self.grid[r][c] = val

    def to_string(self) -> str:
        return grid_to_string(self.grid)

    def display(self) -> str:
        return format_grid(self.grid)

    def __repr__(self) -> str:
        return f"<SudokuBoard clues={self.clue_count}>\n{self.display()}"
