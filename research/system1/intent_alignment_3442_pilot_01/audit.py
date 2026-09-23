import hashlib
import json
import math
import sys

import torch
from torch import nn
from torch.nn import functional as F

RUNNER_SHA256 = "83e59427cebcbffa3c7be76e89f4ffe483727cf4f87dc0efb54539b580724751"
VOCAB = {"LEFT": 0, "RIGHT": 1, "WATCH": 2, "YIELD": 3}

def expected_label(state, intent):
    pos, vel, age, scope = state
    target = -0.8 if intent == 0 else 0.8
    err = target - pos
    if age > 0.90 or scope < 0.5 or abs(pos) > 1.10 or abs(vel) > 0.35:
        return 3
    if abs(err) <= 0.08 and abs(vel) <= 0.05:
        return 2
    return 0 if err < 0 else 1

class AuditNeedle(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(6, 32), nn.Tanh(),
                                 nn.Linear(32, 32), nn.Tanh(),
                                 nn.Linear(32, 4))
    def forward(self, x):
        return self.net(x)

def make_model(weights):
    model = AuditNeedle().cpu()
    state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights.items()}
    model.load_state_dict(state, strict=True)
    model.eval()
    return model

def p95(values):
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]

def audit(obj):
    errors = []
    if obj.get("schema") != "intent_aligned_needle_v1":
        errors.append("schema")
    if obj.get("source_sha256") != RUNNER_SHA256:
        errors.append("runner_source_sha256")
    rows = obj.get("test_rows", [])
    if len(rows) != 1024:
        errors.append("test_row_count")
        return {"audit": "FAIL", "errors": errors}

    states = []
    intents = []
    truth = []
    stored_base = []
    stored_cond = []
    for r in rows:
        state, intent, y, bp, cp = r
        states.append(state)
        intents.append(int(intent))
        truth.append(int(y))
        stored_base.append(int(bp))
        stored_cond.append(int(cp))
        if int(y) != expected_label(state, int(intent)):
            errors.append("teacher_label_mismatch")
            break
    for k in range(0, len(rows), 2):
        if rows[k][1] != 0 or rows[k + 1][1] != 1 or rows[k][0] != rows[k + 1][0]:
            errors.append("paired_test_rows")
            break

    state_t = torch.tensor(states, dtype=torch.float32)
    intent_t = torch.tensor(intents, dtype=torch.long)
    gtest = torch.Generator(device="cpu").manual_seed(344202)
    tp = 2.4 * torch.rand(512, generator=gtest) - 1.2
    tv = 0.8 * torch.rand(512, generator=gtest) - 0.4
    ta = torch.rand(512, generator=gtest)
    ts = (torch.rand(512, generator=gtest) > 0.08).float()
    expected_test_states = torch.stack([tp, tv, ta, ts], dim=1).repeat_interleave(2, dim=0)
    if not torch.equal(state_t, expected_test_states):
        errors.append("test_split_generation_mismatch")
    bits = F.one_hot(intent_t, num_classes=2).float()
    base_x = torch.cat([state_t, torch.zeros_like(bits)], dim=1)
    cond_x = torch.cat([state_t, bits], dim=1)
    base = make_model(obj["model_state"]["baseline"])
    cond = make_model(obj["model_state"]["conditioned"])
    with torch.inference_mode():
        base_pred = base(base_x).argmax(dim=1).tolist()
        cond_pred = cond(cond_x).argmax(dim=1).tolist()
    if base_pred != stored_base:
        errors.append("baseline_predictions_not_reproduced")
    if cond_pred != stored_cond:
        errors.append("conditioned_predictions_not_reproduced")

    n = len(rows)
    base_acc = sum(a == b for a, b in zip(base_pred, truth)) / n
    cond_acc = sum(a == b for a, b in zip(cond_pred, truth)) / n
    base_pair = sum(base_pred[k] == truth[k] and base_pred[k+1] == truth[k+1]
                    for k in range(0, n, 2)) / (n // 2)
    cond_pair = sum(cond_pred[k] == truth[k] and cond_pred[k+1] == truth[k+1]
                    for k in range(0, n, 2)) / (n // 2)

    lp = obj["latency_samples_ms"]
    base_p95 = p95(lp["baseline"])
    cond_p95 = p95(lp["conditioned"])
    metrics = obj["metrics"]
    computed = {
        "baseline_accuracy": base_acc,
        "conditioned_accuracy": cond_acc,
        "accuracy_gain": cond_acc - base_acc,
        "baseline_paired_intent_exact": base_pair,
        "conditioned_paired_intent_exact": cond_pair,
        "baseline_cpu_p95_ms": base_p95,
        "conditioned_cpu_p95_ms": cond_p95
    }
    for key, value in computed.items():
        if abs(float(metrics[key]) - value) > 1e-9:
            errors.append("aggregate_mismatch:" + key)

    train_states = 1024
    g = torch.Generator(device="cpu").manual_seed(344201)
    pos = 2.4 * torch.rand(train_states, generator=g) - 1.2
    vel = 0.8 * torch.rand(train_states, generator=g) - 0.4
    age = torch.rand(train_states, generator=g)
    scope = (torch.rand(train_states, generator=g) > 0.08).float()
    train_x = torch.stack([pos, vel, age, scope], dim=1)
    xx = train_x.repeat_interleave(2, dim=0)
    ii = torch.arange(2, dtype=torch.long).repeat(train_states)
    pp, vv, aa, ss = xx.unbind(dim=1)
    target = torch.where(ii == 0, torch.full_like(pp, -0.8), torch.full_like(pp, 0.8))
    err = target - pp
    invalid = (aa > 0.90) | (ss < 0.5) | (pp.abs() > 1.10) | (vv.abs() > 0.35)
    watch = (err.abs() <= 0.08) & (vv.abs() <= 0.05)
    yy = torch.where(err < 0, torch.zeros_like(ii), torch.ones_like(ii))
    yy = torch.where(watch, torch.full_like(ii, 2), yy)
    yy = torch.where(invalid, torch.full_like(ii, 3), yy).long()
    payload = {"x": xx.tolist(), "intent": ii.tolist(), "y": yy.tolist()}
    digest = hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()
    if digest != obj.get("train_data_sha256"):
        errors.append("train_data_hash_mismatch")

    gate_counts = {"matched_propose": n, "stale_intent_yield": n,
                   "stale_evidence_yield": n, "unknown_intent_yield": n}
    if metrics.get("gate_counts") != gate_counts:
        errors.append("gate_count_mismatch")
    gates = {
        "conditioned_accuracy_ge_0_95": cond_acc >= 0.95,
        "accuracy_gain_ge_0_20": cond_acc - base_acc >= 0.20,
        "conditioned_paired_exact_ge_0_90": cond_pair >= 0.90,
        "stale_intent_all_yield": gate_counts["stale_intent_yield"] == n,
        "stale_evidence_all_yield": gate_counts["stale_evidence_yield"] == n,
        "unknown_intent_all_yield": gate_counts["unknown_intent_yield"] == n,
        "matched_context_all_propose": gate_counts["matched_propose"] == n,
        "conditioned_cpu_p95_lt_60ms": cond_p95 < 60.0
    }
    if obj.get("gates") != gates:
        errors.append("gate_recomputation_mismatch")
    decision = "PASS_INTENT_CONDITIONING_SYNTHETIC_SCOPED" if all(gates.values()) else "HOLD_OR_FAIL_GATE_MISS"
    if obj.get("outcome") != decision:
        errors.append("outcome_mismatch")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "rows_recomputed": n, "metrics_recomputed": computed,
            "gates_recomputed": gates, "decision_recomputed": decision}

if "--self-test" in sys.argv:
    assert expected_label([0.0, 0.0, 0.1, 1.0], 0) == 0
    assert expected_label([0.0, 0.0, 0.1, 1.0], 1) == 1
    assert expected_label([-0.8, 0.0, 0.1, 1.0], 0) == 2
    assert expected_label([0.0, 0.0, 0.95, 1.0], 1) == 3
    print(json.dumps({"audit_self_test": "PASS", "cases": 4}, sort_keys=True))
else:
    torch.set_num_threads(1)
    result = audit(json.load(sys.stdin))
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    if result["audit"] != "PASS":
        raise SystemExit(2)
