"""
Interactive 5-Minute Demonstration Script for Professor Presentation.
Walks step-by-step through:
  1. CSP Formulation & Norvig Invariants
  2. Baseline Backtracking vs. Exponential Explosion
  3. Incremental Optimization: Plain DFS -> FC -> MRV -> LCV -> Norvig
  4. Telemetry Comparison Table
  5. Rigorous Solution Validation
"""

import time
from src.board import SudokuBoard, SQUARES, PEERS, format_grid
from src.validator import SudokuValidator
from src.baseline_solver import BaselineSolver
from src.csp_solver import CSPSolver


def print_banner(text: str):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def run_demo():
    print_banner("DEMO PART 1: SUDOKU CSP FORMULATION & NORVIG GEOMETRY")
    print(f"Total Variables (Cells):       {len(SQUARES)}")
    print(f"Domain for Unassigned Cells:   {{1, 2, 3, 4, 5, 6, 7, 8, 9}}")
    print(f"Total Constraint Units:        27 (9 Rows + 9 Columns + 9 3x3 Boxes)")
    sample_square = "E5"  # Center cell
    print(f"Sample Square '{sample_square}' has exactly {len(PEERS[sample_square])} peers: {sorted(list(PEERS[sample_square]))}")

    # Choose a classic hard benchmark puzzle
    puzzle_str = "000000000000003085001020000000507000004000100090000000500000073002010000000040009"
    board = SudokuBoard(puzzle_str)

    print("\nBenchmark Puzzle Loaded (Hard Tier, 19 Clues):")
    print(board.display())

    print_banner("DEMO PART 2: INCREMENTAL SOLVER COMPARISON")
    print("Evaluating all 5 configurations with a 3.0s timeout per solver:\n")

    solvers = [
        ("Config A: Plain DFS (Baseline)", BaselineSolver(timeout_sec=3.0)),
        ("Config B: DFS + Forward Checking", CSPSolver(propagation="fc", use_mrv=False, use_lcv=False, timeout_sec=3.0)),
        ("Config C: DFS + FC + MRV", CSPSolver(propagation="fc", use_mrv=True, use_lcv=False, timeout_sec=3.0)),
        ("Config D: DFS + FC + MRV + LCV", CSPSolver(propagation="fc", use_mrv=True, use_lcv=True, timeout_sec=3.0)),
        ("Peter Norvig Constraint Agent", CSPSolver(propagation="norvig", timeout_sec=3.0)),
    ]

    results = []
    final_solution = None

    for label, solver in solvers:
        print(f"-> Executing {label}...", end="", flush=True)
        tel = solver.solve(puzzle_str, puzzle_id="demo_hard", difficulty="hard")
        status = "SUCCESS" if tel.solved else ("TIMEOUT" if "Timeout" in str(tel.error_message) else "FAILED")
        print(f" [{status}] | Runtime: {tel.runtime_ms:.2f} ms | Nodes: {tel.nodes_expanded:,} | Max Depth: {tel.max_depth}")

        results.append((label, status, tel.runtime_ms, tel.nodes_expanded, tel.max_depth))
        if tel.solved and final_solution is None:
            final_solution = tel.solution

    print_banner("DEMO PART 3: TELEMETRY COMPARISON TABLE")
    table_fmt = "{:<32} | {:<8} | {:>12} | {:>14} | {:>10}"
    print(table_fmt.format("Configuration", "Status", "Runtime (ms)", "Nodes Expanded", "Max Depth"))
    print("-" * 88)
    for label, status, rtime, nodes, depth in results:
        print(table_fmt.format(label, status, f"{rtime:.2f}", f"{nodes:,}", depth))

    print_banner("DEMO PART 4: MATHEMATICAL SOLUTION VALIDATION")
    if final_solution:
        is_valid, msg = SudokuValidator.is_valid_grid(final_solution, puzzle_str)
        print(f"Validation Status: {'PASS' if is_valid else 'FAIL'}")
        print(f"Validator Output:  {msg}")
        print("\nSolved Sudoku Grid:")
        solved_board = SudokuBoard(final_solution)
        print(solved_board.display())
    else:
        print("No solution was returned by any solver within the time budget.")

    print_banner("DEMO PART 5: KEY TAKEAWAYS FOR THE EVALUATION")
    print("1. Baseline Backtracking explores up to 9^m combinations, timing out on hard puzzles.")
    print("2. Forward Checking prunes domains early, cutting search space by orders of magnitude.")
    print("3. MRV (Minimum Remaining Values) prioritizes the most constrained variables first, causing early failure.")
    print("4. Norvig's dual-rule constraint propagation solves many puzzles with zero search branching!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
