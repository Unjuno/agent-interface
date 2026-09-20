"""Independent raw-row audit for #3847. Does not import runner.py."""
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

import torch
from torch import nn

NAMES = ("CONTINUE", "CORRECT", "WATCH")
EXPECTED_SEEDS = (3464, 3465, 3466)
GATES = {"accuracy": .95, "coverage": .75, "recall": .95, "false_correct": .005,
         "p95_ms": 60.0}


def label(x):
    dx, dy, vx, vy, confidence, visible = x
    if confidence < .72 or visible < .5:
        return 2
    if abs(dx) < .06 and abs(dy) < .06 and abs(vx) + abs(vy) < .12:
        return 0
    return 1


def expected_reason(meta, x):
    if meta != {"intent": "track_target", "scope": "local-servo", "epoch": 7}:
        return "YIELD_METADATA"
    if any(not math.isfinite(v) for v in x):
        return "YIELD_NONFINITE"
    dx, dy, vx, vy, confidence, visible = x
    if max(abs(dx), abs(dy)) > 1.25 or max(abs(vx), abs(vy)) > 1.0 or not 0 <= confidence <= 1 or visible not in (0., 1.):
        return "YIELD_ENVELOPE"
    if (abs(confidence - .72) < .03 or abs(abs(dx) - .06) < .01 or abs(abs(dy) - .06) < .01
            or abs(abs(vx) + abs(vy) - .12) < .02):
        return "YIELD_BOUNDARY"
    return "PROPOSAL"


def summarize(rows):
    accepted = [r for r in rows if r["proposal"] in NAMES]
    n = len(rows)
    correct = sum(NAMES[r["y"]] == r["proposal"] for r in accepted)
    by_class = {}
    for i, name in enumerate(NAMES):
        actual = [r for r in rows if r["y"] == i]
        acc = [r for r in actual if r["proposal"] in NAMES]
        by_class[name] = {
            "n": len(actual), "accepted": len(acc), "coverage": len(acc) / max(1, len(actual)),
            "recall": sum(r["proposal"] == name for r in acc) / max(1, len(acc)),
}


class AuditNeedle(nn.Module):
    """Independent fixed-shape reconstruction; runner source is not imported."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(6, 16), nn.Tanh(), nn.Linear(16, 16), nn.Tanh(), nn.Linear(16, 3))

    def forward(self, x):
        return self.net(x)


def reconstruct_model(state):
    model = AuditNeedle()
    params = dict(model.named_parameters())
    if set(state) != set(params):
        raise ValueError("model parameter names mismatch")
    tensors = {}
    for name, item in state.items():
        if list(params[name].shape) != item.get("shape"):
            raise ValueError(f"model parameter shape mismatch: {name}")
        t = torch.tensor(item.get("values"), dtype=torch.float32).reshape(item["shape"])
        tensors[name] = t
    model.load_state_dict(tensors, strict=True)
    model.eval()
    return model
    false_correct = sum(r["proposal"] == "CORRECT" and r["y"] != 1 for r in accepted)
    return {"n": n, "accepted": len(accepted), "accuracy": correct / max(1, len(accepted)),
            "by_class": by_class, "false_correct": false_correct,
            "false_correct_rate": false_correct / max(1, len(accepted))}


def audit(result):
    errors = []
    if result.get("allocation") != "needle-intent-distill-3458-pilot-05-near-boundary-shift":
        errors.append("allocation mismatch")
    seeds = result.get("seeds", [])
    if tuple(s.get("seed") for s in seeds) != EXPECTED_SEEDS:
        errors.append("seed list/order mismatch")
    reports = []
    for seed_result in seeds:
        sid = seed_result["seed"]
        state = seed_result.get("model_state", {})
        state_bytes = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(state_bytes).hexdigest() != seed_result.get("model_state_sha256"):
            errors.append(f"seed {sid}: model state hash mismatch")
        try:
            model = reconstruct_model(state)
        except Exception as exc:
            errors.append(f"seed {sid}: model state reconstruction failed: {type(exc).__name__}")
            model = None
        for suite_name in ("iid_control", "near_boundary_shift"):
            suite = seed_result.get(suite_name, {})
            if suite.get("name") != suite_name or len(suite.get("rows", [])) != 3072:
                errors.append(f"seed {sid}: {suite_name} shape mismatch")
            for j, row in enumerate(suite.get("rows", [])):
                x = row.get("x", [])
                if len(x) != 6 or any(not math.isfinite(float(v)) for v in x):
                    errors.append(f"seed {sid}: {suite_name} row {j} feature shape/value")
                    continue
                actual_y = label(x)
                if row.get("y") != actual_y:
                    errors.append(f"seed {sid}: {suite_name} row {j} teacher label mismatch")
                reason = expected_reason({"intent": "track_target", "scope": "local-servo", "epoch": 7}, x)
                if suite_name == "near_boundary_shift" and actual_y == 1:
                    if not .071 <= abs(x[0]) <= .149 or abs(x[1]) > .10 or max(abs(x[2]), abs(x[3])) > .05:
                        errors.append(f"seed {sid}: shifted CORRECT row {j} outside preregistered covariate shift")
                if row.get("reason") != reason:
                    errors.append(f"seed {sid}: {suite_name} row {j} reason mismatch")
                if reason == "PROPOSAL" and row.get("proposal") not in NAMES:
                    errors.append(f"seed {sid}: {suite_name} row {j} invalid proposal")
                if reason != "PROPOSAL" and row.get("proposal") is not None:
                    errors.append(f"seed {sid}: {suite_name} row {j} proposed after yield")
            if model is not None and suite.get("rows"):
                valid_rows = [r for r in suite["rows"] if expected_reason({"intent": "track_target", "scope": "local-servo", "epoch": 7}, r["x"]) == "PROPOSAL"]
                if valid_rows:
                    with torch.no_grad():
                        predictions = model(torch.tensor([r["x"] for r in valid_rows], dtype=torch.float32)).argmax(-1).tolist()
                    for row, pred in zip(valid_rows, predictions):
                        if row.get("proposal") != NAMES[pred]:
                            errors.append(f"seed {sid}: {suite_name} learned prediction mismatch")
            summary = summarize(suite.get("rows", []))
            if [summary["by_class"][name]["n"] for name in NAMES] != [1024, 1024, 1024]:
                errors.append(f"seed {sid}: {suite_name} is not balanced by independently recomputed labels")
            reports.append({"seed": sid, "suite": suite_name, **summary})
        bounds = seed_result.get("boundary", [])
        if len(bounds) != 1536:
            errors.append(f"seed {sid}: boundary count mismatch")
        for j, row in enumerate(bounds):
            x = row.get("x", [])
            if row.get("y") != label(x) or row.get("reason") != "YIELD_BOUNDARY" or row.get("proposal") is not None:
                errors.append(f"seed {sid}: boundary row {j} not correctly yielded/audited")
        invalid = seed_result.get("invalid_controls", [])
        expected_invalid = ["YIELD_METADATA", "YIELD_METADATA", "YIELD_METADATA", "YIELD_ENVELOPE", "YIELD_NONFINITE"]
        if len(invalid) != 5 or [v.get("reason") for v in invalid] != expected_invalid or any(v.get("proposal") is not None for v in invalid):
            errors.append(f"seed {sid}: invalid controls mismatch")
        lat = seed_result.get("latency_ms", [])
        if len(lat) != 2000 or any(not math.isfinite(v) or v < 0 for v in lat):
            errors.append(f"seed {sid}: latency vector invalid")
            p95 = math.inf
        else:
            ordered = sorted(lat)
            p95 = ordered[int(.95 * (len(ordered) - 1))]
        reports[-1]["cpu_single_row_p95_ms"] = p95
    shifted_reports = [r for r in reports if r["suite"] == "near_boundary_shift"]
    passes = len(shifted_reports) == 3
    for r in shifted_reports:
        passes &= r["accuracy"] >= GATES["accuracy"]
        passes &= r["false_correct_rate"] <= GATES["false_correct"]
        passes &= r["cpu_single_row_p95_ms"] < GATES["p95_ms"]
        passes &= all(v["coverage"] >= GATES["coverage"] and v["recall"] >= GATES["recall"] for v in r["by_class"].values())
    passes &= len(errors) == 0
    return {"allocation": result.get("allocation"), "decision": "PASS_NEAR_BOUNDARY_SHIFT_SCOPED" if passes else "FAIL_OR_HOLD_NEAR_BOUNDARY_SHIFT",
            "gates": GATES, "reports": reports, "boundary_yield_counts": [sum(r["reason"] == "YIELD_BOUNDARY" for r in s.get("boundary", [])) for s in seeds],
            "errors": errors}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    raw = Path(args.result).read_bytes()
    result = json.loads(raw)
    audited = audit(result)
    audited["formal_result_sha256"] = hashlib.sha256(raw).hexdigest()
    data = (json.dumps(audited, sort_keys=True, indent=2) + "\n").encode()
    Path(args.out).write_bytes(data)
    print(json.dumps({"decision": audited["decision"], "errors": len(audited["errors"]),
                      "audit_sha256": hashlib.sha256(data).hexdigest()}))
    if audited["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
