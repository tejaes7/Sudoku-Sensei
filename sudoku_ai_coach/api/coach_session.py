"""
Coach Session Module - Milestone 3.
Tracks per-session dialogue escalation state so sequential inquiries
("Give me a hint" -> "Why?" -> "I don't understand" -> "Just tell me")
escalate through Socratic -> Focused -> Focused Expanded -> Full Deduction.
"""

import sys
import os
from typing import Dict, Any, Optional

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from .board_state import BoardState
from .reasoning_trace import ReasoningStep
from .hint_engine import find_next_reasoning_step
from .explanation_engine import explain_step
from .analyze import compute_domains


class CoachSession:
    """
    Session-level state manager for adaptive hint escalation and dialogue history.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.last_hinted_cell: Optional[str] = None
        self.last_step: Optional[ReasoningStep] = None
        self.last_level_shown: int = 0
        self.last_expanded: bool = False
        self.dialogue_history: list = []

    def reset_session(self) -> None:
        """Clear cached hint state when board is reset or new puzzle loaded."""
        self.last_hinted_cell = None
        self.last_step = None
        self.last_level_shown = 0
        self.last_expanded = False
        self.dialogue_history.clear()

    def get_hint(
        self,
        board_state: BoardState,
        requested_level: Optional[int] = None,
        escalate: bool = False
    ) -> Dict[str, Any]:
        """
        Produce a hint for the current board state.
        If escalate is True:
          0 -> Level 1 (Socratic)
          Level 1 -> Level 2 (Focused)
          Level 2 -> Level 2 (Focused, Expanded)
          Level 2 Expanded -> Level 3 (Full)
        If requested_level is explicitly passed, respects that level.
        """
        # Determine if we should reuse the existing step or calculate a new one
        domains_set, _ = compute_domains(board_state.board.grid)
        formatted_domains = {
            s: "".join(str(d) for d in sorted(domains_set[s]))
            for s in domains_set
        }

        # If the cached cell was already filled by user, find a new deduction
        need_new_step = (
            self.last_step is None or
            self.last_hinted_cell is None or
            board_state.get_cell_value(self.last_hinted_cell) != 0
        )

        if need_new_step:
            step = find_next_reasoning_step(board_state)
            if step is None:
                return {
                    "level": 0,
                    "level_name": "Completed",
                    "text": "The puzzle is already completely filled and solved! Great job.",
                    "cell": None,
                    "value": None,
                    "certainty": "deduced"
                }
            self.last_step = step
            self.last_hinted_cell = step.cell
            self.last_level_shown = 0
            self.last_expanded = False

        step = self.last_step

        # Determine target level
        target_level = requested_level
        use_expanded = False

        if escalate:
            if self.last_level_shown == 0:
                target_level = 1
                use_expanded = False
            elif self.last_level_shown == 1:
                target_level = 2
                use_expanded = False
            elif self.last_level_shown == 2 and not self.last_expanded:
                target_level = 2
                use_expanded = True
            else:
                target_level = 3
                use_expanded = False
        elif target_level is None:
            target_level = 1  # Default initial hint is Socratic

        # If requested level is 2 and we were already on standard 2, expand it
        if target_level == 2 and self.last_level_shown == 2 and not self.last_expanded:
            use_expanded = True

        self.last_level_shown = target_level
        self.last_expanded = use_expanded

        explanation = explain_step(
            step=step,
            level=target_level,
            expanded=use_expanded,
            current_domains=formatted_domains
        )

        # Log to dialogue history
        self.dialogue_history.append({
            "sender": "ai",
            "level": target_level,
            "level_name": explanation["level_name"],
            "text": explanation["text"],
            "cell": explanation.get("cell"),
            "certainty": explanation.get("certainty", "deduced")
        })

        return explanation

    def explain_cell(self, board_state: BoardState, cell: str) -> Dict[str, Any]:
        """
        Explain the current constraints and candidate options specifically for cell.
        """
        domains_set, _ = compute_domains(board_state.board.grid)
        formatted_domains = {
            s: "".join(str(d) for d in sorted(domains_set[s]))
            for s in domains_set
        }

        val = board_state.get_cell_value(cell)
        if board_state.is_clue(cell):
            return {
                "cell": cell,
                "is_clue": True,
                "text": f"Cell {cell} is an initial clue fixed at {val}.",
                "candidates": [str(val)],
                "certainty": "deduced"
            }

        candidates = formatted_domains.get(cell, "")
        cand_list = list(candidates)
        cand_str = "{" + ", ".join(cand_list) + "}"

        if len(cand_list) == 0:
            text = f"Cell {cell} is currently in a contradiction state: 0 legal candidate digits remain!"
        elif len(cand_list) == 1:
            text = f"Cell {cell} is a Naked Single! It only has one legal candidate remaining: {cand_str}."
        else:
            text = f"Cell {cell} currently has {len(cand_list)} possible legal candidate values: {cand_str}."

        return {
            "cell": cell,
            "is_clue": False,
            "text": text,
            "candidates": cand_list,
            "value": str(val) if val != 0 else None,
            "certainty": "deduced"
        }
