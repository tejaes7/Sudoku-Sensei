"""
Tests for the neuro-symbolic AI Teacher:
intent detection, information gating, offline fallback, and symbolic verification of LLM replies.
"""

import os
import unittest
from unittest import mock

os.environ.setdefault("SUDOKU_GENERATOR_POOL", "0")

from fastapi.testclient import TestClient
from sudoku_ai_coach.api import ai_teacher
from sudoku_ai_coach.api.ai_teacher import detect_intent, extract_claims, teacher_chat, verify_reply, solve_unique
from sudoku_ai_coach.api.app import app, board_state, DEFAULT_PUZZLE
from sudoku_ai_coach.api.board_state import BoardState

PUZZLE = "200080300060070084030500209000105408000000000402706000301007040720040060004010003"
NO_LLM = {"api_key": None, "base_url": "http://unused", "model": "none"}
FAKE_LLM = {"api_key": "test-key", "base_url": "http://fake", "model": "fake-model"}


class TestIntentDetection(unittest.TestCase):

    def test_intents(self):
        self.assertEqual(detect_intent("give me a hint")[0], "hint")
        self.assertEqual(detect_intent("just tell me the answer")[0], "reveal")
        self.assertEqual(detect_intent("what is an X-Wing?")[0], "technique")
        self.assertEqual(detect_intent("explain MRV")[0], "ai_concept")
        self.assertEqual(detect_intent("is this really AI or an API?")[0], "ai_concept")
        intent, slots = detect_intent("what can d7 be?")
        self.assertEqual(intent, "explain_cell")
        self.assertEqual(slots["cell"], "D7")

    def test_cell_and_digit_questions(self):
        intent, slots = detect_intent("why can't 5 go in A1?")
        self.assertEqual((intent, slots["cell"], slots["digit"]), ("cell_digit", "A1", 5))
        # "a 5" is an article and a digit, not cell A5
        intent, slots = detect_intent("can a 5 go in B2?")
        self.assertEqual((intent, slots["cell"], slots["digit"]), ("cell_digit", "B2", 5))
        intent, slots = detect_intent("how was row 3 col 5 filled?")
        self.assertEqual((intent, slots["cell"]), ("explain_cell", "C5"))
        self.assertTrue(slots["wants_answer"])


class TestVerifier(unittest.TestCase):

    def test_extract_claims(self):
        claims = extract_claims("So D7 = 7, put 3 in A2, and 5 goes in B1.")
        self.assertIn(("D7", 7), claims)
        self.assertIn(("A2", 3), claims)
        self.assertIn(("B1", 5), claims)

    def test_rejects_false_claim(self):
        board = BoardState(PUZZLE)
        sol = solve_unique(PUZZLE)
        wrong = 1 if sol[2] != "1" else 2  # A3 is index 2
        check = verify_reply(f"A3 must be {wrong}.", sol, board.board.grid)
        self.assertFalse(check["passed"])
        right = verify_reply(f"A3 must be {sol[2]}.", sol, board.board.grid)
        self.assertTrue(right["passed"])

    def test_hypotheticals_and_negations_are_not_claims(self):
        board = BoardState(PUZZLE)
        sol = solve_unique(PUZZLE)
        wrong = 1 if sol[2] != "1" else 2
        for text in (f"If A3 were {wrong}, Row A would break.", f"You can't put {wrong} in A3.",
                     f"Placing {wrong} in A3 would cause a contradiction."):
            self.assertTrue(verify_reply(text, sol, board.board.grid)["passed"], text)
        # The engine's own What-If pairs are allowed; anything else false is still rejected
        self.assertTrue(verify_reply(f"Then A3 = {wrong}.", sol, board.board.grid, {("A3", wrong)})["passed"])
        self.assertFalse(verify_reply(f"Then A3 = {wrong}.", sol, board.board.grid)["passed"])

    def test_clean_reply_strips_markdown(self):
        self.assertEqual(ai_teacher.clean_reply("**A1** is key.\n* first\n### Note"), "A1 is key.\n- first\nNote")


class TestCellReasoning(unittest.TestCase):
    """'Why can't X go here?' and 'how was this cell filled?' are answered from the engine, not the LLM."""

    def setUp(self):
        self.board = BoardState(PUZZLE)
        self.sol = solve_unique(PUZZLE)
        self.grid = self.board.board.grid
        self.cands = ai_teacher.compute_live_candidates(self.grid)

    def _sol(self, cell):
        r, c = ai_teacher.SQUARE_TO_COORD[cell]
        return int(self.sol[r * 9 + c])

    def _empty_cell_with_choices(self):
        return next(s for s in ai_teacher.SQUARES if len(self.cands[s]) >= 2)

    def test_rule_conflict(self):
        cell = self._empty_cell_with_choices()
        digit = next(d for d in range(1, 10) if d not in self.cands[cell])
        check = ai_teacher.check_digit_in_cell(self.board, cell, digit, self.sol)
        self.assertIn("rule_conflict", check)
        r, c = ai_teacher.SQUARE_TO_COORD[check["rule_conflict"]["conflict_cell"]]
        self.assertEqual(self.grid[r][c], digit)

    def test_wrong_digit_gets_a_contradiction_proof(self):
        cell = self._empty_cell_with_choices()
        digit = next(d for d in sorted(self.cands[cell]) if d != self._sol(cell))
        check = ai_teacher.check_digit_in_cell(self.board, cell, digit, self.sol)
        self.assertTrue(check["verdict"].startswith("legal right now, but wrong"))
        self.assertTrue("what_if" in check or check["search_proof"]["proved_impossible"])
        self.assertNotIn(str(self._sol(cell)), str(check.get("verdict")))  # the right digit is not given away

    def test_correct_digit_and_filled_cell_explained(self):
        cell = next(s for s in ai_teacher.SQUARES if len(self.cands[s]) == 1)
        value = self._sol(cell)
        check = ai_teacher.check_digit_in_cell(self.board, cell, value, self.sol)
        self.assertTrue(check["verdict"].startswith("correct"))
        self.assertTrue(check["reasoning"]["forced_by_a_single_rule"])
        self.board.set_cell_value(cell, value)
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = teacher_chat(self.board, f"how was {cell} filled?")
        self.assertIn("Naked Single", res["reply"])

    def test_empty_cell_answer_is_gated(self):
        cell = self._empty_cell_with_choices()
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = teacher_chat(self.board, f"what can {cell} be?")
        self.assertNotIn("solution_value", res["grounding"]["focus_cell"])
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = teacher_chat(self.board, f"how do I fill {cell}?")
        self.assertEqual(res["grounding"]["focus_cell"]["solution_value"], self._sol(cell))


class TestTeacherChat(unittest.TestCase):

    def setUp(self):
        self.board = BoardState(PUZZLE)

    def test_offline_fallback_answers(self):
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = teacher_chat(self.board, "give me a hint")
        self.assertEqual(res["source"], "engine")
        self.assertTrue(res["reply"])
        self.assertTrue(res["highlight_cause_cells"])

    def test_hint_does_not_leak_answer(self):
        """Information gating: the answer digit is never sent to the LLM for a plain hint."""
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = teacher_chat(self.board, "give me a hint")
        self.assertNotIn("target_value", res["grounding"]["next_deduction"])
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = teacher_chat(self.board, "just tell me")
        self.assertIn("target_value", res["grounding"]["next_deduction"])

    def test_llm_reply_accepted_when_verified(self):
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=FAKE_LLM), \
             mock.patch.object(ai_teacher, "call_llm", return_value="Look at Box 2 and ask which digit is missing."):
            res = teacher_chat(self.board, "give me a hint")
        self.assertEqual(res["source"], "llm")
        self.assertTrue(res["verification"]["passed"])

    def test_hallucinated_llm_reply_is_rejected(self):
        sol = solve_unique(PUZZLE)
        wrong = 1 if sol[2] != "1" else 2
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=FAKE_LLM), \
             mock.patch.object(ai_teacher, "call_llm", return_value=f"Easy: A3 = {wrong}."):
            res = teacher_chat(self.board, "just tell me")
        self.assertEqual(res["source"], "engine")
        self.assertTrue(res["llm_rejected"])
        self.assertIn(f"A3={wrong}", res["verification"]["rejected_claims"])

    def test_llm_failure_falls_back(self):
        import httpx
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=FAKE_LLM), \
             mock.patch.object(ai_teacher, "call_llm", side_effect=httpx.ConnectError("down")):
            res = teacher_chat(self.board, "what is MRV?")
        self.assertEqual(res["source"], "engine")
        self.assertIn("Minimum Remaining Values", res["reply"])


class TestTeacherChatEndpoint(unittest.TestCase):

    def tearDown(self):
        board_state.load_puzzle(DEFAULT_PUZZLE)

    def test_chat_endpoint(self):
        client = TestClient(app)
        client.post("/api/load-puzzle", json={"puzzle": PUZZLE})
        with mock.patch.object(ai_teacher, "get_llm_config", return_value=NO_LLM):
            res = client.post("/api/teacher/chat", json={"message": "what can E5 be?"})
            status = client.get("/api/teacher/ai-status").json()
        self.assertEqual(res.status_code, 200)
        self.assertIn("E5", res.json()["reply"])
        self.assertFalse(status["llm_enabled"])


if __name__ == "__main__":
    unittest.main()
