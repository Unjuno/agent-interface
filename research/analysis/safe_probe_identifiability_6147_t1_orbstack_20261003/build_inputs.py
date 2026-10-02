#!/usr/bin/env python3
"""Build matched public contexts and private GUI decks before the formal freeze."""

import argparse
import json
import random
from pathlib import Path

FAMILIES = {
    "separable": ("A", "B"),
    "action_equivalent": ("C", "D"),
    "impossible": ("E", "F"),
    "stale": ("G", "H"),
    "convergent": ("I", "J"),
}
ARMS = ("adaptive", "no_probe", "one_step")


def build(seed: int) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    rng = random.Random(seed)
    public: dict[str, list[dict]] = {}
    private: dict[str, list[dict]] = {}
    for arm in ARMS:
        contexts = []
        deck = []
        index = 0
        for family, states in FAMILIES.items():
            assignment = list(states)
            rng.shuffle(assignment)
            for state in assignment:
                contexts.append({"trial_index": index, "family": family})
                deck.append({"trial_index": index, "family": family, "state_id": state})
                index += 1
        public[arm] = contexts
        private[arm] = deck
    return public, private


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    public, private = build(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        (args.out / f"contexts_{arm}.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in public[arm]),
            encoding="utf-8",
        )
        (args.out / f"deck_{arm}.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in private[arm]),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
