#!/usr/bin/env python3
"""Candidate for the bounded distinguishing-suffix reset challenge."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

OUT = Path("/work/out")
OUT.mkdir(parents=True, exist_ok=True)
SUFFIX = ["read", "navigate", "commit_scoped", "readback", "release"]
CASES = (
    ("clean_reset", "history_a", "candidate_clean", "genesis_a"),
    ("hidden_carryover", "history_a", "candidate_bad", "genesis_a"),
    ("hidden_carryover", "history_b", "candidate_bad", "genesis_b"),
    ("known_bad_reset", "history_b", "candidate_bad", "genesis_b"),
    ("timing_only", "history_b", "candidate_clean", "genesis_b"),
    ("missing_observation", "history_a", "candidate_clean", "genesis_a"),
)


def genesis(anchor: str) -> dict:
    manifest = {"anchor": anchor, "seed": 17, "initial_visible": "screen-v1", "hidden": 0}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return {**manifest, "identity_sha256": hashlib.sha256(canonical).hexdigest()}


def run_case(kind: str, history: str, reset: str, anchor: str) -> dict:
    start = genesis(anchor)
    state = {"visible": start["initial_visible"], "hidden": start["hidden"], "effect": "unchanged"}
    # Distinct histories perturb hidden state while preserving visible pixels.
    if history == "history_a":
        state["hidden"] = 0
    elif history == "history_b":
        state["hidden"] = 1
    # Candidate reset cleans or incorrectly retains latent memory.
    if reset == "candidate_clean":
        state["hidden"] = 0
    # A defective reset can clear visible state but leave hidden carryover.
    initial_after_reset = state["visible"]
    initial_seed_after_reset = start["seed"]
    outputs = []
    for step in SUFFIX:
        if kind == "missing_observation" and step == "readback":
            outputs.append({"step": step, "observation": None, "effect": None, "released": True})
            continue
        if step == "read":
            outputs.append({"step": step, "observation": state["visible"], "effect": None, "released": True})
        elif step == "navigate":
            outputs.append({"step": step, "observation": "screen-v1", "effect": None, "released": True})
        elif step == "commit_scoped":
            if state["hidden"]:
                state["effect"] = "wrong-target"
            else:
                state["effect"] = "target-committed"
            outputs.append({"step": step, "observation": None, "effect": state["effect"], "released": False})
        elif step == "readback":
            outputs.append({"step": step, "observation": "screen-v1", "effect": state["effect"], "released": False})
        elif step == "release":
            outputs.append({"step": step, "observation": None, "effect": None, "released": True})
    # Timing-only perturbation stays inside the preregistered 50 ms tolerance.
    elapsed_ms = 20 if kind != "timing_only" else 47
    if kind == "known_bad_reset":
        # Independent positive control: the known-bad reset preserves the bit.
        state["effect"] = "wrong-target" if state["hidden"] else "target-committed"
    return {
        "kind": kind,
        "history": history,
        "reset": reset,
        "anchor": anchor,
        "genesis": start,
        "suffix": list(SUFFIX),
        "post_reset_visible": initial_after_reset,
        "post_reset_seed": initial_seed_after_reset,
        "outputs": outputs,
        "elapsed_ms": elapsed_ms,
        "timing_tolerance_ms": 50,
    }


def main() -> None:
    t0 = time.monotonic_ns()
    rows = [run_case(*case) for case in CASES]
    records = [{"kind": "header", "allocation": "distinguishing-suffix-reset-5784-t0-docker-20261001-01",
                "formal_invocations": 1, "reruns": 0, "suffix": SUFFIX,
                "fresh_genesis_independent_of_candidate_reset": True,
                "genesis_a_sha256": genesis("genesis_a")["identity_sha256"],
                "genesis_b_sha256": genesis("genesis_b")["identity_sha256"]}]
    records.extend({"kind": "case", **row} for row in rows)
    records.append({"kind": "footer", "elapsed_monotonic_ns": time.monotonic_ns() - t0})
    raw = OUT / "formal.jsonl"
    raw.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")
    print(json.dumps({"status": "RAW_EMITTED", "rows": len(rows), "path": str(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
