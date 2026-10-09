"""
Lesson Engine Module:
Defines the interactive beginner curriculum (Lessons a through g + 4x4 mini grid option).
Each lesson consists of: short explanation -> small interactive task -> instant feedback -> next step.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Lesson:
    lesson_id: str
    order: int
    title: str
    concept_summary: str
    grid_size: int  # 4 for mini-grid, 9 for full grid
    initial_grid: str
    clues_mask: List[str]  # cells considered clues
    instruction: str
    target_cell: str
    expected_value: Optional[int]
    highlight_cells: List[str]
    success_feedback: str
    hint_text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


LESSONS_CATALOG: List[Lesson] = [
    # Lesson A: The Core Rule on 4x4 Mini-Grid
    Lesson(
        lesson_id="lesson_1_intro",
        order=1,
        title="1. What Sudoku Is (The One Rule)",
        concept_summary="Sudoku has just one simple rule: each number must appear exactly once in every row, column, and box without repeating.",
        grid_size=4,
        # 4x4 grid: row A: 1 2 3 [?], row B: 3 4 1 2, row C: 2 1 4 3, row D: 4 3 2 1
        initial_grid="1230341221434321",
        clues_mask=["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4"],
        instruction="Row A has 1, 2, and 3. By the fundamental rule, what number must go into the empty square A4?",
        target_cell="A4",
        expected_value=4,
        highlight_cells=["A1", "A2", "A3", "A4"],
        success_feedback="Spot on! Every row in this 4x4 grid must have 1, 2, 3, 4 with no duplicates. 4 was the only number missing.",
        hint_text="Look across Row A: you see 1, 2, and 3. In a 4x4 grid, the numbers are 1 through 4. Which one is left?"
    ),

    # Lesson B: Reading the Grid (Rows, Columns, Boxes)
    Lesson(
        lesson_id="lesson_2_grid",
        order=2,
        title="2. Reading the Grid (Rows, Columns, Boxes)",
        concept_summary="A standard Sudoku has 81 cells across 9 Rows (A–I), 9 Columns (1–9), and nine 3×3 Boxes. Each cell is named by its row and column (e.g. E5).",
        grid_size=9,
        initial_grid="000000000" * 9,
        clues_mask=[],
        instruction="Let's practice coordinates. Find and click on cell E5 (the center cell of the entire board).",
        target_cell="E5",
        expected_value=None,  # pure selection task
        highlight_cells=["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "A5", "B5", "C5", "D5", "F5", "G5", "H5", "I5"],
        success_feedback="Perfect! Cell E5 sits at the exact intersection of Row E and Column 5, right in the center Box 5.",
        hint_text="Follow Row E horizontally from the left, and Column 5 vertically from the top. Click right where they meet."
    ),

    # Lesson C: Easiest Win (Full House)
    Lesson(
        lesson_id="lesson_3_full_house",
        order=3,
        title="3. The Easiest Win: Full House",
        concept_summary="Whenever 8 of the 9 cells in any row, column, or box are already filled, you never have to guess. The last remaining cell must be the 9th number.",
        grid_size=9,
        # Box 1 has 1-8 filled, C3 is empty
        initial_grid="123000000456000000780000000" + ("000000000" * 6),
        clues_mask=["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2"],
        instruction="In the top-left 3×3 box, 8 numbers are already placed (1, 2, 3, 4, 5, 6, 7, 8). What number must fill cell C3?",
        target_cell="C3",
        expected_value=9,
        highlight_cells=["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"],
        success_feedback="Brilliant! That is called a 'Full House'. Always keep an eye out for units with just 1 empty square.",
        hint_text="Count through the digits 1 through 9 inside the top-left box. Only one digit hasn't appeared yet."
    ),

    # Lesson D: Scanning for a Digit (Hidden Single)
    Lesson(
        lesson_id="lesson_4_hidden_single",
        order=4,
        title="4. Scanning: Hidden Single",
        concept_summary="Often a cell has several possibilities, but within a 3×3 box, a particular number has only ONE place it can legally fit because other rows/columns block it.",
        grid_size=9,
        # Center box 5 has only cell E5 open for 5
        initial_grid=(
            "000050000"  # A5 has 5
            "000000000"
            "000000000"
            "500000000"  # D1 has 5
            "000000000"  # E row
            "000000005"  # F9 has 5
            "000000000"
            "000000000"
            "000000000"
        ),
        clues_mask=["A5", "D1", "F9"],
        instruction="We need a 5 in Box 5 (the middle 3×3 box). Row D already has a 5, and Row F already has a 5. In Row E, Column 5 already has a 5 blocking it. Where can 5 go in Box 5? Try cell E4.",
        target_cell="E4",
        expected_value=5,
        highlight_cells=["D1", "F9", "A5", "E4"],
        success_feedback="Excellent scanning! Because Rows D and F and Column 5 are blocked by other 5s, 5 is forced into E4.",
        hint_text="Notice how the 5s in other rows cross out lines across Box 5. Enter 5 in cell E4."
    ),

    # Lesson E: Cell Elimination (Naked Single)
    Lesson(
        lesson_id="lesson_5_naked_single",
        order=5,
        title="5. Cell Elimination: Naked Single",
        concept_summary="Instead of asking 'Where can digit X go?', look at ONE cell and strike out all numbers already seen in its row, column, and box. If only one candidate survives, that's a Naked Single.",
        grid_size=9,
        # Cell E5 sees 1,2,3,4,6,7,8,9 in peers, leaving 5
        initial_grid=(
            "000010000"  # A5 has 1
            "000020000"  # B5 has 2
            "000030000"  # C5 has 3
            "000400000"  # D4 has 4
            "678000000"  # E1=6, E2=7, E3=8
            "000090000"  # F5 has 9
            "000000000"
            "000000000"
            "000000000"
        ),
        clues_mask=["A5", "B5", "C5", "D4", "E1", "E2", "E3", "F5"],
        instruction="Inspect cell E5. Its column has 1, 2, 3, 9; its row has 6, 7, 8; its box has 4. What is the ONLY number that can go into E5?",
        target_cell="E5",
        expected_value=5,
        highlight_cells=["A5", "B5", "C5", "D4", "E1", "E2", "E3", "F5", "E5"],
        success_feedback="Outstanding deduction! 1, 2, 3, 4, 6, 7, 8, 9 are all eliminated by its neighbors. Only 5 is legal.",
        hint_text="Check the numbers 1 through 9. Notice 1,2,3,4,6,7,8,9 are all taken by neighbors of E5. What single number is left?"
    ),

    # Lesson F: Pencil Marks (Candidate Notes)
    Lesson(
        lesson_id="lesson_6_pencil_marks",
        order=6,
        title="6. Pencil Marks: Recording Possibilities",
        concept_summary="When a cell has 2 or 3 legal candidates and you can't decide yet, good players jot down small pencil marks. This keeps track of options without guessing.",
        grid_size=9,
        initial_grid="003020600900305001001806400008102900700000008006708200002609500800203009005010300",
        clues_mask=["A3", "A5", "A7", "B1", "B4", "B6", "B9"],
        instruction="Pencil-mark every number that could still go in A1. Type a digit to add it as a small note — I'll tell you if a note can be ruled out.",
        target_cell="A1",
        expected_value=None,  # verified by testing pencil marks
        highlight_cells=["A1"],
        success_feedback="Great! Pencil marks are your memory aid. As you solve other cells, you can erase notes that become blocked.",
        hint_text="Check A1's row (Row A), column (Column 1), and box (Box 1). Any digit 1–9 that none of them contain is a candidate."
    ),

    # Lesson G: Your First Full Puzzle
    Lesson(
        lesson_id="lesson_7_first_puzzle",
        order=7,
        title="7. First Full Puzzle (Guided)",
        concept_summary="You're ready! Start solving on your own. Your patient coach is right beside you — press 'Ask for a hint' whenever you want a gentle nudge.",
        grid_size=9,
        # Very easy puzzle with lots of singles
        initial_grid="003020600900305001001806400008102900700000008006708200002609500800203009005010300",
        clues_mask=[],
        instruction="You've learned the tools. Press 'Start my first puzzle' to solve a full grid — I'll be right beside you with the hint ladder.",
        target_cell="",
        expected_value=None,
        highlight_cells=[],
        success_feedback="You're solving real Sudokus using pure deduction!",
        hint_text="Look at Box 1 or Column 4 to find quick singles."
    )
]


class LessonEngine:
    """Manages lesson state and validation."""

    @staticmethod
    def _verify_pencil_mark(lesson: "Lesson", cell: str, value: Optional[int]) -> Dict[str, Any]:
        from src.board import parse_grid, UNITS, SQUARE_TO_COORD
        from .techniques.utils import compute_live_candidates, format_unit_friendly

        grid = parse_grid(lesson.initial_grid)
        target = lesson.target_cell
        candidates = sorted(compute_live_candidates(grid)[target])
        base = {"pencil": True, "candidates": candidates, "completed": False}

        if cell != target:
            return {**base, "valid": False, "message": f"Pencil-mark cell {target} for this exercise."}
        if not value:
            return {**base, "valid": True, "message": lesson.instruction}
        if value in candidates:
            return {**base, "valid": True, "is_candidate": True,
                    "message": f"Yes — {value} is a candidate: Row A, Column 1, and Box 1 don't contain a {value}."}
        for unit in UNITS[target]:
            for sq in unit:
                r, c = SQUARE_TO_COORD[sq]
                if sq != target and grid[r][c] == value:
                    return {**base, "valid": False, "is_candidate": False,
                            "message": f"{value} can be ruled out — {format_unit_friendly(unit)} already has a {value} at {sq}."}
        return {**base, "valid": False, "is_candidate": False, "message": f"{value} can be ruled out for {target}."}

    @staticmethod
    def get_all_lessons() -> List[Dict[str, Any]]:
        return [l.to_dict() for l in LESSONS_CATALOG]

    @staticmethod
    def get_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
        for l in LESSONS_CATALOG:
            if l.lesson_id == lesson_id:
                return l.to_dict()
        return None

    @staticmethod
    def verify_lesson_action(lesson_id: str, cell: str, value: Optional[int]) -> Dict[str, Any]:
        lesson = None
        for l in LESSONS_CATALOG:
            if l.lesson_id == lesson_id:
                lesson = l
                break

        if not lesson:
            return {"valid": False, "message": "Lesson not found."}

        # Lesson 2 is click cell E5
        if lesson.lesson_id == "lesson_2_grid":
            if cell == lesson.target_cell:
                return {"valid": True, "completed": True, "message": lesson.success_feedback}
            else:
                return {"valid": False, "completed": False, "message": f"You clicked {cell}. We're looking for Row E, Column 5 ({lesson.target_cell})."}

        # Lesson 6 is pencil marks: every candidate of the target cell must be noted
        if lesson.lesson_id == "lesson_6_pencil_marks":
            return LessonEngine._verify_pencil_mark(lesson, cell, value)

        # Lesson 7 is open puzzle
        if lesson.lesson_id == "lesson_7_first_puzzle":
            return {"valid": True, "completed": True, "message": lesson.success_feedback}

        # Standard value entry check
        if cell == lesson.target_cell and value == lesson.expected_value:
            return {
                "valid": True,
                "completed": True,
                "message": lesson.success_feedback,
                "cell": cell,
                "value": value
            }
        elif cell == lesson.target_cell and value != lesson.expected_value:
            return {
                "valid": False,
                "completed": False,
                "message": f"Not quite. {value} in {cell} doesn't complete the rule. {lesson.hint_text}"
            }
        else:
            return {
                "valid": False,
                "completed": False,
                "message": f"Try focusing on cell {lesson.target_cell} first."
            }
