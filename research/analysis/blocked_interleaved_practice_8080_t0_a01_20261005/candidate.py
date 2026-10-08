"""Synthetic schedule candidate; reads only the supplied design fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def effect_rows(schedule: list[str], design: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    seen = {variant: 0 for variant in design["training_variants"]}
    for slot, variant in enumerate(schedule):
        seen[variant] += 1
        before = False
        forward = {"kind": "in_memory_flag", "object": variant, "value": True}
        after_forward = True
        inverse = {"kind": "in_memory_flag", "object": variant, "value": False}
        after_inverse = False
        rows.append(
            {
                "slot": slot,
                "variant": variant,
                "within_variant_attempt": seen[variant],
                "materials_id": design["materials_id"],
                "feedback_event": "fixed_feedback_v1",
                "observed_forward_effect": forward,
                "observed_inverse_effect": inverse,
                "restored_initial_state": before == after_inverse,
            }
        )
        if after_forward is not True:
            raise AssertionError("synthetic forward effect did not set state")
    return rows


def build(design: dict[str, object]) -> dict[str, object]:
    variants = list(design["training_variants"])
    attempts = int(design["attempts_per_variant"])
    blocked = [variant for variant in variants for _ in range(attempts)]
    interleaved = [variants[index] for _ in range(attempts) for index in range(len(variants))]
    return {
        "schema": "blocked-interleaved-8080-candidate-v1",
        "scope": "synthetic_in_memory_only",
        "arms": {
            "blocked": {"schedule": blocked, "effects": effect_rows(blocked, design)},
            "interleaved": {
                "schedule": interleaved,
                "effects": effect_rows(interleaved, design),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, default=Path("design.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    design = json.loads(args.design.read_text())
    raw = build(design)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(f"RAW_WRITTEN {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
