"""
Optimized CSP Sudoku Solver Module - Phase 3.
Implements:
  1. Forward Checking (FC) and AC-3 Arc Consistency constraint propagation.
  2. Minimum Remaining Values (MRV) heuristic with Degree Heuristic tie-breaking.
  3. Least Constraining Value (LCV) heuristic.
  4. Peter Norvig's Constraint Propagation + Search agent.

Heuristics can be toggled independently (FC / AC-3, MRV, LCV, or Norvig).
"""

import time
from collections import deque
from typing import Dict, Set, List, Optional, Tuple, Union
from .board import SQUARES, PEERS, UNITS, parse_grid, grid_to_string, COORD_TO_SQUARE, SQUARE_TO_COORD
from .telemetry import Telemetry
from .validator import SudokuValidator


class CSPSolver:
    """
    Modular Constraint Satisfaction Problem (CSP) Sudoku Solver.
    """

    def __init__(
        self,
        propagation: str = "fc",  # 'fc' (forward checking), 'ac3', or 'norvig'
        use_mrv: bool = True,
        use_lcv: bool = False,
        timeout_sec: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize the CSP Solver with specified heuristics and propagation strategy.

        Args:
            propagation: 'fc' for Forward Checking, 'ac3' for Arc Consistency 3,
                         or 'norvig' for Norvig's elimination + unit propagation.
            use_mrv: Enable Minimum Remaining Values (MRV) variable selection heuristic.
            use_lcv: Enable Least Constraining Value (LCV) value-ordering heuristic.
            timeout_sec: Maximum time budget in seconds before aborting.
            name: Optional custom identifier for telemetry reports.
        """
        self.propagation = propagation.lower()
        self.use_mrv = use_mrv
        self.use_lcv = use_lcv
        self.timeout_sec = timeout_sec

        # Construct a descriptive name if not explicitly given
        if name:
            self.name = name
        elif self.propagation == "norvig":
            self.name = "norvig_csp"
        else:
            parts = ["dfs", self.propagation]
            if self.use_mrv:
                parts.append("mrv")
            if self.use_lcv:
                parts.append("lcv")
            self.name = "_".join(parts)

        self.nodes_expanded = 0
        self.max_depth = 0
        self.start_time = 0.0
        self.timed_out = False

    # --------------------------------------------------------------------------
    # Domain Initialization & Initial Propagation
    # --------------------------------------------------------------------------
    def _initialize_domains(self, grid: List[List[int]]) -> Optional[Dict[str, Set[int]]]:
        """
        Build domain dictionary {square: set_of_valid_values}.
        Applies immediate initial pruning based on original clues.
        """
        domains: Dict[str, Set[int]] = {s: set(range(1, 10)) for s in SQUARES}

        for r in range(9):
            for c in range(9):
                val = grid[r][c]
                if val != 0:
                    sq = COORD_TO_SQUARE[(r, c)]
                    domains[sq] = {val}

        # Initial Forward Checking prune from clues
        for s in SQUARES:
            if len(domains[s]) == 1:
                val = next(iter(domains[s]))
                for peer in PEERS[s]:
                    domains[peer].discard(val)
                    if len(domains[peer]) == 0:
                        return None  # Puzzle has an immediate clue conflict

        # If AC-3 is requested, enforce full initial arc consistency
        if self.propagation == "ac3":
            if not self._ac3(domains):
                return None

        return domains

    # --------------------------------------------------------------------------
    # Constraint Propagation: AC-3
    # --------------------------------------------------------------------------
    def _ac3(self, domains: Dict[str, Set[int]], queue: Optional[deque] = None) -> bool:
        """
        Enforce Arc Consistency 3 (AC-3).
        Maintains consistency such that for every value in domain(Xi),
        there is a valid differing value in domain(Xj).
        """
        if queue is None:
            # Initialize with all directed constraint arcs (Xi, Xj)
            queue = deque((xi, xj) for xi in SQUARES for xj in PEERS[xi])

        while queue:
            # Check timeout
            if self.timeout_sec and (time.perf_counter() - self.start_time) > self.timeout_sec:
                self.timed_out = True
                return False

            xi, xj = queue.popleft()
            if self._revise(domains, xi, xj):
                if len(domains[xi]) == 0:
                    return False  # Domain wipeout
                for xk in PEERS[xi]:
                    if xk != xj:
                        queue.append((xk, xi))
        return True

    def _revise(self, domains: Dict[str, Set[int]], xi: str, xj: str) -> bool:
        """
        Revise domain(xi) with respect to xj.
        If domain(xj) has only one value {y}, then y cannot be in domain(xi).
        """
        revised = False
        if len(domains[xj]) == 1:
            y = next(iter(domains[xj]))
            if y in domains[xi]:
                domains[xi].remove(y)
                revised = True
        return revised

    # --------------------------------------------------------------------------
    # Variable Selection: Static vs MRV (with Degree Heuristic Tie-Breaker)
    # --------------------------------------------------------------------------
    def _select_unassigned_variable(
        self,
        domains: Dict[str, Set[int]],
        assigned: Dict[str, int]
    ) -> Optional[str]:
        """
        Select the next unassigned variable to assign.
        If use_mrv is True:
            Picks cell with fewest remaining legal values (Minimum Remaining Values).
            Ties are broken by Degree Heuristic (most unassigned peers).
        Else:
            Picks the first unassigned cell in standard static order.
        """
        unassigned = [s for s in SQUARES if s not in assigned]
        if not unassigned:
            return None

        if not self.use_mrv:
            # Static ordering
            return unassigned[0]

        # MRV: find minimum domain size
        min_domain_len = min(len(domains[s]) for s in unassigned)
        candidates = [s for s in unassigned if len(domains[s]) == min_domain_len]

        if len(candidates) == 1:
            return candidates[0]

        # Degree Heuristic tie-breaker: most unassigned peers
        def unassigned_peer_count(sq: str) -> int:
            return sum(1 for p in PEERS[sq] if p not in assigned)

        return max(candidates, key=unassigned_peer_count)

    # --------------------------------------------------------------------------
    # Value Ordering: Static vs LCV (Least Constraining Value)
    # --------------------------------------------------------------------------
    def _order_domain_values(
        self,
        var: str,
        domains: Dict[str, Set[int]],
        assigned: Dict[str, int]
    ) -> List[int]:
        """
        Order candidate values for variable var.
        If use_lcv is True:
            Sorts values by the count of options ruled out in unassigned peers
            (ascending order: fewest eliminations first).
        Else:
            Standard numerical order (1 to 9).
        """
        values = sorted(list(domains[var]))
        if not self.use_lcv:
            return values

        # LCV: Count how many values would be eliminated from unassigned peers
        unassigned_peers = [p for p in PEERS[var] if p not in assigned]

        def count_conflicts(val: int) -> int:
            return sum(1 for p in unassigned_peers if val in domains[p])

        return sorted(values, key=count_conflicts)

    # --------------------------------------------------------------------------
    # Recursive Backtracking Search with Constraint Propagation
    # --------------------------------------------------------------------------
    def _backtrack(
        self,
        domains: Dict[str, Set[int]],
        assigned: Dict[str, int],
        depth: int
    ) -> Optional[Dict[str, int]]:
        """
        Recursive search with domain maintenance and pruning.
        """
        if self.timeout_sec and (time.perf_counter() - self.start_time) > self.timeout_sec:
            self.timed_out = True
            return None

        if depth > self.max_depth:
            self.max_depth = depth

        if len(assigned) == 81:
            return assigned

        var = self._select_unassigned_variable(domains, assigned)
        if var is None:
            return assigned

        for val in self._order_domain_values(var, domains, assigned):
            self.nodes_expanded += 1

            # Make local copy of domains for backtracking
            new_domains = {s: set(vals) for s, vals in domains.items()}
            new_domains[var] = {val}
            new_assigned = dict(assigned)
            new_assigned[var] = val

            # Propagate constraints
            consistent = True

            if self.propagation == "fc":
                # Forward Checking: prune val from all unassigned peers
                for peer in PEERS[var]:
                    if peer not in new_assigned:
                        if val in new_domains[peer]:
                            new_domains[peer].remove(val)
                            if len(new_domains[peer]) == 0:
                                consistent = False
                                break

            elif self.propagation == "ac3":
                # AC-3 propagation after setting var = {val}
                arc_queue = deque((p, var) for p in PEERS[var] if p not in new_assigned)
                consistent = self._ac3(new_domains, arc_queue)

            if consistent and not self.timed_out:
                result = self._backtrack(new_domains, new_assigned, depth + 1)
                if result is not None:
                    return result

            if self.timed_out:
                return None

        return None

    # --------------------------------------------------------------------------
    # Peter Norvig's Constraint Propagation + Search Method
    # --------------------------------------------------------------------------
    def _solve_norvig(self, grid: List[List[int]]) -> Tuple[Optional[str], bool]:
        """
        Peter Norvig's exact constraint propagation solver:
        Uses string candidate values and 2 propagation rules:
        1. If a square has only 1 candidate, eliminate it from peers.
        2. If a unit has only 1 place for a digit, put it there.
        """
        digits = "123456789"
        values = {s: digits for s in SQUARES}

        def assign_norvig(vals: Dict[str, str], s: str, d: str) -> Optional[Dict[str, str]]:
            other_values = vals[s].replace(d, "")
            if all(eliminate_norvig(vals, s, d2) for d2 in other_values):
                return vals
            return None

        def eliminate_norvig(vals: Dict[str, str], s: str, d: str) -> Optional[Dict[str, str]]:
            if d not in vals[s]:
                return vals
            vals[s] = vals[s].replace(d, "")
            if len(vals[s]) == 0:
                return None  # Contradiction: removed last value
            elif len(vals[s]) == 1:
                # Rule 1: Eliminate from peers
                d2 = vals[s]
                if not all(eliminate_norvig(vals, s2, d2) for s2 in PEERS[s]):
                    return None

            # Rule 2: If a unit has only 1 place for d, assign it
            for u in UNITS[s]:
                dplaces = [s2 for s2 in u if d in vals[s2]]
                if len(dplaces) == 0:
                    return None  # Contradiction: no place for d
                elif len(dplaces) == 1:
                    if not assign_norvig(vals, dplaces[0], d):
                        return None
            return vals

        def search_norvig(vals: Optional[Dict[str, str]], depth: int) -> Optional[Dict[str, str]]:
            if self.timeout_sec and (time.perf_counter() - self.start_time) > self.timeout_sec:
                self.timed_out = True
                return None

            if vals is None:
                return None

            if depth > self.max_depth:
                self.max_depth = depth

            if all(len(vals[s]) == 1 for s in SQUARES):
                return vals

            # MRV: Choose unfilled square s with fewest candidates
            unfilled = [s for s in SQUARES if len(vals[s]) > 1]
            s = min(unfilled, key=lambda sq: len(vals[sq]))

            for d in vals[s]:
                self.nodes_expanded += 1
                sol = search_norvig(assign_norvig(vals.copy(), s, d), depth + 1)
                if sol is not None:
                    return sol
                if self.timed_out:
                    return None
            return None

        # Load initial grid
        for r in range(9):
            for c in range(9):
                val = grid[r][c]
                if val != 0:
                    sq = COORD_TO_SQUARE[(r, c)]
                    if not assign_norvig(values, sq, str(val)):
                        return None, False

        res = search_norvig(values, depth=0)
        if res is not None:
            sol_str = "".join(res[s] for s in SQUARES)
            return sol_str, True
        return None, False

    # --------------------------------------------------------------------------
    # Main Solve Interface
    # --------------------------------------------------------------------------
    def solve(
        self,
        puzzle: Union[str, List[List[int]]],
        puzzle_id: str = "0",
        difficulty: str = "unknown"
    ) -> Telemetry:
        """
        Solve a Sudoku puzzle and return standardized Telemetry.
        """
        grid = parse_grid(puzzle) if isinstance(puzzle, str) else [row[:] for row in puzzle]
        orig_str = grid_to_string(grid)

        self.nodes_expanded = 0
        self.max_depth = 0
        self.timed_out = False
        self.start_time = time.perf_counter()

        solved = False
        sol_str = None

        if self.propagation == "norvig":
            sol_str, solved = self._solve_norvig(grid)
        else:
            domains = self._initialize_domains(grid)
            if domains is not None:
                # Pre-populate already assigned clue cells
                assigned = {
                    COORD_TO_SQUARE[(r, c)]: grid[r][c]
                    for r in range(9) for c in range(9) if grid[r][c] != 0
                }

                assignment_result = self._backtrack(domains, assigned, depth=0)
                if assignment_result is not None and len(assignment_result) == 81:
                    solved = True
                    sol_str = "".join(str(assignment_result[COORD_TO_SQUARE[(r, c)]])
                                      for r in range(9) for c in range(9))

        end_time = time.perf_counter()
        runtime_ms = (end_time - self.start_time) * 1000.0

        error_msg = "Timeout exceeded" if self.timed_out else (None if solved else "Unsatisfiable or exhausted")

        # Rigorous solution validation
        if solved and sol_str:
            is_valid, reason = SudokuValidator.is_valid_grid(sol_str, orig_str)
            if not is_valid:
                solved = False
                error_msg = f"Validation failed: {reason}"

        return Telemetry(
            solver_name=self.name,
            puzzle_id=str(puzzle_id),
            difficulty=difficulty,
            solved=solved,
            runtime_ms=runtime_ms,
            nodes_expanded=self.nodes_expanded,
            max_depth=self.max_depth,
            solution=sol_str,
            error_message=error_msg,
        )
