"""
Live Board Analysis Module - Milestone 0.
Computes candidate domains, MRV variable, singletons, and constraint analytics for any partial board state.
"""

import sys
import os
from typing import Dict, Set, List, Any, Optional, Tuple

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.board import SQUARES, PEERS, SQUARE_TO_COORD
from .board_state import BoardState


def compute_domains(grid: List[List[int]]) -> Tuple[Dict[str, Set[int]], bool]:
    """
    Compute candidate domains for all 81 cells based on current grid state.
    Returns:
        domains: Dict[str, Set[int]]
        contradiction: bool (True if any cell has an empty domain)
    """
    domains: Dict[str, Set[int]] = {s: set(range(1, 10)) for s in SQUARES}
    contradiction = False

    # Fixed assigned cells
    for s in SQUARES:
        r, c = SQUARE_TO_COORD[s]
        val = grid[r][c]
        if val != 0:
            domains[s] = {val}

    # Forward check: remove assigned values from all peers
    for s in SQUARES:
        r, c = SQUARE_TO_COORD[s]
        val = grid[r][c]
        if val != 0:
            for peer in PEERS[s]:
                peer_r, peer_c = SQUARE_TO_COORD[peer]
                # If peer is unassigned, prune val
                if grid[peer_r][peer_c] == 0:
                    domains[peer].discard(val)
                    if len(domains[peer]) == 0:
                        contradiction = True

    return domains, contradiction


def analyze_board(board_state: BoardState) -> Dict[str, Any]:
    """
    Analyze the current board state and extract candidate domains,
    the MRV cell, singleton counts, contradiction flags, and telemetry metrics.
    """
    grid = board_state.board.grid
    domains_set, has_contradiction = compute_domains(grid)

    # Format domains as string of sorted digits (e.g. "137")
    formatted_domains: Dict[str, str] = {}
    unassigned_cells: List[str] = []
    singleton_cells: List[str] = []

    for s in SQUARES:
        r, c = SQUARE_TO_COORD[s]
        val = grid[r][c]
        d_str = "".join(str(d) for d in sorted(domains_set[s]))
        formatted_domains[s] = d_str
        if val == 0:
            unassigned_cells.append(s)
            if len(domains_set[s]) == 1:
                singleton_cells.append(s)
            elif len(domains_set[s]) == 0:
                has_contradiction = True

    unassigned_count = len(unassigned_cells)

    # Minimum Remaining Values (MRV) selection with Degree Heuristic tiebreak
    mrv_cell: Optional[str] = None
    min_domain_size = 9
    avg_domain_size = 0.0

    if unassigned_cells:
        # Calculate domain sizes for unassigned
        domain_sizes = [len(domains_set[s]) for s in unassigned_cells]
        avg_domain_size = round(sum(domain_sizes) / len(domain_sizes), 2)
        min_domain_size = min(domain_sizes) if domain_sizes else 0

        # Candidates tying for minimum domain size
        tied_candidates = [s for s in unassigned_cells if len(domains_set[s]) == min_domain_size]

        # Degree Heuristic tiebreak: pick cell with most unassigned peers
        def unassigned_peer_count(sq: str) -> int:
            return sum(1 for p in PEERS[sq] if board_state.get_cell_value(p) == 0)

        mrv_cell = max(tied_candidates, key=unassigned_peer_count)

    # Backtracking required: true if puzzle not complete, but no direct naked singles ready
    backtracking_required = (unassigned_count > 0) and (len(singleton_cells) == 0)

    reasoning_mode = "Completed" if unassigned_count == 0 else (
        "Immediate Contradiction" if has_contradiction else (
            "Deductive (Naked Singles Available)" if len(singleton_cells) > 0 else (
                "Search / Backtracking Required"
            )
        )
    )

    return {
        "domains": formatted_domains,
        "unassigned_count": unassigned_count,
        "clue_count": board_state.board.clue_count,
        "mrv_cell": mrv_cell,
        "min_domain_size": min_domain_size if unassigned_cells else 0,
        "avg_domain_size": avg_domain_size,
        "singleton_cells": singleton_cells,
        "singleton_count": len(singleton_cells),
        "contradiction": has_contradiction,
        "backtracking_required": backtracking_required,
        "reasoning_mode": reasoning_mode,
    }
