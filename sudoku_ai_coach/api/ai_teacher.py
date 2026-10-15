"""
AI Teacher Module (neuro-symbolic tutor):
A conversational Sudoku teacher in which the symbolic CSP engine does the reasoning and a
large language model only does the talking.

Pipeline for every chat message:
  1. Intent detection     - classify what the learner is asking (hint, reveal, cell, technique, AI concept...).
  2. Symbolic grounding   - run the CSP / technique engine on the live board to collect verified facts
                            (candidates, next deduction chain, mistakes, unique solution).
  3. Information gating   - only facts the learner is allowed to see go to the LLM; the answer digit is
                            withheld unless they explicitly ask for it, so the tutor cannot spoil it.
  4. LLM explanation      - an OpenAI-compatible chat model turns the facts into a friendly lesson.
  5. Symbolic verification- every "cell = digit" claim in the reply is checked against the solver's
                            unique solution; a reply with a false claim is rejected.
  6. Fallback             - with no API key, a timeout, or a rejected reply, the engine answers with its
                            own templated explanation, so the teacher always works offline.

Configuration (environment variables or a `.env` file in the project root):
  AI_TEACHER_API_KEY   API key for any OpenAI-compatible provider (OPENAI_API_KEY / GROQ_API_KEY also accepted)
  AI_TEACHER_BASE_URL  e.g. https://api.openai.com/v1, https://api.groq.com/openai/v1,
                       https://generativelanguage.googleapis.com/v1beta/openai, https://openrouter.ai/api/v1
  AI_TEACHER_MODEL     e.g. gpt-4o-mini, llama-3.3-70b-versatile, gemini-2.0-flash
"""

import copy
import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.board import SQUARES, PEERS, UNITS, SQUARE_TO_COORD, parse_grid
from src.csp_solver import CSPSolver
from .board_state import BoardState
from .hint_ladder import find_user_mistakes, build_deduction_chain, TIER_RANK
from .move_checker import generate_why_it_works
from .what_if import singles_cascade, search_proof
from .techniques.utils import compute_live_candidates, format_unit_friendly

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
LLM_TIMEOUT_SEC = 20.0
MAX_HISTORY = 6


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
def _read_dotenv() -> Dict[str, str]:
    """Minimal .env reader (KEY=VALUE lines) so no extra dependency is needed."""
    path = os.path.join(PROJECT_ROOT, ".env")
    values: Dict[str, str] = {}
    if not os.path.isfile(path):
        return values
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def get_llm_config() -> Dict[str, Optional[str]]:
    env = {**_read_dotenv(), **os.environ}
    api_key = env.get("AI_TEACHER_API_KEY") or env.get("OPENAI_API_KEY") or env.get("GROQ_API_KEY")
    return {
        "api_key": api_key or None,
        "base_url": (env.get("AI_TEACHER_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"),
        "model": env.get("AI_TEACHER_MODEL") or DEFAULT_MODEL,
    }


def teacher_status() -> Dict[str, Any]:
    cfg = get_llm_config()
    return {
        "llm_enabled": bool(cfg["api_key"]),
        "model": cfg["model"] if cfg["api_key"] else None,
        "mode": "neuro-symbolic (CSP engine + LLM)" if cfg["api_key"] else "symbolic (CSP engine only)",
    }


# --------------------------------------------------------------------------
# 1. Intent detection
# --------------------------------------------------------------------------
CELL_RE = re.compile(r"\b([A-I])\s?([1-9])\b")      # "D7" or "D 7"
CELL_RE_LOWER = re.compile(r"\b([a-i])([1-9])\b")  # "d7" only, so "can a 5 go..." is not read as cell A5
RC_RE = re.compile(r"\br(?:ow)?\s*([1-9])\s*,?\s*c(?:ol(?:umn)?)?\s*([1-9])\b", re.I)  # "r3c5", "row 3 col 5"
DIGIT_RE = re.compile(r"(?<![A-Za-z0-9])([1-9])(?![0-9])")
WANTS_ANSWER_WORDS = ["how", "why", "fill", "what goes", "answer", "solve", "reveal", "just tell", "which number",
                      "what number", "value"]


def find_cell(message: str) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    """Return the first cell mentioned (Norvig notation) and its span in the message."""
    m = CELL_RE.search(message) or CELL_RE_LOWER.search(message)
    if m:
        return (m.group(1) + m.group(2)).upper(), m.span()
    m = RC_RE.search(message)
    if m:
        return "ABCDEFGHI"[int(m.group(1)) - 1] + m.group(2), m.span()
    return None, None


def find_digit(message: str, cell_span: Tuple[int, int]) -> Optional[int]:
    """A standalone digit 1-9 in the message, ignoring the cell reference itself."""
    rest = message[:cell_span[0]] + " " + message[cell_span[1]:]
    m = DIGIT_RE.search(rest)
    return int(m.group(1)) if m else None

TECHNIQUE_KEYWORDS = {
    "full_house": ["full house"],
    "naked_single": ["naked single"],
    "hidden_single": ["hidden single"],
    "naked_pair": ["naked pair"],
    "hidden_pair": ["hidden pair"],
    "pointing_pair": ["pointing pair", "pointing"],
    "box_line_reduction": ["box/line", "box line", "box-line", "claiming"],
    "naked_triple": ["naked triple", "triple"],
    "x_wing": ["x-wing", "x wing", "xwing"],
}

AI_CONCEPT_KEYWORDS = {
    "csp": ["csp", "constraint satisfaction", "constraint"],
    "mrv": ["mrv", "minimum remaining", "fail-first", "fail first"],
    "forward_checking": ["forward checking", "forward-checking"],
    "ac3": ["ac-3", "ac3", "arc consistency", "arc-consistency"],
    "lcv": ["lcv", "least constraining"],
    "backtracking": ["backtrack", "search tree", "dfs", "depth first"],
    "norvig": ["norvig", "propagation"],
    "how_it_works": ["are you ai", "is this ai", "really ai", "how do you work", "how does this work",
                     "how do you think", "are you an api", "what ai", "which ai", "chatgpt", "llm",
                     "how are you built", "who are you", "what are you"],
}


def detect_intent(message: str) -> Tuple[str, Dict[str, Any]]:
    """Rule-based intent classifier. Returns (intent, slots)."""
    text = message.lower().strip()
    slots: Dict[str, Any] = {}

    # Questions about a specific cell come first: "why can't 5 go in A1?", "how was B3 filled?", "what can D7 be?"
    cell, span = find_cell(message)
    if cell:
        slots["cell"] = cell
        digit = find_digit(message, span)
        if digit:
            slots["digit"] = digit
            return "cell_digit", slots
        slots["wants_answer"] = any(w in text for w in WANTS_ANSWER_WORDS)
        return "explain_cell", slots

    for concept, words in AI_CONCEPT_KEYWORDS.items():
        if any(w in text for w in words):
            slots["concept"] = concept
            return "ai_concept", slots

    for tech_id, words in TECHNIQUE_KEYWORDS.items():
        if any(w in text for w in words):
            slots["technique"] = tech_id
            return "technique", slots

    if any(w in text for w in ["just tell", "the answer", "give me the answer", "reveal", "show me the move",
                               "what goes", "solve it for me", "tell me the move"]):
        return "reveal", slots

    if any(w in text for w in ["mistake", "wrong", "error", "did i mess", "is my board", "check my"]):
        return "mistake", slots

    if any(w in text for w in ["hint", "stuck", "help", "next", "where", "what should", "what now", "clue"]):
        return "hint", slots

    if any(w in text for w in ["why", "don't understand", "dont understand", "confused", "explain", "how"]):
        return "explain_step", slots

    return "general", slots


# --------------------------------------------------------------------------
# 2. Symbolic grounding
# --------------------------------------------------------------------------
@lru_cache(maxsize=32)
def solve_unique(initial_puzzle: str) -> Optional[str]:
    tel = CSPSolver(propagation="norvig", timeout_sec=3.0).solve(initial_puzzle)
    return tel.solution if tel.solved else None


def _cell_value(grid: List[List[int]], sq: str) -> int:
    r, c = SQUARE_TO_COORD[sq]
    return grid[r][c]


def describe_cell(grid: List[List[int]], candidates: Dict[str, set], cell: str, is_clue: bool) -> Dict[str, Any]:
    value = _cell_value(grid, cell)
    units = []
    for unit in UNITS[cell]:
        seen = sorted({_cell_value(grid, sq) for sq in unit if sq != cell and _cell_value(grid, sq)})
        units.append({"unit": format_unit_friendly(unit), "digits_present": seen})
    return {
        "cell": cell,
        "filled_value": value or None,
        "is_starting_clue": is_clue,
        "candidates": sorted(candidates.get(cell, set())),
        "units": units,
    }


def _with_cell_cleared(board_state: BoardState, cell: str) -> BoardState:
    """A copy of the board with `cell` emptied, so we can reason about how it gets filled."""
    clone = copy.deepcopy(board_state)
    r, c = SQUARE_TO_COORD[cell]
    clone.board.grid[r][c] = 0
    return clone


def _why(board_state: BoardState, cell: str, value: int) -> Dict[str, Any]:
    why = generate_why_it_works(board_state, cell, value)
    return {"technique": why["technique"], "forced_by_a_single_rule": why["forced"], "steps": why["steps"]}


def explain_filled_or_empty(board_state: BoardState, cell: str, solution: Optional[str],
                            wants_answer: bool) -> Dict[str, Any]:
    """How a filled cell got its value, or how an empty cell can be filled (answer gated by `wants_answer`)."""
    r, c = SQUARE_TO_COORD[cell]
    value = board_state.board.grid[r][c]
    correct = int(solution[r * 9 + c]) if solution else None
    if board_state.is_clue(cell):
        return {"how_filled": "It is a starting clue given by the puzzle, so it needs no deduction."}
    if value:
        if correct is not None and value != correct:
            return {"how_filled": "Filled by the learner, but it does NOT match the unique solution (a mistake)."}
        return {"how_filled": "Filled by the learner and correct. The reasoning that forces it (with the cell emptied):",
                "reasoning": _why(_with_cell_cleared(board_state, cell), cell, value)}
    if correct is None:
        return {}
    why = _why(board_state, cell, correct)
    if wants_answer:
        return {"how_to_fill": why, "solution_value": correct}
    # Gated: say whether a single rule forces it right now and which, but not the digit
    return {"how_to_fill": {"forced_by_a_single_rule": why["forced_by_a_single_rule"], "technique": why["technique"]}}


def check_digit_in_cell(board_state: BoardState, cell: str, digit: int, solution: Optional[str]) -> Dict[str, Any]:
    """Can `digit` go in `cell`? Rule conflict, correct (with the forcing reason), or a What-If contradiction chain."""
    r, c = SQUARE_TO_COORD[cell]
    current = board_state.board.grid[r][c]
    facts: Dict[str, Any] = {"cell": cell, "digit": digit}
    if board_state.is_clue(cell):
        facts["verdict"] = (f"{cell} is a starting clue fixed as {current}, so it can only ever be {current}."
                            if current != digit else f"{cell} is a starting clue and it is {digit}.")
        return facts
    work = _with_cell_cleared(board_state, cell) if current else board_state
    if current:
        facts["currently_filled_with"] = current

    grid = work.board.grid
    for peer in PEERS[cell]:
        pr, pc = SQUARE_TO_COORD[peer]
        if grid[pr][pc] == digit:
            unit = next(u for u in UNITS[cell] if peer in u)
            facts["verdict"] = "impossible: breaks the rules"
            facts["rule_conflict"] = {"conflict_cell": peer, "unit": format_unit_friendly(unit),
                                      "explanation": f"{peer} in {format_unit_friendly(unit)} already holds {digit}, "
                                                     f"and a digit may appear only once per row, column and box."}
            return facts

    if solution and int(solution[r * 9 + c]) == digit:
        facts["verdict"] = "correct: this is the digit in the unique solution"
        facts["reasoning"] = _why(work, cell, digit)
        return facts

    facts["verdict"] = "legal right now, but wrong: it is not in the unique solution"
    chain = contradiction_chain(work.board.grid, cell, digit)
    if chain:
        steps = chain["chain"]
        if len(steps) > 8:  # keep the explanation readable: the first steps, then the last ones before the contradiction
            chain["chain"] = steps[:5] + [{"cell": "...", "value": None, "rule": "",
                                           "reason": f"{len(steps) - 8} more forced singles"}] + steps[-3:]
        facts["what_if"] = chain
    else:
        facts["search_proof"] = search_proof(work.board.grid, cell, digit)
    return facts


RULE_NAMES = {"naked_single": "Naked Single", "hidden_single": "Hidden Single"}


def contradiction_chain(grid: List[List[int]], cell: str, digit: int) -> Optional[Dict[str, Any]]:
    """The What-If engine's singles cascade from cell = digit, if it ends in a contradiction."""
    cascade = singles_cascade(grid, cell, digit)
    if not cascade["contradiction"]:
        return None
    *forced, last = cascade["steps"]
    return {"chain": [{"cell": s["cell"], "value": s["value"], "rule": RULE_NAMES[s["step_type"]], "reason": s["reason"]}
                      for s in forced],
            "culprit_cell": cascade["culprit_cell"], "contradiction": last["reason"]}



def build_grounding(board_state: BoardState, intent: str, slots: Dict[str, Any],
                    selected_cell: Optional[str], user_level: str) -> Dict[str, Any]:
    """Collect engine-verified facts about the live board. Every fact here is computed, not generated."""
    grid = board_state.board.grid
    initial = board_state.initial_puzzle
    solution = solve_unique(initial)
    candidates = compute_live_candidates(grid)
    empty = [s for s in SQUARES if not _cell_value(grid, s)]

    facts: Dict[str, Any] = {
        "empty_cells": len(empty),
        "learner_level": user_level,
        "solved": not empty,
    }

    mistake = find_user_mistakes(grid, initial, solution)
    if mistake:
        facts["mistake"] = {
            "cell": mistake["mistake_cell"],
            "conflicting_cell": mistake.get("conflicting_cell"),
            "type": mistake["mistake_type"],
            "explanation": mistake["explanation"],
        }

    if empty:
        mrv = min(empty, key=lambda s: len(candidates[s]))
        facts["most_constrained_cell"] = {"cell": mrv, "candidate_count": len(candidates[mrv])}
        if intent == "reveal" or len(candidates[mrv]) > 1:
            # A single candidate would give the answer away, so it is only shared when the learner asks for it
            facts["most_constrained_cell"]["candidates"] = sorted(candidates[mrv])

    if empty and not mistake:
        chain = build_deduction_chain(grid, user_level)
        if chain:
            key = max(chain, key=lambda st: TIER_RANK[st.difficulty_tier])
            final = chain[-1]
            places = final.target_value is not None and len(final.target_cells) == 1
            step = {
                "technique": key.technique_name,
                "tier": key.difficulty_tier,
                "definition": key.definition,
                "where_to_look": key.nudge_text,
                "unit": key.unit_name,
                "cause_cells": key.cause_cells[:8],
                "chain_length": len(chain),
            }
            # Information gating: the explanation and the answer are only shared when asked for.
            if intent in ("reveal", "explain_step"):
                step["technique_explanation"] = key.technique_text
            if intent == "reveal":
                step["target_cells"] = final.target_cells if places else key.target_cells
                step["target_value"] = final.target_value if places else None
                step["eliminations"] = {k: v for st in chain for k, v in (st.eliminations or {}).items()}
                step["walkthrough"] = [w for st in chain for w in st.walkthrough_steps]
            facts["next_deduction"] = step

    focus = slots.get("cell") or selected_cell
    if focus in SQUARES:
        r, c = SQUARE_TO_COORD[focus]
        facts["focus_cell"] = describe_cell(grid, candidates, focus, board_state.is_clue(focus))
        if intent == "reveal" and solution:
            facts["focus_cell"]["solution_value"] = int(solution[r * 9 + c])
        if intent == "explain_cell":
            facts["focus_cell"].update(
                explain_filled_or_empty(board_state, focus, solution, slots.get("wants_answer", False)))

    if intent == "cell_digit":
        facts["digit_check"] = check_digit_in_cell(board_state, slots["cell"], slots["digit"], solution)

    return facts


# --------------------------------------------------------------------------
# 5. Symbolic verification of LLM output
# --------------------------------------------------------------------------
CLAIM_PATTERNS = [
    re.compile(r"\b([A-I][1-9])\s*(?:=|must be|is a|is an|is|should be|becomes|gets|will be|has to be)\s*(?:a\s+|an\s+)?([1-9])\b"),
    re.compile(r"\b(?:put|place|write|enter|fill in)\s+(?:a\s+|an\s+)?([1-9])\s+(?:in|into|at)\s+(?:cell\s+)?([A-I][1-9])\b", re.I),
    re.compile(r"\b([1-9])\s+(?:goes|belongs|must go)\s+(?:in|into|at)\s+(?:cell\s+)?([A-I][1-9])\b", re.I),
]


# A claim inside a hypothetical ("if D7 were 5...", "placing 5 in D7 would...") or a negation ("D7 is not 5")
# is not an assertion about the solution, so it is not checked.
HYPOTHETICAL_BEFORE = re.compile(r"\b(if|suppose|supposing|assume|assuming|imagine|were|try|trying|tried|placing|"
                                 r"putting|what if)\b[^.!?,;]{0,40}$", re.I)
NEGATION_BEFORE = re.compile(r"\b(not|cannot|can't|never|don't|do not|shouldn't|won't)\s+(?:\w+\s+)?$", re.I)
HYPOTHETICAL_AFTER = re.compile(r"^[^.!?,;]{0,25}\b(would|leads?|causes?|creates?|breaks?|fails?)\b", re.I)


def extract_claims(text: str, skip_hypothetical: bool = False) -> List[Tuple[str, int]]:
    claims: List[Tuple[str, int]] = []
    for i, pat in enumerate(CLAIM_PATTERNS):
        for m in pat.finditer(text):
            before, after = text[:m.start()], text[m.end():]
            if skip_hypothetical and (HYPOTHETICAL_BEFORE.search(before) or NEGATION_BEFORE.search(before)
                                      or HYPOTHETICAL_AFTER.search(after)):
                continue
            cell, digit = (m.group(1), m.group(2)) if i == 0 else (m.group(2), m.group(1))
            claims.append((cell.upper(), int(digit)))
    return claims


def verify_reply(text: str, solution: Optional[str], grid: List[List[int]],
                 hypotheticals: Optional[set] = None) -> Dict[str, Any]:
    """Check every 'cell = digit' assertion against the solver's unique solution.
    `hypotheticals` are (cell, digit) pairs the engine itself is reasoning about (e.g. a What-If chain)."""
    claims = extract_claims(text, skip_hypothetical=True)
    rejected = []
    if solution:
        for cell, digit in claims:
            r, c = SQUARE_TO_COORD[cell]
            if (cell, digit) in (hypotheticals or set()):
                continue
            if int(solution[r * 9 + c]) != digit and grid[r][c] != digit:
                rejected.append(f"{cell}={digit}")
    return {"claims_checked": len(claims), "rejected_claims": rejected, "passed": not rejected}


def hypothetical_claims(facts: Dict[str, Any]) -> set:
    """(cell, digit) pairs that appear in the engine's own What-If reasoning, so the LLM may repeat them."""
    check = facts.get("digit_check") or {}
    pairs = set()
    if "digit" in check:
        pairs.add((check["cell"], check["digit"]))
    for step in (check.get("what_if") or {}).get("chain", []):
        if step.get("value"):
            try:
                pairs.add((step["cell"], int(step["value"])))
            except (TypeError, ValueError):
                pass
    return pairs


# --------------------------------------------------------------------------
# 4. LLM explanation layer
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a warm, patient Sudoku teacher inside an explainable AI tutoring app.
A symbolic Constraint Satisfaction Problem (CSP) engine has already analysed the learner's board.
You receive its verified facts as JSON. Rules:
- Use ONLY the facts provided. Never invent candidates, cell values or deductions.
- If a fact you need is missing (for example the answer digit), do not guess it. Guide the learner to find it.
- Teach, don't just tell: point to the row/column/box, ask a guiding question, then explain the logic.
- Cells use Norvig notation: the LETTER is the row (A-I, top to bottom) and the NUMBER is the column (1-9, left
  to right). So E3 is Row E, Column 3 - never say "row 3" or "column E".
- If a mistake is listed, address it kindly before anything else.
- If "digit_check" is present, the learner asked whether a digit can go in a cell. Give the verdict first, then the
  reason: name the conflicting cell and its row/column/box for a rule conflict; walk through "reasoning.steps" when
  the digit is correct; for a wrong digit, walk through the "what_if.chain" (the cascade that ends in a
  contradiction, given in "what_if.contradiction") as a hypothetical ("if it were...") and never state the correct
  digit unless it is provided.
  If there is no "what_if" chain, use "search_proof" instead. Never invent deduction steps that are not in
  the facts; if the facts don't show the exact chain, say the solver proved it by search.
- If "focus_cell" has "how_filled", "reasoning" or "how_to_fill", explain how that cell is (or can be) filled by
  walking through those steps in order. Only give the digit of an empty cell if "solution_value" is provided.
- For questions that are not about this board or AI, answer briefly and kindly steer back to the puzzle.
- Keep replies under 150 words, plain text, no markdown headings or tables.
- For questions about AI concepts (CSP, MRV, forward checking, AC-3, LCV, backtracking), explain them at a
  university-intro level and connect them to the current board when possible.
- If asked how you work: the CSP engine does all reasoning and checking; you (the language model) only
  phrase the explanation, and your answers are verified against the solver before being shown."""


def call_llm(message: str, facts: Dict[str, Any], history: List[Dict[str, str]],
             cfg: Dict[str, Optional[str]]) -> str:
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-MAX_HISTORY:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": str(turn["content"])[:1000]})
    messages.append({
        "role": "user",
        "content": f"VERIFIED ENGINE FACTS (JSON):\n{json.dumps(facts)}\n\nLEARNER: {message}",
    })
    body: Dict[str, Any] = {"model": cfg["model"], "messages": messages, "temperature": 0.4, "max_tokens": 900}
    if "gpt-oss" in cfg["model"]:
        body["reasoning_effort"] = "low"  # reasoning models: keep hidden thinking short so the reply is fast
    resp = httpx.post(
        f"{cfg['base_url']}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
        json=body,
        timeout=LLM_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    return clean_reply(resp.json()["choices"][0]["message"]["content"])


def clean_reply(text: str) -> str:
    """The chat bubble shows plain text, so drop markdown emphasis and turn '*' bullets into '-'."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?m)^(\s*)\*\s+", r"\1- ", text)
    text = re.sub(r"(?m)^#+\s*", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# --------------------------------------------------------------------------
# 6. Symbolic fallback answers (no LLM needed)
# --------------------------------------------------------------------------
AI_CONCEPT_ANSWERS = {
    "csp": "Sudoku is a Constraint Satisfaction Problem ⟨X, D, C⟩: 81 variables (A1–I9), each with domain {1..9}, "
           "and 27 AllDifferent constraints (9 rows, 9 columns, 9 boxes). Each cell has 20 peers it must differ from. "
           "Every hint I give is a deduction over these constraints.",
    "mrv": "MRV (Minimum Remaining Values, or 'fail-first') picks the variable with the smallest domain next. "
           "A cell with 1–2 candidates is the most likely to fail, so choosing it prunes dead branches near the root.",
    "forward_checking": "Forward checking: after assigning a cell, remove that digit from the domains of its 20 peers. "
                        "If any peer's domain becomes empty, the assignment is rejected immediately instead of failing deep in the search.",
    "ac3": "AC-3 makes every arc (Xi, Xj) consistent: each value in Xi's domain must leave some value for Xj. "
           "Whenever a domain shrinks, the arcs pointing into it are re-checked. It prunes more than forward checking, at a higher cost per node.",
    "lcv": "LCV (Least Constraining Value) tries the value that removes the fewest options from neighbours first. "
           "In Sudoku it often doesn't pay off: once MRV picks a cell it usually has only 1–2 values, so ordering them barely helps.",
    "backtracking": "Backtracking search is depth-first search over assignments: pick a cell, try a value, propagate, "
                    "and undo (backtrack) on contradiction. Propagation and heuristics are what make it fast enough.",
    "norvig": "Norvig's solver uses two propagation rules: (1) if a cell has one candidate, remove it from its peers; "
              "(2) if a digit has only one possible place in a unit, put it there. Then it searches with MRV. "
              "Rules (1) and (2) are exactly the Naked Single and Hidden Single I teach.",
    "how_it_works": "I'm a neuro-symbolic AI teacher. A CSP engine (constraint propagation, MRV search, and a rule base of "
                    "9 human techniques from Full House to X-Wing) does all the reasoning on your board. When a language model "
                    "is connected it only phrases the explanation, and every 'cell = digit' it says is checked against the "
                    "solver before you see it. Without a model I explain using the engine's own templates.",
}


TECHNIQUE_GLOSSARY = {
    "full_house": ("Full House", "A row, column or box has exactly one empty square left, so it takes the one missing digit."),
    "naked_single": ("Naked Single", "A square's row, column and box already contain eight different digits, so only one candidate remains."),
    "hidden_single": ("Hidden Single", "Inside a row, column or box, a digit fits in only one square, even if that square has other candidates."),
    "naked_pair": ("Naked Pair", "Two squares in a unit have the same two candidates, so those two digits can be removed from every other square in that unit."),
    "hidden_pair": ("Hidden Pair", "Two digits can only go in the same two squares of a unit, so all other candidates can be removed from those two squares."),
    "pointing_pair": ("Pointing Pair", "Inside a box, a digit is confined to one row or column, so it can be removed from the rest of that row or column outside the box."),
    "box_line_reduction": ("Box/Line Reduction", "Inside a row or column, a digit is confined to one box, so it can be removed from the rest of that box."),
    "naked_triple": ("Naked Triple", "Three squares in a unit hold only three digits between them, so those digits leave every other square in the unit."),
    "x_wing": ("X-Wing", "A digit appears in exactly two squares in each of two rows, in the same two columns. It must sit on opposite corners of that rectangle, so it is removed from the rest of those columns."),
}


def digit_check_reply(check: Dict[str, Any]) -> str:
    cell, digit = check["cell"], check["digit"]
    verdict = check.get("verdict", "")
    if "rule_conflict" in check:
        return f"No, {digit} can't go in {cell}. {check['rule_conflict']['explanation']}"
    if verdict.startswith("correct"):
        steps = check["reasoning"]["steps"]
        return f"Yes, {digit} belongs in {cell}. " + " ".join(steps)
    msg = f"{digit} doesn't break a rule in {cell} right now, but it's wrong. "
    if "what_if" in check:
        w = check["what_if"]
        steps = " ".join(f"Then {s['reason']}, so it would be {s['value']} ({s['rule']})." if s["value"]
                         else f"({s['reason']}.)" for s in w["chain"])
        return msg + (f"Suppose {cell} were {digit}. {steps} But now {w['contradiction']} "
                      f"That's a contradiction, so {digit} can't go in {cell}.")
    if check.get("search_proof", {}).get("explanation"):
        return msg + check["search_proof"]["explanation"]
    return verdict


def fallback_reply(intent: str, slots: Dict[str, Any], facts: Dict[str, Any]) -> str:
    if intent == "cell_digit" and facts.get("digit_check"):
        return digit_check_reply(facts["digit_check"])
    if facts.get("mistake"):
        m = facts["mistake"]
        return f"Let's fix one thing first. {m['explanation']}"
    if facts.get("solved"):
        return "The puzzle is solved. Brilliant work! Load a new one when you're ready."

    if intent == "ai_concept":
        return AI_CONCEPT_ANSWERS[slots["concept"]]

    step = facts.get("next_deduction")
    focus = facts.get("focus_cell")

    if intent == "technique":
        name, definition = TECHNIQUE_GLOSSARY[slots["technique"]]
        if step and step["technique"].lower() == name.lower():
            return f"{name}: {definition} There's one on the board right now. {step['where_to_look']}"
        return f"{name}: {definition} It isn't the next step on this board, but I'll point it out when it is."

    if intent == "cell_digit" and facts.get("digit_check"):
        return digit_check_reply(facts["digit_check"])

    if intent == "explain_cell" and focus:
        if focus["filled_value"]:
            head = f"{focus['cell']} holds {focus['filled_value']}. {focus.get('how_filled', '')}"
            steps = (focus.get("reasoning") or {}).get("steps", [])
            return " ".join([head] + steps).strip()
        seen = "; ".join(f"{u['unit']} has {', '.join(map(str, u['digits_present'])) or 'nothing yet'}" for u in focus["units"])
        cands = focus["candidates"]
        tail = f"so {focus['cell']} can only be {', '.join(map(str, cands))}."
        if len(cands) == 1:
            tail = f"so only {cands[0]} is left. That's a Naked Single!"
        reply = f"Let's look at what {focus['cell']} can see: {seen}. That rules out every other digit, {tail}"
        how = focus.get("how_to_fill") or {}
        if how.get("steps"):
            reply += " " + " ".join(how["steps"])
        elif how and len(cands) > 1:
            reply += (f" Right now it's forced by a {how['technique']}. Ask me 'how do I fill {focus['cell']}?' for the steps."
                      if how.get("forced_by_a_single_rule") else
                      " No single rule forces it yet, so it can't be filled safely right now. Fill other cells first.")
        return reply

    if not step:
        return "No standard technique applies right now. Try a speculative move with What-If, or check your pencil marks."

    if intent == "reveal":
        target = ", ".join(step.get("target_cells") or [])
        if step.get("target_value"):
            walk = " ".join(step.get("walkthrough", [])[:4])
            return f"{target} = {step['target_value']}. {walk}"
        return f"This step is an elimination ({step['technique']}). {step.get('technique_explanation', '')}"

    if intent == "explain_step":
        return f"The next step uses {step['technique']}. {step['definition']} {step.get('technique_explanation', '')}"

    if intent == "hint":
        return f"{step['where_to_look']} Ask me 'why?' when you want the technique, or 'just tell me' for the answer."

    return ("I'm your Sudoku teacher. Ask me for a hint, ask about a cell like 'what can D7 be?', "
            "ask what an X-Wing is, or ask how the AI behind me works.")


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def teacher_chat(board_state: BoardState, message: str, history: Optional[List[Dict[str, str]]] = None,
                 selected_cell: Optional[str] = None, user_level: str = "intermediate") -> Dict[str, Any]:
    intent, slots = detect_intent(message)
    facts = build_grounding(board_state, intent, slots, selected_cell, user_level)
    cfg = get_llm_config()

    highlight_cause: List[str] = []
    highlight_target: List[str] = []
    if facts.get("mistake"):
        highlight_target = [facts["mistake"]["cell"]]
        if facts["mistake"].get("conflicting_cell"):
            highlight_cause = [facts["mistake"]["conflicting_cell"]]
    elif facts.get("digit_check"):
        dc = facts["digit_check"]
        highlight_target = [dc["cell"]]
        if "rule_conflict" in dc:
            highlight_cause = [dc["rule_conflict"]["conflict_cell"]]
        elif dc.get("what_if", {}).get("culprit_cell"):
            highlight_cause = [dc["what_if"]["culprit_cell"]]
    elif facts.get("next_deduction") and intent in ("hint", "explain_step", "reveal", "technique"):
        highlight_cause = facts["next_deduction"]["cause_cells"]
        highlight_target = facts["next_deduction"].get("target_cells", [])
    elif facts.get("focus_cell"):
        highlight_target = [facts["focus_cell"]["cell"]]

    result: Dict[str, Any] = {
        "intent": intent,
        "grounding": facts,
        "highlight_cause_cells": highlight_cause,
        "highlight_target_cells": highlight_target,
    }

    if cfg["api_key"]:
        try:
            reply = call_llm(message, facts, history or [], cfg)
            check = verify_reply(reply, solve_unique(board_state.initial_puzzle), board_state.board.grid,
                                 hypothetical_claims(facts))
            if check["passed"]:
                return {**result, "reply": reply, "source": "llm", "model": cfg["model"], "verification": check}
            result["verification"] = check
            result["llm_rejected"] = True
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            result["llm_error"] = type(e).__name__

    return {**result, "reply": fallback_reply(intent, slots, facts), "source": "engine", "model": None}
