"""
Explanation Engine Module - Milestone 2.
Translates ReasoningSteps into natural-language explanations across 3 adaptive tiers
(Socratic, Focused, and Full Deduction) without LLM calls.
"""

import sys
import os
from typing import Dict, Any, Optional, List, Tuple

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, UNITS, PEERS, ROWS, COLS, SQUARE_TO_COORD
from .reasoning_trace import ReasoningStep, get_unit_description


def get_cell_unit_descriptions(cell: str) -> Dict[str, str]:
    """Return friendly names for row, column, and box containing cell."""
    r, c = SQUARE_TO_COORD[cell]
    row_name = f"Row {ROWS[r]}"
    col_name = f"Column {c + 1}"
    box_num = (r // 3) * 3 + (c // 3) + 1
    box_names = {
        1: "the top-left box",
        2: "the top-middle box",
        3: "the top-right box",
        4: "the middle-left box",
        5: "the middle box",
        6: "the middle-right box",
        7: "the bottom-left box",
        8: "the bottom-middle box",
        9: "the bottom-right box",
    }
    box_name = box_names.get(box_num, f"box {box_num}")
    return {
        "row": row_name,
        "column": col_name,
        "box": box_name,
        "primary_unit": box_name
    }


def format_candidates_human(candidates: List[str]) -> str:
    """Format candidate list into natural speech like '2 or 7'."""
    if not candidates:
        return "none"
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) == 2:
        return f"{candidates[0]} or {candidates[1]}"
    return ", ".join(candidates[:-1]) + f", or {candidates[-1]}"


def explain_step(
    step: ReasoningStep,
    level: int = 2,
    expanded: bool = False,
    current_domains: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate natural language explanation for a ReasoningStep at the requested hint level.

    Levels:
      1: Socratic (nudge towards the unit/region, no cell or value revealed)
      2: Focused (name the cell and show its candidate possibilities)
         expanded: include why peer values eliminated other choices
      3: Full Deduction (directly state the deduction and the value)
    """
    cell = step.cell
    val = step.value or ""
    step_type = step.step_type
    units_info = get_cell_unit_descriptions(cell)

    candidates = current_domains.get(cell, step.candidates_before) if current_domains else step.candidates_before
    candidate_list = list(candidates) if candidates else ([val] if val else [])
    human_cands = format_candidates_human(candidate_list)

    # --------------------------------------------------------------------------
    # LEVEL 1: SOCRATIC (Nudge the player to inspect a region)
    # --------------------------------------------------------------------------
    if level == 1:
        if step_type == "contradiction":
            text = f"Notice a conflict near {units_info['primary_unit']} — one square has run out of legal numbers."
        elif step_type == "hidden_single":
            text = f"Look closely at {units_info['primary_unit']} — one digit has almost nowhere else it can go."
        elif step_type == "naked_single":
            unit_hint = units_info["row"]
            text = f"Take a look at {unit_hint} and {units_info['box']} — one square there doesn't have many options left."
        else:  # mrv_focus
            text = f"Take a look at {units_info['primary_unit']} — one square there doesn't have many options left."

        return {
            "level": 1,
            "level_name": "Socratic Nudge",
            "text": text,
            "cell": None,  # Do not spoil cell at Level 1
            "value": None,
            "certainty": step.certainty,
            "target_unit": units_info["primary_unit"],
            "step_type": step_type,
            "reason": step.reason,
            "related_cells": step.related_cells[:4],
        }

    # --------------------------------------------------------------------------
    # LEVEL 2: FOCUSED (Identify the cell and its current candidates)
    # --------------------------------------------------------------------------
    elif level == 2:
        if step_type == "contradiction":
            text = f"Look at {cell} — it has reached a dead end with no legal numbers left ({step.reason})."
        elif expanded:
            if step_type == "naked_single":
                text = (
                    f"Look at {cell} — its surrounding row, column, and box already contain all the other numbers, "
                    f"leaving only {human_cands}."
                )
            elif step_type == "hidden_single":
                text = (
                    f"Look at {cell} in {units_info['primary_unit']} — "
                    f"{val} cannot go anywhere else in this section, leaving {cell} as the only option."
                )
            else:
                text = (
                    f"Look at {cell} — the surrounding numbers have narrowed it down to "
                    f"only {human_cands}."
                )
        else:
            text = f"Look at {cell} — it can only be {human_cands} right now."

        return {
            "level": 2,
            "level_name": "Focused Candidate Hint",
            "text": text,
            "cell": cell,
            "candidates": candidate_list,
            "value": None,  # Still don't give the direct answer at level 2
            "certainty": step.certainty,
            "related_cells": step.related_cells[:4],
            "step_type": step_type,
            "reason": step.reason,
            "expanded": expanded,
        }

    # --------------------------------------------------------------------------
    # LEVEL 3: FULL DEDUCTION (Direct statement and assignment value)
    # --------------------------------------------------------------------------
    else:
        if step_type == "contradiction":
            text = f"That won't work — {step.reason}"
            value_to_place = None
        elif step_type == "hidden_single":
            text = f"{cell} has to be {val} — it is the only cell in {units_info['primary_unit']} that can take this number."
            value_to_place = val
        elif step_type == "naked_single":
            text = f"{cell} has to be {val} — its row, column, and box already rule out every other option."
            value_to_place = val
        else:  # mrv_focus
            text = f"{cell} is the most constrained square right now — try {candidate_list[0]}."
            value_to_place = candidate_list[0] if candidate_list else None

        return {
            "level": 3,
            "level_name": "Full Deduction",
            "text": text,
            "cell": cell,
            "value": value_to_place,
            "candidates": candidate_list,
            "certainty": step.certainty,
            "reason": step.reason,
            "related_cells": step.related_cells,
            "step_type": step_type,
        }

