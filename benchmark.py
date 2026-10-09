"""
Benchmarking Harness - Phase 4.
Runs all solver configurations against benchmark puzzles grouped by difficulty.
Collects consistent telemetry and exports structured CSV results.
"""

import os
import sys
import time
import argparse
import pandas as pd
from typing import List, Dict, Any

from src.dataset_loader import DatasetLoader
from src.baseline_solver import BaselineSolver
from src.csp_solver import CSPSolver
from src.telemetry import Telemetry


def instantiate_solvers(solver_names: List[str], timeout_sec: float) -> Dict[str, Any]:
    """Factory creating solver instances based on name string."""
    registry = {}
    for name in solver_names:
        clean = name.strip().lower()
        if clean in ("baseline", "baseline_dfs", "dfs"):
            registry["baseline_dfs"] = BaselineSolver(timeout_sec=timeout_sec)
        elif clean in ("dfs_fc", "fc"):
            registry["dfs_fc"] = CSPSolver(
                propagation="fc", use_mrv=False, use_lcv=False,
                timeout_sec=timeout_sec, name="dfs_fc"
            )
        elif clean in ("dfs_fc_mrv", "fc_mrv", "mrv"):
            registry["dfs_fc_mrv"] = CSPSolver(
                propagation="fc", use_mrv=True, use_lcv=False,
                timeout_sec=timeout_sec, name="dfs_fc_mrv"
            )
        elif clean in ("dfs_fc_mrv_lcv", "fc_mrv_lcv", "lcv"):
            registry["dfs_fc_mrv_lcv"] = CSPSolver(
                propagation="fc", use_mrv=True, use_lcv=True,
                timeout_sec=timeout_sec, name="dfs_fc_mrv_lcv"
            )
        elif clean in ("norvig", "norvig_csp"):
            registry["norvig_csp"] = CSPSolver(
                propagation="norvig", timeout_sec=timeout_sec, name="norvig_csp"
            )
        elif clean in ("dfs_ac3", "ac3"):
            registry["dfs_ac3"] = CSPSolver(
                propagation="ac3", use_mrv=False, use_lcv=False,
                timeout_sec=timeout_sec, name="dfs_ac3"
            )
        else:
            print(f"Warning: Unknown solver name '{name}', skipping.")
    return registry


def run_benchmark(
    dataset_path: str = "data/synthetic_puzzles.csv",
    output_csv: str = "results/benchmark_results.csv",
    limit_per_difficulty: int = 5,
    timeout_sec: float = 3.0,
    solvers_to_run: Optional[List[str]] = None,
    plot_after: bool = True
) -> pd.DataFrame:
    """
    Execute benchmark suite across solvers and difficulty tiers.
    """
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    if solvers_to_run is None:
        solvers_to_run = ["baseline_dfs", "dfs_fc", "dfs_fc_mrv", "dfs_fc_mrv_lcv", "norvig_csp"]

    solvers = instantiate_solvers(solvers_to_run, timeout_sec)

    print("=" * 80)
    print("SUDOKU CSP BENCHMARK HARNESS")
    print(f"Dataset:       {dataset_path}")
    print(f"Solvers:       {list(solvers.keys())}")
    print(f"Per-diff cap:  {limit_per_difficulty} puzzles")
    print(f"Timeout:       {timeout_sec}s per puzzle")
    print("=" * 80)

    # Load dataset grouped by difficulty
    all_puzzles = DatasetLoader.load_csv(dataset_path)
    difficulties = ["easy", "medium", "hard", "extreme"]
    selected_puzzles = []

    for diff in difficulties:
        diff_puzzles = [p for p in all_puzzles if p["difficulty"] == diff]
        selected_puzzles.extend(diff_puzzles[:limit_per_difficulty])

    print(f"Total benchmark puzzles selected: {len(selected_puzzles)}\n")

    results: List[Dict[str, Any]] = []

    header_fmt = "{:<12} | {:<8} | {:<16} | {:<8} | {:>10} | {:>10} | {:>8}"
    print(header_fmt.format("Puzzle ID", "Diff", "Solver", "Status", "Time (ms)", "Nodes", "MaxDepth"))
    print("-" * 86)

    for p in selected_puzzles:
        puz_id = p["puzzle_id"]
        diff = p["difficulty"]
        puz_str = p["puzzle"]

        for s_name, solver in solvers.items():
            tel: Telemetry = solver.solve(puz_str, puzzle_id=puz_id, difficulty=diff)

            status_str = "SOLVED" if tel.solved else ("TIMEOUT" if "Timeout" in str(tel.error_message) else "FAILED")

            row_dict = {
                "puzzle_id": puz_id,
                "difficulty": diff,
                "clue_count": p["clue_count"],
                "is_synthetic": p["is_synthetic"],
                "solver": tel.solver_name,
                "solved": tel.solved,
                "runtime_ms": round(tel.runtime_ms, 3),
                "nodes_expanded": tel.nodes_expanded,
                "max_depth": tel.max_depth,
                "error_message": tel.error_message or "",
            }
            results.append(row_dict)

            print(header_fmt.format(
                puz_id[:12],
                diff[:8],
                tel.solver_name[:16],
                status_str[:8],
                f"{tel.runtime_ms:.2f}",
                tel.nodes_expanded,
                tel.max_depth
            ))

    # Convert to DataFrame and save
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print("\n" + "=" * 80)
    print(f"Benchmark complete! Results saved to -> {output_csv}")
    print("=" * 80)

    # Print Summary Table
    print("\nBENCHMARK AGGREGATE SUMMARY:")
    summary = df.groupby(["solver", "difficulty"]).agg(
        total_puzzles=("solved", "count"),
        solved_count=("solved", lambda s: s.sum()),
        success_rate=("solved", lambda s: f"{s.mean() * 100:.1f}%"),
        avg_runtime_ms=("runtime_ms", "mean"),
        avg_nodes=("nodes_expanded", "mean"),
        avg_max_depth=("max_depth", "mean"),
    ).reset_index()

    # Sort logically
    diff_order = {"easy": 1, "medium": 2, "hard": 3, "extreme": 4}
    summary["diff_rank"] = summary["difficulty"].map(diff_order)
    summary = summary.sort_values(by=["solver", "diff_rank"]).drop(columns=["diff_rank"])

    print(summary.to_string(index=False))

    if plot_after:
        try:
            from visualize import generate_all_charts
            print("\nGenerating publication-quality charts...")
            generate_all_charts(output_csv)
        except Exception as e:
            print(f"Chart generation note: {e}")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Sudoku CSP Benchmark Suite.")
    parser.add_argument("--dataset", type=str, default="data/synthetic_puzzles.csv", help="Path to input CSV dataset")
    parser.add_argument("--output", type=str, default="results/benchmark_results.csv", help="Path to save output CSV")
    parser.add_argument("--limit", type=int, default=5, help="Number of puzzles per difficulty tier")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds per puzzle")
    parser.add_argument(
        "--solvers",
        type=str,
        default="baseline_dfs,dfs_fc,dfs_fc_mrv,dfs_fc_mrv_lcv,norvig_csp",
        help="Comma-separated solver identifiers"
    )
    parser.add_argument("--no-plot", action="store_true", help="Skip automatic plot generation")

    args = parser.parse_args()
    solvers_list = [s.strip() for s in args.solvers.split(",") if s.strip()]

    run_benchmark(
        dataset_path=args.dataset,
        output_csv=args.output,
        limit_per_difficulty=args.limit,
        timeout_sec=args.timeout,
        solvers_to_run=solvers_list,
        plot_after=not args.no_plot,
    )
