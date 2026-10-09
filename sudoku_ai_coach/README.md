# Explainable Adaptive Sudoku AI Coach

An interactive, explainable artificial intelligence web platform powered by Constraint Satisfaction Problem (CSP) propagation and heuristic search.

---

## 1. Executive Summary & Novelty Framing

> **Core Research Framing**:  
> Most Sudoku-solving projects report which search heuristic is fastest. This project reuses that same reasoning engine to explain its own deductions in real time, distinguish a logically forced move from an untested guess, and let a user test a hypothetical move before committing to it.

Unlike traditional "black-box" solvers that merely compute an output array or machine-learning difficulty estimators that predict probabilities, the **Sudoku AI Coach** is grounded in deterministic constraint deduction. Every hint, warning, and speculative cascade traces directly to formal constraint operations (AllDifferent peer elimination, Naked Singles, Hidden Singles, and Minimum Remaining Values).

---

## 2. Problem Statement & Motivation

Sudoku is an NP-complete combinatorial number-placement problem on an 81-cell grid governed by 27 AllDifferent units. While automated solvers can navigate the $O(9^m)$ search space in milliseconds using AC-3 or Norvig propagation, human players face a steep learning curve when attempting to understand *why* a number must be placed in a specific square.

Most puzzle apps provide unhelpful "hints" that simply spoil the answer without explaining the logical trail, or present canned, hardcoded advice. The **Explainable Adaptive Sudoku AI Coach** bridges this gap:
1. It explains deductions adaptively at three levels of pedagogical depth: Socratic nudge, focused candidate review, or full logical deduction.
2. It classifies every deduction with explicit certainty (`"deduced"` vs `"guessed"`).
3. It validates user moves in real time, catching immediate peer conflicts (Case A) and looking ahead to detect future domain wipeouts (Case B).
4. It provides a **What-If Move Inspector** that simulates hypothetical branches on a sandboxed clone of the board, reporting downstream consequences without altering the player's active grid.

---

## 3. Architecture & Existing CSP Foundation

The AI Coach is built as a clean, non-invasive wrapper on top of the established `src/` constraint engine:

```
Sudokusolver/
├── src/                         # Core CSP Engine (100% Untouched)
│   ├── board.py                 # Norvig notation (A1–I9), UNITS (27), PEERS (20/cell)
│   ├── csp_solver.py            # FC, MRV, LCV, AC-3, and Peter Norvig's dual-rule agent
│   ├── validator.py             # Mathematical AllDifferent constraint validator
│   └── dataset_loader.py        # Kaggle and Synthetic puzzle loaders
│
└── sudoku_ai_coach/             # Explainable Adaptive AI Coach Web Platform
    ├── api/
    │   ├── app.py               # FastAPI application & REST endpoint routes
    │   ├── board_state.py       # BoardState: SudokuBoard wrapper + move history & undo
    │   ├── analyze.py           # analyze_board(): live domain calculation & MRV metrics
    │   ├── reasoning_trace.py   # ReasoningStep dataclass + instrumented Norvig rules
    │   ├── explanation_engine.py# Natural-language templating across 3 hint tiers
    │   ├── hint_engine.py       # Deduction priority: Naked -> Hidden -> MRV
    │   ├── move_checker.py      # Move validation: Case A / Case B / Case C
    │   ├── what_if.py           # Speculative sandbox simulation engine
    │   └── coach_session.py     # Multi-turn escalation state management
    ├── static/
    │   ├── index.html           # 9x9 grid, numpad, and unified coach panel
    │   ├── style.css            # Dark glass design system (responsive)
    │   └── app.js               # Reactive client with conversational escalation & what-if
    ├── tests/
    │   └── test_coach_api.py    # Complete automated unit & integration test suite
    └── README.md                # System documentation
```

### Zero-Touch Guarantee
All original solver and benchmark code in `src/` is untouched. The coach imports `SQUARES`, `UNITS`, `PEERS`, `SudokuBoard`, `CSPSolver`, and `SudokuValidator` directly, respecting the architectural boundaries of the codebase.

---

## 4. Formal Data Model: `ReasoningStep`

Every inference made by the engine produces an immutable, machine-readable `ReasoningStep`:

```python
@dataclass
class ReasoningStep:
    step_type: str                # "naked_single" | "hidden_single" | "elimination" | "contradiction" | "mrv_focus"
    cell: str                     # Norvig square identifier, e.g. "D7"
    candidates_before: str        # Domain string before deduction, e.g. "27"
    candidates_after: str         # Domain string after deduction, e.g. "7"
    value: Optional[str]          # Deduced digit if single, e.g. "7"
    related_cells: List[str]      # Peers or unit members causing this inference
    reason: str                   # Human/machine readable rationale
    certainty: Literal["deduced", "guessed"]   # Exact logic vs speculative branch
    contradiction: bool = False   # True if step triggered a domain wipeout
```

---

## 5. Pedagogical Hint Generation & Adaptive Escalation

The coach provides three tiers of hints designed to foster learning rather than spoiling the answer:

| Tier | Level Name | Pedagogical Purpose | Example Output |
| :--- | :--- | :--- | :--- |
| **Level 1** | **Socratic Nudge** | Directs attention to a constrained unit without revealing the cell or digit. | *"Look at Row D and Box 4. A cell in this section is heavily constrained by its neighbors."* |
| **Level 2** | **Focused Hint** | Identifies the target cell and reveals its remaining candidate possibilities. | *"Focus on D7. It currently has only two possible values: {2, 7}."* |
| **Level 2+**| **Focused (Expanded)**| Explains which peer units forced the candidate eliminations. | *"Column 7 already contains 2. Therefore 2 cannot go in D7, leaving 7."* |
| **Level 3** | **Full Deduction** | Reveals the exact assignment with its mathematical justification. | *"D7 = 7. It is the only remaining legal candidate for this cell."* |

### Escalation Dialogue Flow
When a player interacts sequentially with the coach, the dialogue dynamically escalates on the **same** deduction without re-selecting a random cell:
```
User: "Give me a hint."
AI:   "Look at Row E and Box 5. A cell in this section is heavily constrained by its neighbors."    [Level 1]
User: "Why?"
AI:   "Focus on E6. It currently has only two possible values: {2, 4}."                              [Level 2]
User: "I don't understand."
AI:   "Column 6 already contains 2. Therefore 2 cannot go in E6, leaving 4."                       [Level 2, expanded]
User: "Just tell me."
AI:   "E6 = 4. It is the only remaining legal candidate for this cell."                             [Level 3]
```

---

## 6. The Interactive AI Teacher Hub (CS / CSP Course Professor)

For computer science and AI students who already know how to play Sudoku, the platform includes a dedicated **AI Teacher Mode** designed to teach the underlying theoretical AI search mechanics:

1. **"Teach Me This Step" (Live Algorithmic Dissection)**:
   - **Formal CSP Representation**: Shows the exact mathematical domain formula $D(X^*) = \{1..9\} \setminus \bigcup_{Y \in \text{Peers}(X)} \{\text{val}(Y)\}$.
   - **Algorithmic Technique**: Identifies whether the move uses Forward Checking lookahead, Norvig Rule 1 (Naked Single), Norvig Rule 2 (Unit Hidden Single), or MRV branch selection.
   - **Search Tree Impact**: Computes the exact reduction in branching factor (e.g. *"Branching factor drops from $b=9$ to $b=1$. Node expansions avoided: 15,300"*).
2. **"Test My AI Knowledge" (Socratic AI Quizzes)**:
   - Evaluates the student's mastery of AI concepts in real time based on the active grid (e.g., *"Which cell will the MRV heuristic choose next and why?"*, *"Is this an example of Rule 1 or Rule 2?"*, *"Why does LCV introduce overhead in Sudoku?"*).
   - Provides immediate interactive feedback and pedagogical reinforcement.
3. **5-Step Guided AI Walkthrough**:
   - Compiles a sequential pedagogical trace of how the CSP solver resolves the next 5 moves without mutating the board.
4. **Structured AI Mini-Lecture Curriculum**:
   - 6 built-in textbook reference modules covering CSP formulation $\langle X, D, C \rangle$, Forward Checking, MRV ("Fail-First"), LCV ("Succeed-First") & the LCV Paradox, Peter Norvig's dual propagation rules, and combinatorial search complexity $O(9^m)$.

---

## 7. Move Checker: Case A, B, and C

When a user places or checks a digit in cell $X$, the move checker executes a hierarchical validation:
* **Case A (Immediate Peer Violation)**: Checks if digit $v$ already exists in $X$'s 20 peers (same row, column, or $3 \times 3$ box). If so, rejects immediately and identifies the conflicting cell.
* **Case B (Future Contradiction via Forward Checking)**: Clones candidate domains, tentatively sets $X \leftarrow v$, and performs forward-checking pruning across all unassigned peers. If any peer domain wipes out to $\emptyset$, rejects the move and flags the peer cell that would be starved of candidates.
* **Case C (Consistent Move)**: Confirms that the move satisfies all immediate and forward-checking constraints. Explicitly avoids falsely claiming that the move is guaranteed to be part of the final solution unless verified by a full solve.

---

## 7. What-If Speculative Simulation

The What-If engine (`simulate_move`) provides a sandboxed speculative environment:
```
WHAT IF D7 = 7?
→ D8 loses candidate 7 → D8 becomes {2}.
→ F8 becomes empty.
→ Contradiction detected.
Conclusion: "7 cannot be safely assigned to D7 — it creates a downstream contradiction at F8."
```
* **Safety Contract**: Deep-copies the candidate matrix; the player's active `BoardState` is **never** mutated.

---

## 8. REST API Specification

| Endpoint | Method | Payload / Query | Description |
| :--- | :--- | :--- | :--- |
| `/api/board` | GET | — | Returns current 81-cell board state, clues, and move count |
| `/api/move` | POST | `{cell, value, session_id}` | Applies validated move or clears cell (`value: 0`) |
| `/api/analyze` | GET | — | Live telemetry: candidate domains, MRV cell, singletons |
| `/api/hint` | GET | `?level=1\|2\|3&escalate=true` | Session-aware adaptive hint generation |
| `/api/explain` | GET | `?cell=D7` | Cell-specific constraint and candidate explanation |
| `/api/check-move`| POST | `{cell, value}` | Evaluates move against Cases A, B, and C |
| `/api/what-if` | POST | `{cell, value}` | Sandboxed speculative cascade simulation |
| `/api/undo` | POST | — | Reverts the most recent user move |
| `/api/reset` | POST | — | Restores grid to initial puzzle clues |
| `/api/solve` | POST | — | Full solve via Peter Norvig's CSP propagation agent |
| `/api/puzzles` | GET | — | Preset puzzle catalog (Easy, Medium, Hard, Extreme) |
| `/api/load-puzzle`| POST| `{puzzle, difficulty}` | Loads arbitrary 81-character puzzle string |

---

## 9. How to Run & Verify

### Prerequisites
* Python 3.10+
* Dependencies: `fastapi`, `uvicorn`, `httpx` (installed via pip)

### 1. Launch the AI Coach Server
From the root directory:
```bash
python -m uvicorn sudoku_ai_coach.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://localhost:8000`** in any modern web browser.

### 2. Run Automated Unit Tests
```bash
python -m unittest sudoku_ai_coach/tests/test_coach_api.py
```

### 3. Run Core Solver Tests (Verifying Zero Regressions in `src/`)
```bash
python -m unittest tests/test_solvers.py
```

---

## 10. Limitations & Future Work

1. **Higher-Order Deduction Techniques**: The current explanation engine traces Naked Singles, Hidden Singles, and Forward Checking domain wipeouts. Advanced human techniques such as X-Wings, Swordfish, and Naked Pairs can be formalized as higher-order cycle detection on the constraint graph.
2. **Backtracking Branch Explanations**: When a puzzle has no deterministic singles available, the engine defaults to the Minimum Remaining Values (MRV) heuristic to suggest the most constrained cell. Future extensions could generate full decision-tree proofs demonstrating why alternate branches fail.
3. **Session Persistence**: Currently, sessions are maintained in-memory. Multi-user production environments could store game trees in Redis or SQLite.
