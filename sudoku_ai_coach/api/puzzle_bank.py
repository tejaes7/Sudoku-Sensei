"""
Puzzle Bank Access Module:
Loads and queries graded puzzles from data/puzzle_bank.json.
"""

import os
import json
from typing import List, Dict, Any, Optional

BANK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "puzzle_bank.json"))


def load_puzzle_bank() -> Dict[str, List[Dict[str, Any]]]:
    """Load the full graded puzzle bank."""
    if not os.path.exists(BANK_PATH):
        # Fallback to building if missing
        from .puzzle_bank_builder import build_puzzle_bank
        return build_puzzle_bank()

    with open(BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_puzzles_by_tier(tier: str = "beginner") -> List[Dict[str, Any]]:
    """Return all verified puzzles for a given difficulty tier."""
    bank = load_puzzle_bank()
    clean_tier = tier.lower()
    return bank.get(clean_tier, bank.get("beginner", []))


def get_puzzle_by_id(puzzle_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single puzzle by its ID."""
    bank = load_puzzle_bank()
    for tier, plist in bank.items():
        for p in plist:
            if p.get("puzzle_id") == puzzle_id:
                return p
    return None
