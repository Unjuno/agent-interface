import hashlib
import json
import math
import platform
import sys
import time

import torch
from torch import nn
from torch.nn import functional as F

SOURCE_SHA256 = globals().get("__RUNNER_SOURCE_SHA256__", "")
SEED_TRAIN = 344201
SEED_TEST = 344202
SEED_BATCHES = 344204
SEED_INIT = 344205
TRAIN_STATES = 1024
TEST_STATES = 512
STEPS = 500
BATCH_SIZE = 128
VOCAB = {"LEFT": 0, "RIGHT": 1, "WATCH": 2, "YIELD": 3}
INTENT_IDS = {0: "target-left-v1", 1: "target-right-v1"}

def states(seed, n):
    g = torch.Generator(device="cpu").manual_seed(seed)
    pos = 2.4 * torch.rand(n, generator=g) - 1.2
    vel = 0.8 * torch.rand(n, generator=g) - 0.4
    age = torch.rand(n, generator=g)
    scope = (torch.rand(n, generator=g) > 0.08).float()
    return torch.stack([pos, vel, age, scope], dim=1)

def teacher(x, intent):
    pos, vel, age, scope = x.unbind(dim=1)
    target = torch.where(intent == 0, torch.full_like(pos, -0.8), torch.full_like(pos, 0.8))
    err = target - pos
    invalid = (age > 0.90) | (scope < 0.5) | (pos.abs() > 1.10) | (vel.abs() > 0.35)
    watch = (err.abs() <= 0.08) & (vel.abs() <= 0.05)
    action = torch.where(err < 0, torch.zeros_like(intent), torch.ones_like(intent))
    action = torch.where(watch, torch.full_like(intent, 2), action)
    return torch.where(invalid, torch.full_like(intent, 3), action).long()

class Needle(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
            nn.Linear(32, 4)
        )
    def forward(self, x):
        return self.net(x)

def inputs(x, intent, conditioned):
    if conditioned:
        bits = F.one_hot(intent, num_classes=2).float()
    else:
        bits = torch.zeros((len(intent), 2), dtype=torch.float32)
    return torch.cat([x, bits], dim=1)

def make_training_data():
    x = states(SEED_TRAIN, TRAIN_STATES)
    xx = x.repeat_interleave(2, dim=0)
    intent = torch.arange(2, dtype=torch.long).repeat(TRAIN_STATES)
    y = teacher(xx, intent)
    return xx, intent, y

def fit(x, y, schedule):
    torch.manual_seed(SEED_INIT)
    model = Needle().cpu()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.008, weight_decay=0.0001)
    model.train()
    started = time.perf_counter_ns()
    for ix in schedule:
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(x[ix]), y[ix])
        loss.backward()
        optimizer.step()
    elapsed_ms = (time.perf_counter_ns() - started) / 1e6
    model.eval()
    return model, elapsed_ms

def p95_ms(model, sample):
    single = sample[:1].clone()
    with torch.inference_mode():
        for _ in range(32):
            model(single)
        values = []
        for _ in range(256):
            t0 = time.perf_counter_ns()
            model(single)
            values.append((time.perf_counter_ns() - t0) / 1e6)
    return sorted(values)[math.ceil(0.95 * len(values)) - 1], values

def intent_gate(proposal_intent, proposal_intent_version, current_intent, current_intent_version,
                proposal_evidence_version, current_evidence_version):
    if proposal_intent not in INTENT_IDS.values() or current_intent not in INTENT_IDS.values():
        return "YIELD"
    if proposal_intent != current_intent:
        return "YIELD"
    if proposal_intent_version != current_intent_version:
        return "YIELD"
    if proposal_evidence_version != current_evidence_version:
        return "YIELD"
    return "PROPOSE"

def construction_only():
    torch.set_num_threads(1)
    x = torch.tensor([[0.0, 0.0, 0.10, 1.0],
                      [0.0, 0.0, 0.10, 1.0],
                      [-0.8, 0.0, 0.10, 1.0],
                      [0.0, 0.0, 0.95, 1.0]], dtype=torch.float32)
    i = torch.tensor([0, 1, 0, 1], dtype=torch.long)
    y = teacher(x, i)
    model = Needle()
    shape = tuple(model(inputs(x, i, True)).shape)
    paired = states(SEED_TRAIN, 8).repeat_interleave(2, dim=0)
    tests = {
        "label_vocab": y.tolist() == [0, 1, 2, 3],
        "output_shape": shape == (4, 4),
        "paired_state_order": torch.equal(paired[::2], paired[1::2]),
        "matched_context_proposes": intent_gate("target-left-v1", 1, "target-left-v1", 1, 7, 7) == "PROPOSE",
        "stale_intent_yields": intent_gate("target-left-v1", 1, "target-left-v1", 2, 7, 7) == "YIELD",
        "stale_evidence_yields": intent_gate("target-left-v1", 1, "target-left-v1", 1, 7, 8) == "YIELD",
        "unknown_intent_yields": intent_gate("role-unknown", 1, "target-left-v1", 1, 7, 7) == "YIELD"
    }
    print(json.dumps({"mode": "CONSTRUCTION_ONLY", "torch": torch.__version__,
                      "device": "cpu", "tests": tests, "passed": sum(tests.values()),
                      "total": len(tests)}, sort_keys=True))
    if not all(tests.values()):
        raise SystemExit(2)

def formal():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    train_x, train_intent, train_y = make_training_data()
    train_base = inputs(train_x, train_intent, False)
    train_cond = inputs(train_x, train_intent, True)
    batch_g = torch.Generator(device="cpu").manual_seed(SEED_BATCHES)
    schedule = [torch.randint(len(train_y), (BATCH_SIZE,), generator=batch_g) for _ in range(STEPS)]
    baseline, baseline_train_ms = fit(train_base, train_y, schedule)
    conditioned, conditioned_train_ms = fit(train_cond, train_y, schedule)

    test_x0 = states(SEED_TEST, TEST_STATES)
    test_x = test_x0.repeat_interleave(2, dim=0)
    test_intent = torch.arange(2, dtype=torch.long).repeat(TEST_STATES)
    test_y = teacher(test_x, test_intent)
    test_base = inputs(test_x, test_intent, False)
    test_cond = inputs(test_x, test_intent, True)
    with torch.inference_mode():
        base_logits = baseline(test_base)
        cond_logits = conditioned(test_cond)
        base_pred = base_logits.argmax(dim=1)
        cond_pred = cond_logits.argmax(dim=1)
    baseline_p95, baseline_latencies = p95_ms(baseline, test_base)
    conditioned_p95, conditioned_latencies = p95_ms(conditioned, test_cond)

    base_acc = float((base_pred == test_y).float().mean())
    cond_acc = float((cond_pred == test_y).float().mean())
    pair_ok = ((base_pred[::2] == test_y[::2]) & (base_pred[1::2] == test_y[1::2]))
    pair_cond_ok = ((cond_pred[::2] == test_y[::2]) & (cond_pred[1::2] == test_y[1::2]))
    matched = [intent_gate(INTENT_IDS[int(test_intent[j])], 1, INTENT_IDS[int(test_intent[j])], 1, 7, 7)
               for j in range(len(test_y))]
    stale_intent = [intent_gate(INTENT_IDS[int(test_intent[j])], 1, INTENT_IDS[int(test_intent[j])], 2, 7, 7)
                    for j in range(len(test_y))]
    stale_evidence = [intent_gate(INTENT_IDS[int(test_intent[j])], 1, INTENT_IDS[int(test_intent[j])], 1, 7, 8)
                      for j in range(len(test_y))]
    unknown = [intent_gate("unknown-role", 1, INTENT_IDS[int(test_intent[j])], 1, 7, 7)
               for j in range(len(test_y))]

    rows = []
    states_list = test_x.tolist()
    for j in range(len(test_y)):
        rows.append([states_list[j], int(test_intent[j]), int(test_y[j]),
                     int(base_pred[j]), int(cond_pred[j])])
    train_payload = {"x": train_x.tolist(), "intent": train_intent.tolist(), "y": train_y.tolist()}
    def weights(model):
        return {k: v.detach().cpu().tolist() for k, v in model.state_dict().items()}
    def pcount(model):
        return sum(p.numel() for p in model.parameters())
    def p95(samples):
        return sorted(samples)[math.ceil(0.95 * len(samples)) - 1]

    result = {
        "schema": "intent_aligned_needle_v1",
        "allocation": "intent-aligned-system1-3442-pilot-01",
        "issue": 3442,
        "source_sha256": SOURCE_SHA256,
        "environment": {"python": platform.python_version(), "torch": str(torch.__version__),
                        "device": "CPU", "cpu_threads": torch.get_num_threads(),
                        "execution": "Windows host memory-only; no local artifacts"},
        "parameters": {"seed_train": SEED_TRAIN, "seed_test": SEED_TEST,
                       "seed_batches": SEED_BATCHES, "seed_initialization": SEED_INIT,
                       "train_states_per_intent": TRAIN_STATES, "test_states_per_intent": TEST_STATES,
                       "steps": STEPS, "batch_size": BATCH_SIZE, "architecture": "6-32-32-4 tanh MLP",
                       "optimizer": "AdamW", "learning_rate": 0.008, "weight_decay": 0.0001},
        "vocabulary": VOCAB,
        "metrics": {"baseline_accuracy": base_acc, "conditioned_accuracy": cond_acc,
                    "accuracy_gain": cond_acc - base_acc,
                    "baseline_paired_intent_exact": float(pair_ok.float().mean()),
                    "conditioned_paired_intent_exact": float(pair_cond_ok.float().mean()),
                    "baseline_train_ms": baseline_train_ms, "conditioned_train_ms": conditioned_train_ms,
                    "baseline_cpu_p95_ms": baseline_p95, "conditioned_cpu_p95_ms": conditioned_p95,
                    "baseline_cpu_p95_recomputed_ms": p95(baseline_latencies),
                    "conditioned_cpu_p95_recomputed_ms": p95(conditioned_latencies),
                    "parameter_count_each": pcount(baseline),
                    "gate_counts": {"matched_propose": matched.count("PROPOSE"),
                                    "stale_intent_yield": stale_intent.count("YIELD"),
                                    "stale_evidence_yield": stale_evidence.count("YIELD"),
                                    "unknown_intent_yield": unknown.count("YIELD")}},
        "latency_samples_ms": {"baseline": baseline_latencies, "conditioned": conditioned_latencies},
        "train_data_sha256": hashlib.sha256(json.dumps(train_payload, separators=(",", ":")).encode()).hexdigest(),
        "model_state": {"baseline": weights(baseline), "conditioned": weights(conditioned)},
        "test_rows": rows,
        "limitations": ["synthetic paired intents, not Astra trajectories or human labels",
                        "one seed; authority-neutral proposals only; no GUI/action execution",
                        "version equality is tested, not cryptographic intent signatures",
                        "host CPU run, not container verification"]
    }
    gates = {
        "conditioned_accuracy_ge_0_95": cond_acc >= 0.95,
        "accuracy_gain_ge_0_20": cond_acc - base_acc >= 0.20,
        "conditioned_paired_exact_ge_0_90": float(pair_cond_ok.float().mean()) >= 0.90,
        "stale_intent_all_yield": stale_intent.count("YIELD") == len(test_y),
        "stale_evidence_all_yield": stale_evidence.count("YIELD") == len(test_y),
        "unknown_intent_all_yield": unknown.count("YIELD") == len(test_y),
        "matched_context_all_propose": matched.count("PROPOSE") == len(test_y),
        "conditioned_cpu_p95_lt_60ms": conditioned_p95 < 60.0
    }
    result["gates"] = gates
    result["outcome"] = "PASS_INTENT_CONDITIONING_SYNTHETIC_SCOPED" if all(gates.values()) else "HOLD_OR_FAIL_GATE_MISS"
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))

if "--construction-only" in sys.argv:
    construction_only()
else:
    formal()
