"""
Visualization Module - Phase 4.
Generates publication-quality charts from benchmark CSV results.
Plots:
  1. Node Expansions by Difficulty (Log Scale)
  2. Runtime (ms) by Difficulty (Log Scale)
  3. Search Tree Depth by Difficulty
  4. 3-in-1 Comparative Summary Dashboard
"""

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configure clean aesthetic styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 15,
    "figure.dpi": 300,
})

SOLVER_COLORS = {
    "baseline_dfs": "#e74c3c",       # Crimson Red
    "dfs_fc": "#e67e22",             # Pumpkin Orange
    "dfs_fc_mrv": "#2980b9",         # Cobalt Blue
    "dfs_fc_mrv_lcv": "#27ae60",     # Emerald Green
    "norvig_csp": "#8e44ad",         # Royal Purple
    "dfs_ac3": "#16a085",            # Teal
}

DIFFICULTIES = ["easy", "medium", "hard", "extreme"]


def setup_chart_dir(output_dir: str = "results/charts"):
    os.makedirs(output_dir, exist_ok=True)


def plot_grouped_metric(
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    output_path: str,
    log_scale: bool = False
):
    """Generate and save a grouped bar chart for a single metric."""
    setup_chart_dir(os.path.dirname(output_path))

    # Aggregate mean metric per solver & difficulty
    agg = df.groupby(["difficulty", "solver"])[metric].mean().unstack(fill_value=0)
    # Reindex difficulties
    agg = agg.reindex([d for d in DIFFICULTIES if d in agg.index])

    solvers = [s for s in agg.columns if s in SOLVER_COLORS] or list(agg.columns)

    x = np.arange(len(agg.index))
    total_width = 0.8
    bar_width = total_width / len(solvers)

    fig, ax = plt.subplots(figsize=(10, 6))

    for idx, s in enumerate(solvers):
        offset = (idx - len(solvers) / 2) * bar_width + bar_width / 2
        values = agg[s].values
        color = SOLVER_COLORS.get(s, "#7f8c8d")
        ax.bar(x + offset, values, width=bar_width, label=s, color=color, edgecolor="black", linewidth=0.5, alpha=0.9)

    ax.set_title(title, fontweight="bold", pad=15)
    ax.set_xlabel("Puzzle Difficulty Tier", fontweight="semibold")
    ax.set_ylabel(ylabel, fontweight="semibold")
    ax.set_xticks(x)
    ax.set_xticklabels([d.capitalize() for d in agg.index])
    ax.legend(title="Solver Configuration", frameon=True, facecolor="white", edgecolor="#cccccc")

    if log_scale:
        ax.set_yscale("log")
        # Ensure grid lines on log scale
        ax.grid(True, which="both", ls="--", alpha=0.5)
    else:
        ax.grid(True, ls="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved chart -> {output_path}")


def plot_summary_dashboard(df: pd.DataFrame, output_path: str = "results/charts/summary_dashboard.png"):
    """Generate a combined 3-panel publication-grade dashboard figure."""
    setup_chart_dir(os.path.dirname(output_path))

    solvers = [s for s in df["solver"].unique() if s in SOLVER_COLORS]
    if not solvers:
        solvers = list(df["solver"].unique())

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    metrics = [
        ("runtime_ms", "Runtime (ms, Log Scale)", "Average Runtime by Difficulty", True),
        ("nodes_expanded", "Node Expansions (Log Scale)", "Average Node Expansions", True),
        ("max_depth", "Recursion Tree Depth", "Average Maximum Tree Depth", False),
    ]

    for ax_idx, (metric, ylabel, title, log_scale) in enumerate(metrics):
        ax = axes[ax_idx]
        agg = df.groupby(["difficulty", "solver"])[metric].mean().unstack(fill_value=0)
        agg = agg.reindex([d for d in DIFFICULTIES if d in agg.index])

        x = np.arange(len(agg.index))
        total_width = 0.8
        bar_width = total_width / len(solvers)

        for s_idx, s in enumerate(solvers):
            offset = (s_idx - len(solvers) / 2) * bar_width + bar_width / 2
            values = agg[s].values if s in agg.columns else np.zeros(len(x))
            color = SOLVER_COLORS.get(s, "#7f8c8d")
            ax.bar(x + offset, values, width=bar_width, label=s, color=color, edgecolor="black", linewidth=0.5)

        ax.set_title(title, fontweight="bold", pad=12)
        ax.set_xlabel("Difficulty Tier", fontweight="semibold")
        ax.set_ylabel(ylabel, fontweight="semibold")
        ax.set_xticks(x)
        ax.set_xticklabels([d.capitalize() for d in agg.index])
        if log_scale:
            ax.set_yscale("log")
            ax.grid(True, which="both", ls="--", alpha=0.4)
        else:
            ax.grid(True, ls="--", alpha=0.5)

    # Place a single shared legend at the top
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(solvers), bbox_to_anchor=(0.5, 1.05),
               title="Solver Configurations", frameon=True, facecolor="white")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved dashboard -> {output_path}")


def generate_all_charts(csv_path: str = "results/benchmark_results.csv"):
    """Load benchmark results CSV and generate all four figures."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Cannot generate charts.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print("Warning: CSV file is empty.")
        return

    # 1. Node Expansions
    plot_grouped_metric(
        df,
        metric="nodes_expanded",
        ylabel="Nodes / Assignments (Log Scale)",
        title="Sudoku CSP: Node Expansions by Difficulty (Log Scale)",
        output_path="results/charts/node_expansions_by_difficulty.png",
        log_scale=True
    )

    # 2. Runtime
    plot_grouped_metric(
        df,
        metric="runtime_ms",
        ylabel="Execution Time in ms (Log Scale)",
        title="Sudoku CSP: Runtime (ms) by Difficulty (Log Scale)",
        output_path="results/charts/runtime_ms_by_difficulty.png",
        log_scale=True
    )

    # 3. Maximum Depth
    plot_grouped_metric(
        df,
        metric="max_depth",
        ylabel="Max Search Tree Depth",
        title="Sudoku CSP: Search Tree Depth by Difficulty",
        output_path="results/charts/search_depth_by_difficulty.png",
        log_scale=False
    )

    # 4. Summary Dashboard
    plot_summary_dashboard(df, "results/charts/summary_dashboard.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate benchmark visualization charts.")
    parser.add_argument("--csv", type=str, default="results/benchmark_results.csv", help="Path to benchmark results CSV")
    args = parser.parse_args()

    generate_all_charts(args.csv)
