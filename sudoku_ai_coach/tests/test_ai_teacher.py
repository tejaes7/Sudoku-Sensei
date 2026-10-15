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
