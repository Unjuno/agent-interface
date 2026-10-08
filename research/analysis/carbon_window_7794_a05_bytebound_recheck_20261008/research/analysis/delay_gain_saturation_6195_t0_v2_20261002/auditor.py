#!/usr/bin/env python3
"""Independent raw-only exact reconstruction; imports no candidate module."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

BASE = Fraction(1)
K = Fraction(6, 5)
BOUND = Fraction(1, 2)
LIMIT = Fraction(3, 2)
STEPS = 8
ALLOCATION = "DELAY-GAIN-SATURATION-6195-T0-20261002-01"
MAIN = "936a86c1026e70ee68221c773b5e367b4ed1947a"


def text(q: Fraction) -> str:
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def reconstruct(kind: str) -> dict:
    legal = kind != "unbounded_delayed_counterfactual"
    xx = [BASE]
    uu: list[Fraction] = []
    ticks: list[int] = []
    losses: list[Fraction] = []
    for n in range(STEPS):
        obs = n if kind == "fresh_saturated" else max(0, n - 1)
        estimate = xx[obs]
        if kind == "history_saturated" and obs < n:
            estimate = estimate + sum(uu[obs:n], Fraction(0))
        request = Fraction(0) if kind == "stale_hold_saturated" and obs < n else -K * estimate
        applied = max(-BOUND, min(BOUND, request)) if legal else request
        ticks.append(obs)
        losses.append(abs(request - applied))
        uu.append(applied)
        xx.append(xx[-1] + applied)
    first = next((j for j, value in enumerate(xx[1:], 1) if abs(value) >= LIMIT), None)
    return {"mode": kind, "counterfactual_only": not legal, "actuation_admissible": legal,
            "source_ticks": ticks,
            "raw_commands": [text(u + loss if u >= 0 else u - loss) for u, loss in zip(uu, losses)],
            "inputs": [text(u) for u in uu], "saturation_amounts": [text(z) for z in losses],
            "states": [text(x) for x in xx], "first_forbidden_step": first}


def valid(doc: dict) -> bool:
    expected_modes = ("fresh_saturated", "delayed_saturated", "history_saturated", "stale_hold_saturated", "unbounded_delayed_counterfactual")
    if doc.get("schema") != "agent-interface/6195-delay-gain-saturation-candidate-v2" or doc.get("allocation_id") != ALLOCATION or doc.get("main_sha") != MAIN:
        return False
    if doc.get("frozen") != {"plant": "x[t+1]=x[t]+u[t]", "gain": "6/5", "x0": "1", "horizon": 8, "cap": "1/2", "forbidden_abs_state": "3/2"}:
        return False
    rows = doc.get("trajectories")
    if not isinstance(rows, list) or len(rows) != len(expected_modes):
        return False
    if [r.get("mode") for r in rows] != list(expected_modes):
        return False
    if rows != [reconstruct(m) for m in expected_modes]:
        return False
    for row in rows:
        if row["actuation_admissible"] and any(abs(F(v)) > BOUND for v in row["inputs"]):
            return False
    return (rows[2]["states"] == rows[0]["states"] and rows[2]["inputs"] == rows[0]["inputs"]
            and rows[1]["first_forbidden_step"] is None
            and rows[4]["first_forbidden_step"] == 5
            and rows[4]["counterfactual_only"] is True and rows[4]["actuation_admissible"] is False)


def corruption_corpus(doc: dict) -> list[dict]:
    variants = []
    d = copy.deepcopy(doc); d["trajectories"][0]["inputs"][0] = "-6/5"; variants.append(("actuator_cap_violation", d))
    d = copy.deepcopy(doc); d["trajectories"].pop(); variants.append(("row_deletion", d))
    d = copy.deepcopy(doc); d["trajectories"][4]["actuation_admissible"] = True; d["trajectories"][4]["counterfactual_only"] = False; variants.append(("counterfactual_relabel", d))
    d = copy.deepcopy(doc); d["trajectories"][1]["source_ticks"][3] += 1; variants.append(("source_tick_drift", d))
    d = copy.deepcopy(doc); d["trajectories"][1]["first_forbidden_step"] = 5; variants.append(("forged_boundary_crossing", d))
    return [{"corruption": name, "rejected": not valid(mutated)} for name, mutated in variants]


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--input", required=True); ap.add_argument("--output", required=True); args = ap.parse_args()
    raw = Path(args.input).read_bytes(); doc = json.loads(raw)
    probes = corruption_corpus(doc); errors = []
    if not valid(doc): errors.append("raw candidate differs from independently reconstructed frozen trajectories")
    if len(probes) != 5 or not all(p["rejected"] for p in probes): errors.append("a frozen corruption was accepted")
    result = {"schema": "agent-interface/6195-delay-gain-saturation-audit-v2", "allocation_id": ALLOCATION,
              "input_sha256": hashlib.sha256(raw).hexdigest(), "pristine_reconstructed": valid(doc),
              "rows_reconstructed": 5 if valid(doc) else 0, "corruption_probes": probes,
              "errors": errors, "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT_METHOD"}
    out = Path(args.output)
    if out.exists(): raise FileExistsError(f"formal output collision: {out}")
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "corruptions_rejected": sum(p["rejected"] for p in probes), "errors": errors}))
    return 0 if not errors else 2


if __name__ == "__main__": raise SystemExit(main())
