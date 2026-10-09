# Constraint Satisfaction Problem (CSP) Sudoku Solver & Comparative Analysis

An academic and empirical implementation comparing unoptimized backtracking search against incremental Constraint Satisfaction Problem (CSP) heuristics—including **Forward Checking**, **AC-3 Arc Consistency**, **Minimum Remaining Values (MRV)**, **Least Constraining Value (LCV)**, and **Peter Norvig's Constraint Propagation Agent**.

---

## Table of Contents
1. [Project Overview & Objectives](#project-overview--objectives)
2. [CSP Formulation & Mathematical Framework](#csp-formulation--mathematical-framework)
3. [Solver Architectures](#solver-architectures)
   - [Baseline DFS (Backtracking)](#baseline-dfs-backtracking)
   - [Forward Checking & AC-3 Arc Consistency](#forward-checking--ac-3-arc-consistency)
   - [MRV & Degree Heuristic](#mrv--degree-heuristic)
   - [LCV Value Ordering](#lcv-value-ordering)
   - [Peter Norvig's Constraint Propagation Agent](#peter-norvigs-constraint-propagation-agent)
4. [Dataset Specifications (Kaggle & Synthetic)](#dataset-specifications-kaggle--synthetic)
5. [Telemetry & Correctness Validation](#telemetry--correctness-validation)
6. [How to Run](#how-to-run)
7. [Project Directory Layout](#project-directory-layout)

---

## Project Overview & Objectives

Sudoku is an NP-complete combinatorial number-placement puzzle. The primary objective of this project is to quantitatively investigate how classic Artificial Intelligence techniques transform an intractable brute-force search space ($O(9^m)$ where $m$ is the number of unassigned cells) into a deterministic or near-instantaneous decision process.

### Research Questions
1. How does domain pruning via **Forward Checking** compare against unpruned depth-first search?
2. What is the impact of variable-ordering heuristics (**MRV**) versus value-ordering heuristics (**LCV**) on search tree depth and node expansions?
3. Under what circumstances does Peter Norvig's dual-rule constraint propagation solve puzzles without branching?

---

## CSP Formulation & Mathematical Framework

Sudoku is formally modeled as a triple $\langle X, D, C \rangle$:

1. **Variables ($X$)**:
   $$X = \{X_{r,c} \mid r \in \{0,\dots,8\}, c \in \{0,\dots,8\}\}$$
   There are exactly 81 variables corresponding to the 81 cells of the $9 \times 9$ grid. In Norvig notation, these are labeled `'A1'` through `'I9'`.

2. **Domains ($D$)**:
   For each variable $X_{r,c}$:
   - If the cell is a given clue with digit $d \in \{1,\dots,9\}$, $D(X_{r,c}) = \{d\}$.
   - If the cell is blank, initial $D(X_{r,c}) = \{1, 2, 3, 4, 5, 6, 7, 8, 9\}$.

3. **Constraints ($C$)**:
   There are 27 distinct **AllDifferent** units:
   - **9 Row Constraints**: $\text{AllDifferent}(X_{r,0}, X_{r,1}, \dots, X_{r,8}) \quad \forall r \in \{0,\dots,8\}$
   - **9 Column Constraints**: $\text{AllDifferent}(X_{0,c}, X_{1,c}, \dots, X_{8,c}) \quad \forall c \in \{0,\dots,8\}$
   - **9 Box ($3 \times 3$) Constraints**: $\text{AllDifferent}(X_{3i+u, 3j+v}) \quad \forall u,v \in \{0,1,2\}, \; i,j \in \{0,1,2\}$

4. **Peers**:
   For any variable $X$, its peers $\text{Peers}(X)$ are the unique set of 20 other variables that share a row, column, or $3 \times 3$ box with $X$. Binary constraints exist between $X$ and every $Y \in \text{Peers}(X)$:
   $$X \neq Y \quad \forall Y \in \text{Peers}(X)$$

---

## Solver Architectures

The project decomposes solver complexity into 5 distinct configurations:

| Configuration | Variable Selection | Value Ordering | Constraint Propagation | Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Config A: Plain DFS** | Static (row-major) | Static ($1 \to 9$) | None (check validity at assignment) | $O(9^m)$ worst-case |
| **Config B: DFS + FC** | Static (row-major) | Static ($1 \to 9$) | Forward Checking (prune peer domains) | Substantial pruning |
| **Config C: DFS + FC + MRV** | MRV + Degree Heuristic | Static ($1 \to 9$) | Forward Checking | Fail-first optimization |
| **Config D: DFS + FC + MRV + LCV** | MRV + Degree Heuristic | LCV (ascending conflicts) | Forward Checking | Fail-first + succeed-first |
| **Norvig Agent** | MRV | Static string order | Singles + Unit Propagation | Near $O(1)$ on easy/medium |

### Baseline DFS (Backtracking)
- **Cell Order**: Scans from top-left $(0,0)$ to bottom-right $(8,8)$ for the first cell with value 0.
- **Value Order**: Tries digits $1, 2, \dots, 9$ sequentially.
- **Pruning**: Does **not** maintain domain sets. Only checks row, column, and box validity when assigning a value.
- **Limitation**: Suffers from catastrophic thrashing on hard puzzles with deep search trees.

### Forward Checking & AC-3 Arc Consistency
- **Forward Checking (FC)**: When variable $X$ is assigned value $v$, $v$ is immediately removed from the domains of all unassigned peers $Y \in \text{Peers}(X)$. If any peer's domain becomes empty ($\emptyset$), the branch fails immediately (domain wipeout).
- **AC-3 (Arc Consistency)**: Enforces arc consistency over all directed pairs $(X_i, X_j)$. If value $x \in D(X_i)$ has no valid support $y \in D(X_j)$ with $x \ne y$, $x$ is eliminated, and arcs $(X_k, X_i)$ are re-queued.

### MRV & Degree Heuristic
- **Minimum Remaining Values (MRV / "Fail-First" Heuristic)**: Selects the unassigned variable with the fewest legal values remaining in its domain:
  $$X^* = \arg\min_{X \text{ unassigned}} |D(X)|$$
  *Rationale*: If a variable only has 1 or 2 options, deciding it immediately minimizes the branching factor and catches dead ends early.
- **Degree Heuristic (Tie-Breaker)**: If multiple variables tie for minimum domain size, picks the variable involved in the largest number of constraints with other *unassigned* variables.

### LCV Value Ordering
- **Least Constraining Value (LCV / "Succeed-First" Heuristic)**: Given variable $X$, orders candidate values $v \in D(X)$ by the number of choices they eliminate from the domains of unassigned peers:
  $$\text{conflicts}(v) = \sum_{Y \in \text{Peers}(X), Y \text{ unassigned}} \mathbb{I}(v \in D(Y))$$
  Candidates with the lowest conflict count are attempted first to maximize the chance of finding a solution on the first branch.

### Peter Norvig's Constraint Propagation Agent
Combines two deterministic propagation rules:
1. **Rule 1 (Peer Elimination)**: If a cell has only one remaining value, eliminate that value from all its peers.
2. **Rule 2 (Unit Propagation / Hidden Singles)**: If a unit (row, col, or box) has only one remaining place for a value $d$, assign $d$ to that place.
These two rules cascade recursively and solve most easy and medium puzzles before search even begins!

---

## Dataset Specifications (Kaggle & Synthetic)

### Kaggle Format Support
The dataset loader (`src/dataset_loader.py`) supports Kaggle CSV formats containing:
- `quizzes` (81-char puzzle string with `0` or `.`) and `solutions` (81-char solution string).
- Optional difficulty labels (`easy`, `medium`, `hard`, `extreme`). If omitted, difficulty is automatically inferred from clue counts.

### Synthetic Benchmark (`data/synthetic_puzzles.csv`)
To guarantee academic integrity without pretending synthetic data is real Kaggle data:
- Procedurally generated from valid Latin hypercubes with carved clues.
- Includes curated, published historical benchmark puzzles (such as Arto Inkala's *AI Escargot* and minimal 17-clue puzzles).
- Labeled with `is_synthetic: True` and categorized:
  - **Easy**: 36–40 clues
  - **Medium**: 30–34 clues
  - **Hard**: 25–28 clues
  - **Extreme**: 21–24 clues

---

## Telemetry & Correctness Validation

### Telemetry Contract
Every solver returns a unified `Telemetry` dataclass:
```python
@dataclass
class Telemetry:
    solver_name: str     # e.g. 'baseline_dfs', 'dfs_fc_mrv'
    puzzle_id: str       # puzzle identifier
    difficulty: str      # 'easy', 'medium', 'hard', 'extreme'
    solved: bool         # True if complete valid solution found
    runtime_ms: float    # High-resolution wall-clock time (ms)
    nodes_expanded: int  # Variable assignments attempted
    max_depth: int       # Maximum recursion stack depth
    solution: str        # 81-char solution string
    error_message: str   # Timeout or error description
```

### Mathematical Validation (`src/validator.py`)
Every solution is automatically validated:
1. Exact length of 81 digits (1–9, no zeros or dots).
2. Clue preservation: every original clue matches the solution cell.
3. Every row contains $\{1, 2, \dots, 9\}$ with zero duplicates.
4. Every column contains $\{1, 2, \dots, 9\}$ with zero duplicates.
5. Every $3 \times 3$ box contains $\{1, 2, \dots, 9\}$ with zero duplicates.

---

## How to Run

### 1. Run Unit Tests
```bash
python -m unittest tests/test_solvers.py
```

### 2. Run Interactive 5-Minute Professor Demonstration
```bash
python demo.py
```

### 3. Run Benchmark Harness
```bash
# Run 5 puzzles per difficulty tier across all solvers with a 3-second timeout
python benchmark.py --limit 5 --timeout 3.0

# Run on a custom Kaggle CSV
python benchmark.py --dataset data/kaggle_sample.csv --limit 10
```

### 4. Generate Publication-Quality Charts
```bash
python visualize.py --csv results/benchmark_results.csv
```
Charts are exported to `results/charts/`:
- `node_expansions_by_difficulty.png`
- `runtime_ms_by_difficulty.png`
- `search_depth_by_difficulty.png`
- `summary_dashboard.png`

---

## Project Directory Layout

```
Sudokusolver/
├── data/
│   ├── synthetic_puzzles.csv       # Procedurally generated benchmark dataset
│   └── kaggle_sample.csv           # Kaggle schema sample (quizzes,solutions)
├── results/
│   ├── benchmark_results.csv       # Benchmark telemetry records
│   └── charts/                     # Generated PNG figures
├── src/
│   ├── __init__.py
│   ├── board.py                    # Norvig geometry, conversions, ASCII display
│   ├── validator.py                # Mathematical constraint validator
│   ├── telemetry.py                # Unified Telemetry dataclass
│   ├── baseline_solver.py          # Phase 2: Unoptimized recursive backtracking
│   ├── csp_solver.py               # Phase 3: Modular FC, AC-3, MRV, LCV, Norvig
│   └── dataset_loader.py           # Phase 1: Robust Kaggle/synthetic loader
├── tests/
│   ├── __init__.py
│   └── test_solvers.py             # Full unit test suite
├── benchmark.py                    # Phase 4: Automated benchmarking harness
├── visualize.py                    # Phase 4: Matplotlib chart generator
├── demo.py                         # Interactive 5-minute presentation script
├── generate_dataset.py             # Synthetic generator with difficulty tiers
├── README.md                       # Complete technical documentation
└── report.md                       # Formal academic project report
```
