#!/usr/bin/env python3
"""Single deterministic exact-rational candidate for successor #6195 T0."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from fractions import Fraction as F
from pathlib import Path

MAIN_SHA = "936a86c1026e70ee68221c773b5e367b4ed1947a"
ALLOCATION = "DELAY-GAIN-SATURATION-6195-T0-20261002-01"
GAIN, X0, CAP, LIMIT, HORIZON = F(6, 5), F(1), F(1, 2), F(3, 2), 8


def fmt(v: F) -> str:
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def clamp(v: F) -> F:
    return max(-CAP, min(CAP, v))


def trajectory(mode: str) -> dict:
    bounded = mode != "unbounded_delayed_counterfactual"
    source_ticks: list[int] = []
    inputs: list[F] = []
    states = [X0]
    saturated: list[F] = []
    for t in range(HORIZON):
        source = t if mode == "fresh_saturated" else max(0, t - 1)
        estimate = states[source]
        if mode == "history_saturated" and source < t:
            estimate += sum(inputs[source:t], F(0))
        raw = F(0) if mode == "stale_hold_saturated" and source < t else -GAIN * estimate
        command = clamp(raw) if bounded else raw
        source_ticks.append(source)
        saturated.append(abs(raw - command))
        inputs.append(command)
        states.append(states[-1] + command)
    crossing = next((i for i, x in enumerate(states[1:], 1) if abs(x) >= LIMIT), None)
    return {
        "mode": mode,
        "counterfactual_only": not bounded,
        "actuation_admissible": bounded,
        "source_ticks": source_ticks,
        "raw_commands": [fmt(x) for x in (inputs[i] + (saturated[i] if inputs[i] >= 0 else -saturated[i]) for i in range(HORIZON))],
        "inputs": [fmt(x) for x in inputs],
        "saturation_amounts": [fmt(x) for x in saturated],
        "states": [fmt(x) for x in states],
        "first_forbidden_step": crossing,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    rows = [trajectory(m) for m in ("fresh_saturated", "delayed_saturated", "history_saturated", "stale_hold_saturated", "unbounded_delayed_counterfactual")]
    doc = {
        "schema": "agent-interface/6195-delay-gain-saturation-candidate-v2",
        "allocation_id": ALLOCATION,
        "main_sha": MAIN_SHA,
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(), "device": "host CPU only"},
        "frozen": {"plant": "x[t+1]=x[t]+u[t]", "gain": "6/5", "x0": "1", "horizon": HORIZON, "cap": "1/2", "forbidden_abs_state": "3/2"},
        "trajectories": rows,
        "scope": "authored exact-rational method fixture only; no physical plant/runtime/task claim",
    }
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(f"formal output collision: {out}")
    out.parent.mkdir(parents=True, exist_ok=False)
    out.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(rows), "output": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
