"""Read-only source-bound eligibility check for Issue #7799 T0."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys


SOURCE_PATHS = (
    "research/live_control/INTEGRATED_EFFICIENCY_PLAN_V1.md",
    "research/live_control/integrated_efficiency_protocol_v1.py",
)
EXPECTED_COMMIT = "b5be19963454ce5edafc945b78b100012952dd15"
ARMS = ("plain", "ephemeral", "persistent")
CELLS = ((0, 0), (0, 1), (1, 0), (1, 1))


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py SOURCE_ROOT OUTPUT_JSON")
    root = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    plan = (root / SOURCE_PATHS[0]).read_text(encoding="utf-8")
    protocol = (root / SOURCE_PATHS[1]).read_text(encoding="utf-8")
    arm_tuple = re.search(r'^ARMS\s*=\s*\(([^\n]+)\)', protocol, re.M)
    if not arm_tuple:
        raise ValueError("frozen protocol arm tuple missing")
    parsed_arms = tuple(re.findall(r"['\"]([^'\"]+)['\"]", arm_tuple.group(1)))
    if parsed_arms != ARMS:
        raise ValueError(f"unexpected frozen protocol arms: {parsed_arms!r}")
    required_plan_facts = {
        "representation_and_local_execution_share_compiled_interface":
            "| Representation | `compiled_gui_interface_v1` plus point-derived scoped target handles |",
        "local_execution_uses_same_compiled_interface":
            "| Local execution | `compiled_gui_interface_v1` |",
        "ephemeral_combines_handles_and_local_continuation":
            "scoped handles and local continuation execute the task",
        "persistent_cold_path_matches_ephemeral":
            "Cold behavior is identical to B.",
        "other_evidence_compression_variants_excluded":
            "planner-evidence compression variants",
    }
    observed = {name: needle in plan for name, needle in required_plan_facts.items()}
    if not all(observed.values()):
        raise ValueError(f"selected-plan facts changed: {observed!r}")

    # Factors are representation (R) and local continuation (L). The selected
    # plan only exposes plain (0,0) and the compiled B/C arms (1,1); B/C differ
    # in persistence, not either selected factor.
    arm_cells = {
        "plain": [0, 0],
        "ephemeral": [1, 1],
        "persistent": [1, 1],
    }
    observed_cells = sorted({tuple(v) for v in arm_cells.values()})
    missing = [list(cell) for cell in CELLS if cell not in observed_cells]
    result = {
        "schema": "issue-7799-pairwise-eligibility-t0-v1",
        "source_commit": EXPECTED_COMMIT,
        "source_sha256": {
            path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in SOURCE_PATHS
        },
        "protocol_arms": list(parsed_arms),
        "candidate_pair": ["compiled symbolic representation/target handles",
                           "local continuation"],
        "arm_factor_values": arm_cells,
        "required_2x2_cells": [list(cell) for cell in CELLS],
        "observed_factor_cells": [list(cell) for cell in observed_cells],
        "missing_factor_cells": missing,
        "selected_plan_facts": observed,
        "eligibility": "HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR",
        "reason": "The selected plan couples representation and local continuation in both compiled arms; the protocol has only plain/ephemeral/persistent, and the persistent arm adds reuse rather than an independent setting for either factor.",
        "scope": "source-bound eligibility only; no outcome or interaction estimate",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
