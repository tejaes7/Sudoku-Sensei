"""
Puzzle Generator Module:
Generates fresh, uniquely-solvable Sudoku puzzles graded to a learner's level.

Strategy ("dig with a human solver"):
  1. Build a random complete grid with randomized backtracking.
  2. Visit cells in random order and blank each one, keeping the removal only if the
     puzzle is still solvable using techniques at or below the requested tier.
     Any puzzle the technique engine can finish has exactly one solution, because every
     step is a forced deduction — so uniqueness comes for free.
  3. Accept the puzzle only if it actually *needs* the requested tier
     (e.g. an intermediate puzzle must not be solvable with singles alone).

Advanced puzzles (Naked Triple / X-Wing required) are rare in random digs, so a small
background pool keeps a few pre-generated puzzles per level, persisted to disk.
"""

import os
import json
import random
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.validator import SudokuValidator
from .techniques.technique_engine import TechniqueEngine, TIER_ORDER

LEVELS = ("beginner", "intermediate", "advanced")

# Clue floor per level: beginner grids stop digging early so they stay approachable.
BEGINNER_CLUE_RANGE = (30, 36)

# How long a synchronous request may search before falling back.
SYNC_BUDGET_SEC = {"beginner": 3.0, "intermediate": 6.0, "advanced": 8.0}

POOL_TARGET = {"beginner": 2, "intermediate": 2, "advanced": 3}
POOL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "generated_pool.json"))

TECHNIQUE_LABELS = {
    "full_house": "Full House",
    "naked_single": "Naked Single",
    "hidden_single": "Hidden Single",
    "naked_pair": "Naked Pair",
    "hidden_pair": "Hidden Pair",
    "pointing_pair": "Pointing Pair",
    "box_line_reduction": "Box/Line Reduction",
    "naked_triple": "Naked Triple",
    "x_wing": "X-Wing",
}


# --------------------------------------------------------------------------
# Grid construction
# --------------------------------------------------------------------------
def random_solution(rng: random.Random) -> List[int]:
    """Return a random complete Sudoku grid as a flat list of 81 ints."""
    grid = [0] * 81
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9

    def fill(i: int) -> bool:
        if i == 81:
            return True
        r, c = divmod(i, 9)
        b = (r // 3) * 3 + c // 3
        used = rows[r] | cols[c] | boxes[b]
        for v in rng.sample(range(1, 10), 9):
            bit = 1 << v
            if used & bit:
                continue
            grid[i] = v
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            if fill(i + 1):
                return True
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[b] ^= bit
        grid[i] = 0
        return False

    fill(0)
    return grid


def count_solutions(puzzle: str, limit: int = 2) -> int:
    """Count solutions of an 81-char puzzle string, stopping once `limit` is reached."""
    grid = [int(ch) if ch.isdigit() else 0 for ch in puzzle]
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9
    for i, v in enumerate(grid):
        if v:
            r, c = divmod(i, 9)
            bit = 1 << v
            b = (r // 3) * 3 + c // 3
            if (rows[r] | cols[c] | boxes[b]) & bit:
                return 0
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit

    empties = [i for i, v in enumerate(grid) if v == 0]
    found = 0

    def search() -> bool:
        nonlocal found
        # Most-constrained empty cell first (MRV)
        best, best_mask, best_count = -1, 0, 10
        for i in empties:
            if grid[i]:
                continue
            r, c = divmod(i, 9)
            mask = ~(rows[r] | cols[c] | boxes[(r // 3) * 3 + c // 3]) & 0x3FE
            n = bin(mask).count("1")
            if n < best_count:
                best, best_mask, best_count = i, mask, n
                if n <= 1:
                    break
        if best == -1:
            found += 1
            return found >= limit
        if best_count == 0:
            return False
        r, c = divmod(best, 9)
        b = (r // 3) * 3 + c // 3
        for v in range(1, 10):
            bit = 1 << v
            if not best_mask & bit:
                continue
            grid[best] = v
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            stop = search()
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[b] ^= bit
            grid[best] = 0
            if stop:
                return True
        return False

    search()
    return found


# --------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------
def grade_puzzle(puzzle: str) -> Optional[Dict[str, Any]]:
    """
    Solve with the full technique hierarchy and report which tier the puzzle requires.
    Returns None if the puzzle cannot be finished without guessing.
    """
    solved, steps, final, _ = TechniqueEngine.solve_puzzle_with_techniques(puzzle, max_tier="advanced", max_steps=400)
    if not solved:
        return None

    required_rank = max((TIER_ORDER[s.difficulty_tier] for s in steps), default=1)
    required_tier = next(t for t, rank in TIER_ORDER.items() if rank == required_rank)

    # The hardest technique is the most-used technique from the highest tier needed
    top_steps = [s.technique_id for s in steps if TIER_ORDER[s.difficulty_tier] == required_rank]
    hardest = max(set(top_steps), key=top_steps.count) if top_steps else "full_house"

    techniques_used: List[str] = []
    for s in steps:
        if s.technique_id not in techniques_used:
            techniques_used.append(s.technique_id)

    advanced_steps = sum(1 for s in steps if TIER_ORDER[s.difficulty_tier] >= 2)
    return {
        "solution": final,
        "required_tier": required_tier,
        "required_rank": required_rank,
        "hardest_technique": hardest,
        "techniques_used": techniques_used,
        "step_count": len(steps),
        "advanced_step_count": advanced_steps,
    }


def _dig(rng: random.Random, max_tier: str, min_clues: int = 17) -> str:
    """Blank cells while the puzzle stays solvable using techniques up to max_tier."""
    grid = random_solution(rng)
    cells = list(range(81))
    rng.shuffle(cells)
    clues = 81
    for i in cells:
        if clues <= min_clues:
            break
        saved = grid[i]
        grid[i] = 0
        candidate = "".join(map(str, grid))
        if TechniqueEngine.solve_puzzle_with_techniques(candidate, max_tier=max_tier)[0]:
            clues -= 1
        else:
            grid[i] = saved
    return "".join(map(str, grid))


def _build_record(puzzle: str, level: str, grade: Dict[str, Any]) -> Dict[str, Any]:
    hardest_label = TECHNIQUE_LABELS.get(grade["hardest_technique"], grade["hardest_technique"])
    clue_count = sum(1 for ch in puzzle if ch != "0")
    meets_level = TIER_ORDER[grade["required_tier"]] >= TIER_ORDER[level]

    if level == "beginner":
        description = "Solvable with Full House and Singles — scan rows, columns, and boxes."
    elif meets_level:
        description = f"Freshly generated. You'll need {hardest_label} to crack it without guessing."
    else:
        description = (
            f"Freshly generated. A puzzle needing an {level}-only technique wasn't found in time, "
            f"so this is the toughest close match — it needs {hardest_label}."
        )

    return {
        "puzzle_id": f"gen_{uuid.uuid4().hex[:8]}",
        "title": f"Fresh {level.capitalize()} · {hardest_label}",
        "difficulty": level,
        "generated": True,
        "meets_level": meets_level,
        "clue_count": clue_count,
        "puzzle": puzzle,
        "solution": grade["solution"],
        "required_tier": grade["required_tier"],
        "hardest_technique": grade["hardest_technique"],
        "hardest_technique_label": hardest_label,
        "techniques_used": grade["techniques_used"],
        "description": description,
    }


def generate_puzzle(
    level: str = "beginner",
    seed: Optional[int] = None,
    time_budget: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Generate a new puzzle whose required technique tier matches `level`.
    Always returns a valid, uniquely-solvable, guess-free puzzle; if the exact tier is not
    found within the time budget, returns the hardest puzzle found and sets meets_level=False.
    """
    level = level.lower()
    if level not in LEVELS:
        raise ValueError(f"Unknown level '{level}'. Expected one of {LEVELS}.")

    rng = random.Random(seed)
    budget = SYNC_BUDGET_SEC[level] if time_budget is None else time_budget
    deadline = time.monotonic() + budget
    target_rank = TIER_ORDER[level]

    best: Optional[Tuple[Tuple[int, int, int], str, Dict[str, Any]]] = None
    attempts = 0

    while True:
        attempts += 1
        if level == "beginner":
            puzzle = _dig(rng, "beginner", min_clues=rng.randint(*BEGINNER_CLUE_RANGE))
        else:
            puzzle = _dig(rng, level)

        grade = grade_puzzle(puzzle)
        if grade is not None:
            rank = grade["required_rank"]
            if rank == target_rank:
                return _finalize(puzzle, level, grade)
            if rank <= target_rank:
                clues = sum(1 for ch in puzzle if ch != "0")
                score = (rank, grade["advanced_step_count"], -clues)
                if best is None or score > best[0]:
                    best = (score, puzzle, grade)

        if time.monotonic() >= deadline and best is not None:
            return _finalize(best[1], level, best[2])
        if attempts > 500:
            raise RuntimeError("Puzzle generation failed to converge.")


def _finalize(puzzle: str, level: str, grade: Dict[str, Any]) -> Dict[str, Any]:
    is_valid, msg = SudokuValidator.is_valid_grid(grade["solution"], puzzle)
    if not is_valid:
        raise RuntimeError(f"Generated puzzle failed validation: {msg}")
    return _build_record(puzzle, level, grade)


# --------------------------------------------------------------------------
# Background pool (keeps a few ready puzzles per level so requests are instant)
# --------------------------------------------------------------------------
class PuzzlePool:
    def __init__(self, path: str = POOL_PATH):
        self.path = path
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.pool: Dict[str, List[Dict[str, Any]]] = {lvl: [] for lvl in LEVELS}
        self.thread: Optional[threading.Thread] = None
        self._load()

    def _load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for lvl in LEVELS:
                self.pool[lvl] = [p for p in data.get(lvl, []) if p.get("puzzle")]
        except (OSError, ValueError):
            pass

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.pool, f, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass

    def take(self, level: str) -> Optional[Dict[str, Any]]:
        """Pop a pooled puzzle that meets the level, if one is ready."""
        with self.lock:
            items = self.pool.get(level, [])
            item = items.pop(0) if items else None
            if item is not None:
                self._save()
        self.wake.set()
        return item

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, name="puzzle-pool", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        while True:
            needed = [lvl for lvl in LEVELS if len(self.pool[lvl]) < POOL_TARGET[lvl]]
            if not needed:
                self.wake.wait()
                self.wake.clear()
                continue
            # Fill the quick levels first so they're instant soon after startup; advanced is slow
            level = min(needed, key=lambda lvl: TIER_ORDER[lvl])
            try:
                record = generate_puzzle(level, time_budget=120.0)
            except Exception:
                time.sleep(5)
                continue
            if record.get("meets_level"):
                with self.lock:
                    self.pool[level].append(record)
                    self._save()


_pool: Optional[PuzzlePool] = None


def get_pool() -> PuzzlePool:
    global _pool
    if _pool is None:
        _pool = PuzzlePool()
    return _pool


def start_background_pool() -> None:
    """Start the refill thread unless disabled (e.g. for tests) via SUDOKU_GENERATOR_POOL=0."""
    if os.environ.get("SUDOKU_GENERATOR_POOL", "1") == "0":
        return
    get_pool().start()


def get_fresh_puzzle(level: str) -> Dict[str, Any]:
    """Serve a pooled puzzle if one is ready, otherwise generate one now."""
    level = level.lower()
    if level not in LEVELS:
        raise ValueError(f"Unknown level '{level}'. Expected one of {LEVELS}.")
    pooled = get_pool().take(level)
    if pooled is not None:
        return pooled
    return generate_puzzle(level)
