#!/usr/bin/env python3
"""Independent, bounded-memory audit of the retained #3442 model output.

Uses only the Python standard library. It never trains or imports torch.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def expected_label(state: list[float], intent: int) -> int:
    pos, vel, age, scope = state
    target = -0.8 if intent == 0 else 0.8
    error = target - pos
    if age > 0.90 or scope < 0.5 or abs(pos) > 1.10 or abs(vel) > 0.35:
        return 3
    if abs(error) <= 0.08 and abs(vel) <= 0.05:
        return 2
    return 0 if error < 0 else 1


def linear(x: list[float], state: dict[str, list], layer: int) -> list[float]:
    weights = state[f"net.{layer}.weight"]
    bias = state[f"net.{layer}.bias"]
    result = []
    for row, offset in zip(weights, bias):
        # fsum reduces dependence on host summation order; the result is then
        # rounded to the source model's float32 activation dtype.
        result.append(f32(math.fsum(float(w) * float(v) for w, v in zip(row, x)) + float(offset)))
    return result


def predict(x: list[float], weights: dict[str, list]) -> int:
    x = [f32(v) for v in x]
    x = [f32(math.tanh(v)) for v in linear(x, weights, 0)]
    x = [f32(math.tanh(v)) for v in linear(x, weights, 2)]
    logits = linear(x, weights, 4)
    return max(range(len(logits)), key=logits.__getitem__)


def input_for(state: list[float], intent: int, conditioned: bool) -> list[float]:
    return list(state) + ([1.0 if intent == i else 0.0 for i in range(2)] if conditioned else [0.0, 0.0])


def p95(values: list[float]) -> float:
    if not values:
        raise ValueError("empty latency sample")
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def evaluate(weights: dict[str, list], rows: list, conditioned: bool) -> list[int]:
    predictions = []
    for state, intent, _label, _baseline, _conditional in rows:
        predictions.append(predict(input_for(state, int(intent), conditioned), weights))
    return predictions


def audit(obj: dict) -> dict:
    errors: list[str] = []
    rows = obj.get("test_rows")
    if obj.get("schema") != "intent_aligned_needle_v1":
        errors.append("schema_mismatch")
    if obj.get("source_sha256") != "83e59427cebcbffa3c7be76e89f4ffe483727cf4f87dc0efb54539b580724751":
        errors.append("runner_source_identity_mismatch")
    if not isinstance(rows, list) or len(rows) != 1024:
        return {"audit": "FAIL", "errors": errors + ["test_row_count"]}

    truth: list[int] = []
    stored_base: list[int] = []
    stored_cond: list[int] = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 5:
            errors.append("row_shape")
            break
        state, intent, label, baseline, conditioned = row
        if len(state) != 4 or int(intent) not in (0, 1):
            errors.append("row_input_shape")
            break
        if int(label) != expected_label(state, int(intent)):
            errors.append("teacher_label_mismatch")
        truth.append(int(label))
        stored_base.append(int(baseline))
        stored_cond.append(int(conditioned))
        if i % 2 == 0:
            if int(intent) != 0 or i + 1 >= len(rows):
                errors.append("paired_intent_order")
                break
        elif int(intent) != 1 or state != rows[i - 1][0]:
            errors.append("paired_state_mismatch")
            break

    if len(truth) != 1024:
        return {"audit": "FAIL", "errors": errors + ["row_reconstruction_incomplete"]}

    model_state = obj.get("model_state", {})
    try:
        baseline = evaluate(model_state["baseline"], rows, conditioned=False)
        conditioned = evaluate(model_state["conditioned"], rows, conditioned=True)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return {"audit": "FAIL", "errors": errors + ["model_forward_error:" + type(exc).__name__]}
    if baseline != stored_base:
        errors.append("baseline_predictions_not_reproduced")
    if conditioned != stored_cond:
        errors.append("conditioned_predictions_not_reproduced")

    n = len(rows)
    base_acc = sum(a == b for a, b in zip(baseline, truth)) / n
    cond_acc = sum(a == b for a, b in zip(conditioned, truth)) / n
    base_pair = sum(baseline[k] == truth[k] and baseline[k + 1] == truth[k + 1]
                    for k in range(0, n, 2)) / (n // 2)
    cond_pair = sum(conditioned[k] == truth[k] and conditioned[k + 1] == truth[k + 1]
                    for k in range(0, n, 2)) / (n // 2)
    latencies = obj["latency_samples_ms"]
    metrics = {
        "baseline_accuracy": base_acc,
        "conditioned_accuracy": cond_acc,
        "accuracy_gain": cond_acc - base_acc,
        "baseline_paired_intent_exact": base_pair,
        "conditioned_paired_intent_exact": cond_pair,
        "baseline_cpu_p95_ms": p95(latencies["baseline"]),
        "conditioned_cpu_p95_ms": p95(latencies["conditioned"]),
    }
    for key, actual in metrics.items():
        if abs(float(obj["metrics"][key]) - actual) > 1e-9:
            errors.append("metric_mismatch:" + key)

    count = n
    gates = {
        "conditioned_accuracy_ge_0_95": cond_acc >= 0.95,
        "accuracy_gain_ge_0_20": cond_acc - base_acc >= 0.20,
        "conditioned_paired_exact_ge_0_90": cond_pair >= 0.90,
        "stale_intent_all_yield": obj["metrics"]["gate_counts"]["stale_intent_yield"] == count,
        "stale_evidence_all_yield": obj["metrics"]["gate_counts"]["stale_evidence_yield"] == count,
        "unknown_intent_all_yield": obj["metrics"]["gate_counts"]["unknown_intent_yield"] == count,
        "matched_context_all_propose": obj["metrics"]["gate_counts"]["matched_propose"] == count,
        "conditioned_cpu_p95_lt_60ms": metrics["conditioned_cpu_p95_ms"] < 60.0,
    }
    if obj.get("gates") != gates:
        errors.append("gate_mismatch")
    decision = "PASS_INTENT_CONDITIONING_SYNTHETIC_SCOPED" if all(gates.values()) else "HOLD_OR_FAIL_GATE_MISS"
    if obj.get("outcome") != decision:
        errors.append("outcome_mismatch")
    return {
        "audit": "PASS" if not errors else "FAIL",
        "errors": errors,
        "rows_recomputed": n,
        "metrics_recomputed": metrics,
        "gates_recomputed": gates,
        "decision_recomputed": decision,
    }


def audit_bytes(raw: bytes, expected_sha256: str) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        return {"audit": "FAIL", "errors": ["result_sha256_mismatch"], "result_sha256": digest}
    try:
        obj = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"audit": "FAIL", "errors": ["result_json_invalid"], "result_sha256": digest}
    result = audit(obj)
    result["result_sha256"] = digest
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: audit_stdlib.py RESULT.json EXPECTED_SHA256", file=sys.stderr)
        return 64
    raw = Path(sys.argv[1]).read_bytes()
    result = audit_bytes(raw, sys.argv[2])
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if result["audit"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
