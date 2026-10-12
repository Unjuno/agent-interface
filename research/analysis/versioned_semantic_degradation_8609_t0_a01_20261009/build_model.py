#!/usr/bin/env python3
"""Build the frozen exhaustive input matrix for Issue #8609 T0 A01."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

SERVICES = (
    "planner",
    "raw_observer",
    "semantic_observer",
    "verifier",
    "effect_observer",
    "telemetry",
)


def build() -> dict:
    scenarios = []
    bits = itertools.product((False, True), repeat=10)
    for index, values in enumerate(bits):
        service_bits = values[:6]
        authority, release, fresh, pending = values[6:]
        scenarios.append(
            {
                "scenario_id": f"s{index:04d}",
                "available_services": dict(zip(SERVICES, service_bits)),
                "authority_granted": authority,
                "release_channel_available": release,
                "evidence_fresh": fresh,
                "pending_release_ids": ["lease-01"] if pending else [],
                "unlisted_sources": [],
            }
        )
    return {
        "schema": "semantic-degradation-model-v1",
        "services": list(SERVICES),
        "claim_order": [
            "NONE",
            "RAW_OBSERVATION",
            "SEMANTIC_OBSERVATION",
            "EFFECT_EVIDENCE_REVIEWABLE",
            "ACTION_ADMITTED",
        ],
        "scenarios": scenarios,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: build_model.py OUTPUT.json")
    output = Path(argv[1])
    output.write_text(
        json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(build()['scenarios'])} scenarios to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
