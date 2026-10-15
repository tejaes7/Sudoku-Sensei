"""
Comprehensive Unit & Integration Test Suite for Explainable Adaptive Sudoku AI Coach.
Validates Milestones M0 through M4.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from sudoku_ai_coach.api.board_state import BoardState
from sudoku_ai_coach.api.analyze import analyze_board, compute_domains
from sudoku_ai_coach.api.reasoning_trace import (
    ReasoningStep, assign_trace, eliminate_trace, build_propagated_state
)
from sudoku_ai_coach.api.move_checker import check_move
from sudoku_ai_coach.api.explanation_engine import explain_step
from sudoku_ai_coach.api.what_if import simulate_move
from sudoku_ai_coach.api.coach_session import CoachSession
from sudoku_ai_coach.api.app import app


class TestSudokuAICoach(unittest.TestCase):

    def setUp(self):
        # Sample standard easy puzzle
        self.easy_puzzle = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        self.easy_solution = "483921657967345821251876493548132976729564138136798245372689514814253769695417382"
        self.board = BoardState(self.easy_puzzle)
        self.client = TestClient(app)

    # --------------------------------------------------------------------------
    # Milestone 0 Tests: BoardState and analyze_board
    # --------------------------------------------------------------------------
    def test_m0_board_state_clue_locking_and_undo(self):
        """Verify BoardState locks clues, applies valid moves, and supports undo/reset."""
        # A3 is clue '3'
        self.assertTrue(self.board.is_clue("A3"))
        self.assertFalse(self.board.set_cell_value("A3", 9))
        self.assertEqual(self.board.get_cell_value("A3"), 3)

        # A1 is unassigned (0)
        self.assertFalse(self.board.is_clue("A1"))
        self.assertTrue(self.board.set_cell_value("A1", 4))
        self.assertEqual(self.board.get_cell_value("A1"), 4)
        self.assertEqual(len(self.board.move_history), 1)

        # Undo
        undone = self.board.undo()
        self.assertIsNotNone(undone)
        self.assertEqual(self.board.get_cell_value("A1"), 0)
        self.assertEqual(len(self.board.move_history), 0)

        # Reset
        self.board.set_cell_value("A1", 4)
        self.board.reset()
        self.assertEqual(self.board.get_cell_value("A1"), 0)
        self.assertEqual(self.board.get_current_string(), self.easy_puzzle)

    def test_m0_analyze_board_metrics(self):
        """Verify analyze_board returns accurate domains, MRV cell, and constraint analytics."""
        analysis = analyze_board(self.board)
        self.assertIn("domains", analysis)
        self.assertIn("mrv_cell", analysis)
        self.assertGreater(analysis["unassigned_count"], 0)
        self.assertGreater(analysis["avg_domain_size"], 0.0)
        self.assertFalse(analysis["contradiction"])
        # E7 or A1 should have valid domain strings
        self.assertTrue(len(analysis["domains"]["A1"]) >= 1)

    # --------------------------------------------------------------------------
    # Milestone 1 Tests: ReasoningStep and Instrumented Propagation
    # --------------------------------------------------------------------------
    def test_m1_reasoning_step_contract_and_trace(self):
        """Verify ReasoningStep dataclass contract and certainty field."""
        step = ReasoningStep(
            step_type="naked_single",
            cell="D7",
            candidates_before="27",
            candidates_after="7",
            value="7",
            related_cells=["D1", "D2"],
            reason="Cell D7 has only one remaining candidate: 7.",
            certainty="deduced",
            contradiction=False
        )
        self.assertEqual(step.certainty, "deduced")
        self.assertFalse(step.contradiction)
        d = step.to_dict()
        self.assertEqual(d["cell"], "D7")

    def test_m1_instrumented_norvig_propagation(self):
        """Verify standalone assign_trace and eliminate_trace capture deduction steps."""
        from src.board import parse_grid
        grid = parse_grid(self.easy_puzzle)
        values, trace = build_propagated_state(grid, record_initial_clues=True)
        self.assertIsNotNone(values)
        self.assertGreater(len(trace), 0)
        # Verify that all recorded steps have certainty == 'deduced'
        for s in trace:
            self.assertEqual(s.certainty, "deduced")

    # --------------------------------------------------------------------------
    # Milestone 2 Tests: Move Checker & Explanation Engine
    # --------------------------------------------------------------------------
    def test_m2_move_checker_cases(self):
        """Verify Case A (immediate peer violation) and Case C (consistent move)."""
        # A3 is '3', so placing '3' in A1 violates Row A / Box 1
        res_a = check_move(self.board, "A1", 3)
        self.assertEqual(res_a["case"], "A")
        self.assertEqual(res_a["status"], "immediate_violation")
        self.assertFalse(res_a["valid"])

        # Placing 4 in A1 has no immediate row/col/box conflict
        res_c = check_move(self.board, "A1", 4)
        self.assertEqual(res_c["case"], "C")
        self.assertEqual(res_c["status"], "valid")
        self.assertTrue(res_c["valid"])

    def test_m2_explanation_engine_3_levels(self):
        """Verify ExplanationEngine produces distinct Socratic, Focused, and Full texts."""
        step = ReasoningStep(
            step_type="naked_single",
            cell="D7",
            candidates_before="7",
            candidates_after="7",
            value="7",
            related_cells=["D1", "D2"],
            reason="Cell D7 has only one remaining candidate: 7.",
            certainty="deduced",
            contradiction=False
        )

        # Level 1: Socratic (unit named, no cell or value)
        exp_l1 = explain_step(step, level=1)
        self.assertEqual(exp_l1["level"], 1)
        self.assertIsNone(exp_l1["cell"])
        self.assertIsNone(exp_l1["value"])
        self.assertIn("Row D", exp_l1["text"])

        # Level 2: Focused (cell named, candidates shown, no direct value assignment)
        exp_l2 = explain_step(step, level=2)
        self.assertEqual(exp_l2["level"], 2)
        self.assertEqual(exp_l2["cell"], "D7")
        self.assertIsNone(exp_l2["value"])
        self.assertIn("Look at D7", exp_l2["text"])

        # Level 3: Full (direct assignment and value)
        exp_l3 = explain_step(step, level=3)
        self.assertEqual(exp_l3["level"], 3)
        self.assertEqual(exp_l3["cell"], "D7")
        self.assertEqual(exp_l3["value"], "7")
        self.assertIn("D7 has to be 7", exp_l3["text"])

    # --------------------------------------------------------------------------
    # Milestone 3 Tests: What-If Simulation and Coach Escalation
    # --------------------------------------------------------------------------
    def test_m3_what_if_zero_board_mutation(self):
        """Verify simulate_move never mutates the original BoardState."""
        orig_str = self.board.get_current_string()
        res = simulate_move(self.board, "A1", 4)
        self.assertTrue(res["success"])
        self.assertFalse(res["board_mutated"])
        # Original board must remain 100% unchanged
        self.assertEqual(self.board.get_current_string(), orig_str)
        self.assertEqual(self.board.get_cell_value("A1"), 0)

    def test_m3_what_if_wrong_digit_shows_real_cascade(self):
        """A legal-but-wrong digit must end in a contradiction somewhere else, reached through forced singles."""
        from sudoku_ai_coach.api.ai_teacher import solve_unique
        from sudoku_ai_coach.api.techniques.utils import compute_live_candidates
        from src.board import SQUARES, SQUARE_TO_COORD
        sol = solve_unique(self.board.initial_puzzle)
        cands = compute_live_candidates(self.board.board.grid)
        cell, digit = next((s, d) for s in SQUARES for d in sorted(cands[s])
                           if int(sol[SQUARE_TO_COORD[s][0] * 9 + SQUARE_TO_COORD[s][1]]) != d)
        res = simulate_move(self.board, cell, digit)
        self.assertFalse(res["success"])
        self.assertTrue(res["contradiction"])
        self.assertNotEqual(res.get("culprit_cell"), cell)
        self.assertTrue(res["cascade_steps"] or res.get("search_proof"))
        if res["cascade_steps"]:
            self.assertTrue(res["cascade_steps"][-1]["contradiction"])
            self.assertTrue(all(s["explanation"] for s in res["cascade_steps"]))

    def test_m3_what_if_immediate_conflict(self):
        """Verify what-if handles immediate conflict gracefully."""
        res = simulate_move(self.board, "A1", 3)
        self.assertFalse(res["success"])
        self.assertTrue(res["contradiction"])
        self.assertIn("Immediate conflict", res["conclusion"])

    def test_m3_adaptive_escalation(self):
        """Verify dialogue escalates through Socratic -> Focused -> Expanded -> Full."""
        session = CoachSession("test_session")
        # Step 1: L1
        h1 = session.get_hint(self.board, escalate=True)
        self.assertEqual(h1["level"], 1)

        # Step 2: L2
        h2 = session.get_hint(self.board, escalate=True)
        self.assertEqual(h2["level"], 2)
        self.assertIsNotNone(h2["cell"])

        # Step 3: L2 Expanded
        h2_exp = session.get_hint(self.board, escalate=True)
        self.assertEqual(h2_exp["level"], 2)

        # Step 4: L3 Full
        h3 = session.get_hint(self.board, escalate=True)
        self.assertEqual(h3["level"], 3)
        self.assertIsNotNone(h3["value"])

    # --------------------------------------------------------------------------
    # Milestone 4 Tests: FastAPI Endpoints
    # --------------------------------------------------------------------------
    def test_m4_api_endpoints(self):
        """Verify all FastAPI routes respond with correct schemas and status codes."""
        # 1. GET /api/board
        r = self.client.get("/api/board")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data["cells"]), 81)

        # 2. GET /api/analyze
        r = self.client.get("/api/analyze")
        self.assertEqual(r.status_code, 200)
        self.assertIn("mrv_cell", r.json())

        # 3. GET /api/hint
        r = self.client.get("/api/hint?level=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["level"], 1)

        # 4. GET /api/explain?cell=A1
        r = self.client.get("/api/explain?cell=A1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["cell"], "A1")

        # 5. POST /api/check-move
        r = self.client.post("/api/check-move", json={"cell": "A1", "value": 3})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["valid"])

        # 6. POST /api/what-if
        r = self.client.post("/api/what-if", json={"cell": "A1", "value": 4})
        self.assertEqual(r.status_code, 200)
        self.assertIn("conclusion", r.json())

        # 7. GET /api/puzzles
        r = self.client.get("/api/puzzles")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.json()["puzzles"]), 0)

        # 8. POST /api/solve
        r = self.client.post("/api/solve")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])
        self.assertEqual(r.json()["solution"], self.easy_solution)



if __name__ == "__main__":
    unittest.main()
