#!/usr/bin/env python3
"""Separate raw-only verifier for Issue #6195 candidate output; imports no candidate code."""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

EXPECTED_MAIN = "3d33fe482ad55e99943f2c7b40e92c685c3bf92a"
EXPECTED_ID = "DELAY-GAIN-STABILITY-6195-T0-HOST-20261001-01"
N = 8
GAIN = Fraction(6, 5)
CAP = Fraction(1, 2)
LIMIT = Fraction(3, 2)


def parse(value: str) -> Fraction:
    return Fraction(value)


def fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def reference(mode: str, bounded: bool = False) -> dict:
    x = [Fraction(1)]
    u: list[Fraction] = []
    ticks: list[int] = []
    for t in range(N):
        s = t if mode == "fresh" else max(t - 1, 0)
        xhat = x[s]
        if mode == "history_aware" and s < t:
            xhat = xhat + sum(u[s:t], Fraction(0))
        effort = Fraction(0) if mode == "capped_hold" and s != t else -GAIN * xhat
        if bounded:
            effort = max(-CAP, min(CAP, effort))
        u.append(effort)
        ticks.append(s)
        x.append(x[-1] + effort)
    crossing = None
    for index, value in enumerate(x[1:], 1):
        if abs(value) >= LIMIT:
            crossing = index
            break
    return {"mode": mode, "source_ticks": ticks, "inputs": [fmt(v) for v in u], "states": [fmt(v) for v in x], "first_forbidden_step": crossing}


def validate(doc: dict) -> bool:
    if doc.get("schema") != "agent-interface/6195-delay-gain-t0-candidate-v1":
        return False
    if doc.get("main_sha") != EXPECTED_MAIN or doc.get("allocation_id") != EXPECTED_ID:
        return False
    if doc.get("algebra") != {"fresh_closed_loop_pole": "-1/5", "one_step_delayed_characteristic": "z^2-z+6/5", "delayed_root_modulus_squared": "6/5", "fresh_stable": True, "delayed_unstable_oscillatory": True}:
        return False
    want = [reference("fresh"), reference("naive_delayed"), reference("history_aware"), reference("capped_hold"), reference("naive_delayed", bounded=True)]
    if doc.get("trajectories") != want:
        return False
    controls = doc.get("mutation_controls")
    if not isinstance(controls, list) or len(controls) != 5:
        return False
    by_case = {x.get("case"): x for x in controls if isinstance(x, dict)}
    if len(by_case) != 5:
        return False
    if by_case.get("missing_actuation_history", {}).get("observed") != "YIELD":
        return False
    stale = by_case.get("newer_arrival_older_source", {})
    if stale.get("source_order") != [7, 4] or stale.get("observed") != "YIELD_STALE_SOURCE":
        return False
    swapped = by_case.get("target_swap", {})
    if swapped.get("source_target") == swapped.get("current_target") or swapped.get("observed") != "YIELD_TARGET_MISMATCH":
        return False
    gain = by_case.get("wrong_plant_gain", {})
    if abs(parse(gain.get("residual", "0"))) <= parse(gain.get("tolerance", "1")) or gain.get("observed") != "YIELD_MODEL_MISMATCH":
        return False
    lag = by_case.get("release_lag_prefix", {})
    if parse(lag.get("next_state", "0")) < parse(lag.get("forbidden_boundary", "0")) or lag.get("observed") != "REFUSE_PREFIX_CROSSING":
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = Path(args.input).read_bytes()
    candidate = json.loads(raw)
    pristine = validate(candidate)
    probes = []
    mutations = [
        lambda d: d["trajectories"].pop(),
        lambda d: d["trajectories"][0]["states"].__setitem__(1, "999"),
        lambda d: d["mutation_controls"][0].__setitem__("observed", "ACT"),
        lambda d: d["mutation_controls"][2].__setitem__("current_target", "A"),
        lambda d: d.__setitem__("main_sha", "0" * 40),
    ]
    for index, mutate in enumerate(mutations, 1):
        altered = json.loads(json.dumps(candidate))
        mutate(altered)
        probes.append({"mutation": index, "rejected": not validate(altered)})
    errors = []
    if not pristine:
        errors.append("pristine candidate did not match independent exact reconstruction")
    if any(not p["rejected"] for p in probes):
        errors.append("one or more corruption probes were accepted")
    audit = {
        "schema": "agent-interface/6195-delay-gain-t0-audit-v1",
        "allocation_id": EXPECTED_ID,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "pristine_reconstructed": pristine,
        "trajectory_rows_reconstructed": 5 if pristine else 0,
        "corruption_probes": probes,
        "errors": errors,
        "disposition": "PASS_AUDIT_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "scope": "independent exact-rational reconstruction of authored method fixture only; no transfer claim",
    }
    Path(args.output).write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": audit["disposition"], "rows": audit["trajectory_rows_reconstructed"], "corruptions_rejected": sum(p["rejected"] for p in probes), "errors": errors}))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

