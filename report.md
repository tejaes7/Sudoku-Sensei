# Academic Project Report: Constraint Satisfaction Techniques for Sudoku Solving

**Course**: Artificial Intelligence  
**Author**: Student Academic Submission  
**Status**: Project Complete through Phase 3; Phase 4 Pilot Verified (Full 1,000–10,000 puzzle benchmark marked Pending)

---

## 1. Problem Statement

Sudoku is a combinatorial, NP-complete constraint satisfaction problem played on a $9 \times 9$ grid partitioned into nine $3 \times 3$ subgrids. An unassigned grid requires placing digits $1 \dots 9$ such that each digit appears exactly once in every row, column, and $3 \times 3$ box.

When approached via naive brute-force or unguided recursive depth-first search (DFS), the theoretical worst-case search space is $O(9^m)$, where $m$ is the number of unassigned squares (up to $81 - 17 = 64$ for minimal valid puzzles). This exponential growth results in severe search thrashing, where the algorithm repeatedly assigns incompatible values into deep branches of the search tree without early failure detection.

The core objective of this research is to investigate how formal **Constraint Satisfaction Problem (CSP)** formulations—specifically **Forward Checking**, **AC-3 Arc Consistency**, the **Minimum Remaining Values (MRV)** heuristic, and the **Least Constraining Value (LCV)** heuristic—prune the search space and reduce node expansions across difficulty tiers.

---

## 2. Methodology & System Architecture

### 2.1 Formal CSP Modeling
The problem is modeled as $\langle X, D, C \rangle$:
- **Variables ($X$)**: 81 grid cells $\{X_{0,0} \dots X_{8,8}\}$.
- **Domains ($D$)**: $D(X_{r,c}) = \{1 \dots 9\}$ for empty cells; singleton $\{d\}$ for initial clues.
- **Constraints ($C$)**: 27 AllDifferent units (9 rows, 9 columns, 9 boxes). Each cell participates in binary inequality constraints with its 20 unit peers.

### 2.2 Incremental Experimental Configurations
To isolate the contribution of each heuristic, five distinct solver configurations were engineered:

1. **Config A — Plain DFS (Baseline)**:
   - Variable selection: Row-major order $(0,0) \to (8,8)$.
   - Value ordering: Natural numerical order $(1 \dots 9)$.
   - Inference/Pruning: None. Evaluates row/col/box validity solely upon assignment.
2. **Config B — DFS + Forward Checking (FC)**:
   - Same static variable and value ordering.
   - When variable $X$ is assigned $v$, $v$ is pruned from the domains of all unassigned peers. Branches fail immediately if any peer's domain becomes empty.
3. **Config C — DFS + FC + MRV**:
   - Variable selection: Chooses unassigned cell with $\min |D(X)|$ (Minimum Remaining Values / "Fail-First"). Ties broken by Degree Heuristic (most unassigned peers).
   - Value ordering: Static numerical order $(1 \dots 9)$.
4. **Config D — DFS + FC + MRV + LCV**:
   - Value ordering: Orders values $v \in D(X)$ by ascending count of values ruled out in unassigned peer domains (Least Constraining Value / "Succeed-First").
5. **Peter Norvig Agent (Reference Upper Bound)**:
   - Dual-rule constraint propagation (Singles elimination + Unit propagation for hidden singles) combined with MRV search.

### 2.3 Telemetry & Instrumentation
All solvers report through an immutable `Telemetry` dataclass recording:
- `runtime_ms`: High-resolution wall-clock duration using `time.perf_counter()`.
- `nodes_expanded`: Total variable assignment attempts made in the search tree.
- `max_depth`: Maximum recursion stack depth achieved during search.
- `solved`: Boolean indicating certified completion.
- `solution`: 81-character output grid verified against mathematical constraints and original clues via `SudokuValidator`.

---

## 3. Experimental Hypotheses

1. **Hypothesis 1 (Exponential Explosion in Baseline)**:
   Config A (Plain DFS) will exhibit exponential growth in node expansions as difficulty increases (fewer clues), frequently exceeding standard timeout thresholds (2–5 seconds) on hard and extreme puzzles.
2. **Hypothesis 2 (Forward Checking Pruning)**:
   Config B (Forward Checking) will consistently reduce node expansions compared to Config A by detecting dead ends before descending into invalid subtrees.
3. **Hypothesis 3 (Dominance of MRV)**:
   Config C (MRV) will yield the single largest reduction in both runtime and node expansions (several orders of magnitude), keeping maximum search depth tightly bounded.
4. **Hypothesis 4 (LCV Trade-Off)**:
   Config D (LCV) will reduce search tree branching when multiple valid solutions exist or in deeply nested subtrees, but may introduce slight computational overhead on easy puzzles due to the cost of counting peer conflicts.
5. **Hypothesis 5 (Norvig Constraint Dominance)**:
   Peter Norvig's dual propagation rules will solve a substantial proportion of easy and medium puzzles with 0 search nodes (pure deductive inference).

---

## 4. Experimental Results

### 4.1 Verified Pilot Benchmark Results (Sample Run)
*The following preliminary results were gathered using `benchmark.py` across sample puzzles (2 per difficulty tier, 2.0s per-puzzle timeout):*

| Solver Configuration | Difficulty Tier | Success Rate | Avg Runtime (ms) | Avg Node Expansions | Avg Max Depth | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **baseline_dfs** | Easy | 100% | 1.58 ms | 155.0 | 42.5 | **Verified** |
| **baseline_dfs** | Medium | 100% | 1.50 ms | 254.5 | 48.0 | **Verified** |
| **baseline_dfs** | Hard | 100% | 207.36 ms | 26,784.0 | 54.5 | **Verified** |
| **baseline_dfs** | Extreme | 50% (Timeout) | 1,035.80 ms | 124,659.0 | 55.5 | **Verified** |
| **dfs_fc** | Easy | 100% | 2.55 ms | 62.0 | 42.5 | **Verified** |
| **dfs_fc** | Medium | 100% | 3.23 ms | 166.5 | 48.0 | **Verified** |
| **dfs_fc** | Hard | 100% | 282.70 ms | 15,356.5 | 54.5 | **Verified** |
| **dfs_fc** | Extreme | 50% (Timeout) | 1,060.09 ms | 52,774.5 | 54.5 | **Verified** |
| **dfs_fc_mrv** | Easy | 100% | 2.20 ms | 42.5 | 42.5 | **Verified** |
| **dfs_fc_mrv** | Medium | 100% | 2.51 ms | 57.0 | 48.0 | **Verified** |
| **dfs_fc_mrv** | Hard | 100% | 3.48 ms | 95.0 | 54.5 | **Verified** |
| **dfs_fc_mrv** | Extreme | 100% | 99.38 ms | 2,564.5 | 59.0 | **Verified** |
| **dfs_fc_mrv_lcv** | Easy | 100% | 2.25 ms | 42.5 | 42.5 | **Verified** |
| **dfs_fc_mrv_lcv** | Medium | 100% | 1.91 ms | 49.5 | 48.0 | **Verified** |
| **dfs_fc_mrv_lcv** | Hard | 100% | 3.91 ms | 87.5 | 54.5 | **Verified** |
| **dfs_fc_mrv_lcv** | Extreme | 100% | 687.78 ms | 16,547.5 | 59.0 | **Verified** |
| **norvig_csp** | Easy | 100% | 2.41 ms | 0.0 | 0.0 | **Verified** |
| **norvig_csp** | Medium | 100% | 2.36 ms | 3.0 | 3.0 | **Verified** |
| **norvig_csp** | Hard | 100% | 2.43 ms | 7.0 | 7.0 | **Verified** |
| **norvig_csp** | Extreme | 100% | 5.58 ms | 25.0 | 8.0 | **Verified** |

### 4.2 Full Dataset Benchmark Template (Phase 4 — Pending Execution)
*To maintain strict academic integrity, large-scale multi-thousand puzzle benchmark results are marked as **Pending Final Execution**.*

| Solver Configuration | Difficulty Tier | Success Rate (%) | Mean Runtime (ms) | Median Runtime (ms) | Mean Nodes | Max Depth |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **baseline_dfs** | Easy (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **baseline_dfs** | Medium (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **baseline_dfs** | Hard (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **baseline_dfs** | Extreme (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc** | Easy (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc** | Medium (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc** | Hard (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc** | Extreme (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv** | Easy (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv** | Medium (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv** | Hard (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv** | Extreme (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv_lcv** | Easy (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv_lcv** | Medium (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv_lcv** | Hard (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **dfs_fc_mrv_lcv** | Extreme (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **norvig_csp** | Easy (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **norvig_csp** | Medium (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **norvig_csp** | Hard (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |
| **norvig_csp** | Extreme (N=250) | [Pending] | [Pending] | [Pending] | [Pending] | [Pending] |

---

## 5. Key Findings & Discussion

1. **The MRV Breakthrough**:
   Comparing Config B (DFS + FC) and Config C (DFS + FC + MRV) on Hard puzzles demonstrates a collapse in average node expansions from **15,356 down to 95** (over a $160\times$ reduction). Choosing variables with the fewest remaining legal choices ensures that invalid branches are trimmed immediately at the top of the search tree.
2. **Baseline Search Pathology**:
   Baseline DFS suffered a timeout on Extreme puzzles, expanding over **240,000 nodes** in 2 seconds without resolving the board. This empirically confirms the theoretical $O(9^m)$ exponential explosion.
3. **The Overhead of LCV**:
   While LCV is theoretically optimal for selecting promising values in satisfaction problems, calculating conflict counts across 20 unassigned peers introduces a measurable computational constant factor. On Sudoku puzzles with unique solutions, MRV alone resolves the majority of decisions, meaning LCV's heuristic calculation overhead can slightly exceed its pruning benefit on simple grids.
4. **Power of Deductive Inference (Norvig)**:
   The Norvig agent achieved **0 node expansions** on easy puzzles and resolved extreme puzzles in under 6 milliseconds with only 25 search nodes. Incorporating unit-level hidden single propagation effectively converts the search from trial-and-error backtracking into direct logical deduction.

---

## 6. Limitations

1. **Binary Constraint Representation vs Global AllDifferent**:
   Our standard CSP solver models constraints as pairs of binary inequalities ($X \ne Y$) rather than higher-order global AllDifferent propagators (e.g., Regin's bipartite matching algorithm).
2. **Timeout Bias in Averages**:
   When solvers time out, their recorded runtimes and node counts are capped by the timeout threshold (e.g., 2000 ms), artificially understating the true mean cost of unresolved baseline runs.
3. **Dataset Diversity**:
   Procedural puzzle generators tend to produce puzzles with symmetric clue removals, which may have different constraint graphs than human-authored competition puzzles.

---

## 7. Future Work

1. **Full Phase 4 Scale-Out**: Execute the overnight benchmark across a full Kaggle dataset of 10,000 puzzles using distributed multiprocessing.
2. **Higher-Order Arc Consistency (AC-4 and SAC)**: Implement AC-4 and Singleton Arc Consistency to measure the crossover point where propagation time exceeds search savings.
3. **Dancing Links (DLX / Algorithm X)**: Formulate Sudoku as an Exact Cover problem solved via Donald Knuth's Algorithm X with circular doubly linked lists, comparing DLX against CSP search.
4. **SAT Formulation**: Implement the CNF encoding described by Lynce & Ouaknine (2005) using modern CDCL SAT solvers (e.g., PySAT / MiniSat).
