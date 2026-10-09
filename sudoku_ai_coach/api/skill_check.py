"""
Skill Check Assessment Module:
Delivers a 2-minute quick check (4 lightweight questions) to recommend the optimal learning level.
"""

from typing import List, Dict, Any


SKILL_CHECK_QUESTIONS = [
    {
        "id": "q1_rules",
        "question": "What is the fundamental rule of Sudoku?",
        "options": [
            {"id": "a", "text": "Every row, column, and 3×3 box must contain digits 1–9 with NO duplicates.", "correct": True},
            {"id": "b", "text": "Digits in each row must sum up to exactly 100.", "correct": False},
            {"id": "c", "text": "You can repeat numbers in a box as long as the row is unique.", "correct": False}
        ],
        "explanation": "Correct! Each digit 1–9 must appear exactly once in every row, column, and 3×3 box."
    },
    {
        "id": "q2_full_house",
        "question": "In a 4×4 mini-grid row, you see [1, 3, 4, _]. What number must fill the empty space?",
        "options": [
            {"id": "a", "text": "2", "correct": True},
            {"id": "b", "text": "4", "correct": False},
            {"id": "c", "text": "5", "correct": False}
        ],
        "explanation": "Spot on! The missing number in the set {1, 2, 3, 4} is 2."
    },
    {
        "id": "q3_naked_single",
        "question": "A blank cell's neighbors (row, column, box) contain numbers 1, 2, 3, 4, 6, 7, 8, 9. What number can go in this cell?",
        "options": [
            {"id": "a", "text": "5 (the only number not seen)", "correct": True},
            {"id": "b", "text": "Any number from 1 to 9", "correct": False},
            {"id": "c", "text": "None, the puzzle is broken", "correct": False}
        ],
        "explanation": "Exactly! When 8 numbers are ruled out by neighbors, the 9th number (5) is forced (Naked Single)."
    },
    {
        "id": "q4_experience",
        "question": "How comfortable are you with advanced techniques like Naked Pairs or Pointing Lines?",
        "options": [
            {"id": "a", "text": "I've never heard of them — I want to learn the basics.", "tier": "beginner"},
            {"id": "b", "text": "I know what pairs are, but struggle with harder puzzles.", "tier": "intermediate"},
            {"id": "c", "text": "Very comfortable — I use them regularly on medium and hard grids.", "tier": "advanced"}
        ]
    }
]


def evaluate_skill_check(answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Evaluates the 4 answers and returns a recommended starting level.
    """
    score = 0
    # Q1
    if answers.get("q1_rules") == "a":
        score += 1
    # Q2
    if answers.get("q2_full_house") == "a":
        score += 1
    # Q3
    if answers.get("q3_naked_single") == "a":
        score += 1

    exp = answers.get("q4_experience", "a")

    if score <= 1 or exp == "a":
        rec_level = "beginner"
        rec_title = "Beginner Track"
        rationale = "We recommend starting with our gentle guided lessons on the board. You'll master grid reading, scanning, and full houses in minutes!"
    elif score >= 2 and exp == "c":
        rec_level = "advanced"
        rec_title = "Advanced Track"
        rationale = "You have strong Sudoku fundamentals! We'll start you on medium and hard puzzles with advanced techniques like Pairs, Triples, and X-Wings."
    else:
        rec_level = "intermediate"
        rec_title = "Intermediate Track"
        rationale = "You have a solid grasp of Sudoku rules! You'll jump straight into solving with on-demand hints and learn intermediate techniques when needed."

    return {
        "score": score,
        "recommended_level": rec_level,
        "recommended_title": rec_title,
        "rationale": rationale
    }
