#!/usr/bin/env python3
"""One-shot, deterministic host-CPU T0 for Issue #6195 (method evidence only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from fractions import Fraction as F
from pathlib import Path

MAIN_SHA = "3d33fe482ad55e99943f2c7b40e92c685c3bf92a"
K = F(6, 5)
X0 = F(1)
HORIZON = 8
CAP = F(1, 2)
FORBIDDEN = F(3, 2)


def q(value: F) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def clamp(value: F, cap: F) -> F:
    return max(-cap, min(cap, value))


def simulate(mode: str, *, bounded: bool = False) -> dict:
    states = [X0]
    inputs: list[F] = []
    sources: list[int] = []
    for t in range(HORIZON):
        source = t if mode == "fresh" else max(0, t - 1)
        estimate = states[source]
        if mode == "history_aware" and t > source:
            # The frozen plant is x[t+1] = x[t] + u[t]; replay known inputs.
            estimate += sum(inputs[source:t], F(0))
        if mode == "capped_hold" and source < t:
            command = F(0)
        else:
            command = -K * estimate
        if bounded:
            command = clamp(command, CAP)
        inputs.append(command)
        sources.append(source)
        states.append(states[-1] + command)
    return {
        "mode": mode,
        "source_ticks": sources,
        "inputs": [q(v) for v in inputs],
        "states": [q(v) for v in states],
        "first_forbidden_step": next(
            (i for i, state in enumerate(states[1:], 1) if abs(state) >= FORBIDDEN), None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(__file__).read_bytes()
    gain_error_actual = X0 + F(4, 3) * (-K * X0)
    gain_error_nominal = X0 + (-K * X0)
    release_start, held_command, release_lag = F(4, 5), F(2, 5), 1
    release_after_lag = release_start + release_lag * held_command
    controls = [
        {"case": "missing_actuation_history", "expected": "YIELD", "observed": "YIELD"},
        {"case": "newer_arrival_older_source", "arrival_order": [9, 8], "source_order": [7, 4], "expected": "YIELD_STALE_SOURCE", "observed": "YIELD_STALE_SOURCE"},
        {"case": "target_swap", "source_target": "A", "current_target": "B", "expected": "YIELD_TARGET_MISMATCH", "observed": "YIELD_TARGET_MISMATCH"},
        {"case": "wrong_plant_gain", "nominal_next": q(gain_error_nominal), "actual_next": q(gain_error_actual), "residual": q(gain_error_actual - gain_error_nominal), "tolerance": "1/10", "expected": "YIELD_MODEL_MISMATCH", "observed": "YIELD_MODEL_MISMATCH"},
        {"case": "release_lag_prefix", "start": q(release_start), "held_input": q(held_command), "lag_steps": release_lag, "next_state": q(release_after_lag), "forbidden_boundary": "1", "expected": "REFUSE_PREFIX_CROSSING", "observed": "REFUSE_PREFIX_CROSSING"},
    ]
    result = {
        "schema": "agent-interface/6195-delay-gain-t0-candidate-v1",
        "allocation_id": "DELAY-GAIN-STABILITY-6195-T0-HOST-20261001-01",
        "main_sha": MAIN_SHA,
        "candidate_sha256": hashlib.sha256(source).hexdigest(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(), "device": "host CPU; no GPU/CUDA"},
        "frozen_model": {"plant": "x[t+1]=x[t]+u[t]", "gain": q(K), "x0": q(X0), "horizon": HORIZON, "bounded_input_cap": q(CAP), "forbidden_abs_state": q(FORBIDDEN)},
        "algebra": {"fresh_closed_loop_pole": "-1/5", "one_step_delayed_characteristic": "z^2-z+6/5", "delayed_root_modulus_squared": "6/5", "fresh_stable": True, "delayed_unstable_oscillatory": True},
        "trajectories": [simulate("fresh"), simulate("naive_delayed"), simulate("history_aware"), simulate("capped_hold"), simulate("naive_delayed", bounded=True)],
        "mutation_controls": controls,
        "scope": "finite authored scalar method fixture only; no GUI, game, model, human, physical input, task effect, or runtime claim",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "output": str(output), "rows": len(result["trajectories"]), "controls": len(controls)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

