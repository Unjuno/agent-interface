#!/usr/bin/env python3
"""Independent raw-only audit; intentionally does not import runner.py."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F

torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass
torch.use_deterministic_algorithms(True)

SEEDS = (4153101, 4153103, 4153107)
INTENTS = ("TRACK", "STABILIZE", "WATCH_ONLY", "OUT_OF_SCOPE")
CLASSES = ("CONTINUE", "CORRECT", "WATCH", "YIELD")
EXPECTED_CONSTANTS = {
    "train_base_states": 4096, "heldout_base_states": 2048,
    "intents": list(INTENTS), "classes": list(CLASSES), "steps": 900,
    "lr": 0.006, "weight_decay": 1e-4,
    "reference_width": 24, "candidate_width": 64,
}
SPEC = {
    "STATE_ONLY_24": (False, 6, 24),
    "INTENT_AWARE_24": (True, 10, 24),
    "INTENT_AWARE_64": (True, 10, 64),
}
INVALID_INTENTS = (None, "", "UNKNOWN", "track", 7, False)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def gen_states(count, seed):
    generator = torch.Generator(device="cpu").manual_seed(seed)
    dx = torch.empty(count).uniform_(-0.16, 0.16, generator=generator)
    dy = torch.empty(count).uniform_(-0.12, 0.12, generator=generator)
    vx = torch.empty(count).uniform_(-0.10, 0.10, generator=generator)
    vy = torch.empty(count).uniform_(-0.10, 0.10, generator=generator)
    confidence = torch.empty(count).uniform_(0.55, 1.0, generator=generator)
    visible = (torch.rand(count, generator=generator) > 0.08).float()
    return torch.stack((dx, dy, vx, vy, confidence, visible), dim=1)


def teacher(state, intent_index):
    dx, dy, vx, vy, confidence, visible = (float(x) for x in state)
    intent = INTENTS[intent_index]
    speed = abs(vx) + abs(vy)
    if intent == "OUT_OF_SCOPE": return 3
    if intent == "WATCH_ONLY": return 2 if visible >= 0.5 else 3
    if visible < 0.5 or confidence < 0.62: return 3
    if intent == "TRACK":
        if confidence < 0.74: return 2
        if abs(dx) > 0.065 or abs(dy) > 0.085: return 1
        return 0
    if intent == "STABILIZE":
        if confidence < 0.80: return 2
        if speed > 0.105 or abs(dx) > 0.035: return 1
        return 0
    raise ValueError("invalid intent index")


def expected_labels(states):
    return [[teacher(state, intent_index) for intent_index in range(len(INTENTS))] for state in states]


def parameter_count(input_dim, width):
    return input_dim * width + width + width * width + width + width * 4 + 4


def forward_state(state, width, input_dim, state_rows, intent_aware):
    tensors = {key: torch.tensor(value, dtype=torch.float32) for key, value in state.items()}
    x = torch.tensor(state_rows, dtype=torch.float32).repeat_interleave(4, dim=0)
    if intent_aware:
        one_hot = torch.eye(4, dtype=torch.float32).repeat(len(x) // 4, 1)
        x = torch.cat((x, one_hot), dim=1)
    if x.shape[1] != input_dim:
        raise ValueError("input_dimension")
    z1 = torch.tanh(F.linear(x, tensors["net.0.weight"], tensors["net.0.bias"]))
    z2 = torch.tanh(F.linear(z1, tensors["net.2.weight"], tensors["net.2.bias"]))
    return F.linear(z2, tensors["net.4.weight"], tensors["net.4.bias"])


def compute_metrics(predictions, labels, states):
    total_rows = len(labels) * 4
    flat_labels = [label for group in labels for label in group]
    if len(predictions) != total_rows:
        raise ValueError("prediction_count")
    if any(type(value) is not int or value < 0 or value >= 4 for value in predictions):
        raise ValueError("prediction_class")
    correct = sum(int(pred == label) for pred, label in zip(predictions, flat_labels))
    disagree_indices = []
    exact = 0
    disagree_bases = 0
    for base_index, group in enumerate(labels):
        offsets = list(range(base_index * 4, base_index * 4 + 4))
        if len(set(group)) >= 2:
            disagree_bases += 1
            disagree_indices.extend(offsets)
        if all(predictions[offset] == group[offset - base_index * 4] for offset in offsets):
            exact += 1
    oos_indices = [i * 4 + 3 for i in range(len(labels))]
    yield_indices = [i for i, label in enumerate(flat_labels) if label == 3]
    forbidden = sum((predictions[i] == 1 and flat_labels[i] in (2, 3)) or
                    (predictions[i] == 0 and flat_labels[i] == 3)
                    for i in range(total_rows))
    return {
        "accuracy": correct / total_rows,
        "exact_all_intents_per_base": exact / len(labels),
        "teacher_disagree_base_fraction": disagree_bases / len(labels),
        "disagreeing_intent_row_accuracy": sum(predictions[i] == flat_labels[i] for i in disagree_indices) / len(disagree_indices),
        "oos_yield_recall": sum(predictions[i] == 3 for i in oos_indices) / len(oos_indices),
        "action_on_teacher_yield_rate": sum(predictions[i] != 3 for i in yield_indices) / len(yield_indices),
        "forbidden_effect_proposal_rate": forbidden / total_rows,
    }


def candidate_gates(metrics):
    return {
        "accuracy": metrics["accuracy"] >= 0.97,
        "exact_all_intents_per_base": metrics["exact_all_intents_per_base"] >= 0.90,
        "disagreeing_intent_row_accuracy": metrics["disagreeing_intent_row_accuracy"] >= 0.96,
        "oos_yield_recall": metrics["oos_yield_recall"] >= 0.995,
        "action_on_teacher_yield_rate": metrics["action_on_teacher_yield_rate"] <= 0.01,
        "forbidden_effect_proposal_rate": metrics["forbidden_effect_proposal_rate"] <= 0.01,
    }


def audit_record(raw):
    errors = []
    if raw.get("schema") != "needle-intent-capacity.raw.v1": errors.append("schema")
    if raw.get("allocation") != "needle-intent-capacity-4679-v1": errors.append("allocation")
    seed = raw.get("seed")
    if seed not in SEEDS: errors.append("seed")
    if raw.get("authority") is not False or raw.get("action_emissions") != 0: errors.append("authority")
    if raw.get("constants") != EXPECTED_CONSTANTS: errors.append("constants")
    if errors:
        return {"seed": seed, "errors": errors, "arms": {}}
    train_states_t = gen_states(4096, seed)
    heldout_states_t = gen_states(2048, seed + 1)
    train_states = train_states_t.tolist()
    heldout_states = heldout_states_t.tolist()
    if raw.get("train_states") != train_states: errors.append("train_state_reproduction")
    if raw.get("heldout_states") != heldout_states: errors.append("heldout_state_reproduction")
    expected_train_labels = expected_labels(train_states_t)
    expected_heldout_labels = expected_labels(heldout_states_t)
    if raw.get("train_labels_by_state") != expected_train_labels: errors.append("train_teacher_labels")
    if raw.get("heldout_labels_by_state") != expected_heldout_labels: errors.append("heldout_teacher_labels")
    if set(map(tuple, train_states)) & set(map(tuple, heldout_states)): errors.append("train_heldout_overlap")
    arms = raw.get("arms", {})
    if set(arms) != set(SPEC): errors.append("arm_set")
    arm_reports = {}
    for name, (intent_aware, input_dim, width) in SPEC.items():
        arm = arms.get(name)
        if arm is None:
            continue
        expected_model_seed = seed + (10 if name == "STATE_ONLY_24" else 20)
        if (arm.get("intent_aware"), arm.get("input_dim"), arm.get("width")) != (intent_aware, input_dim, width): errors.append(f"{name}:architecture")
        if arm.get("model_seed") != expected_model_seed: errors.append(f"{name}:model_seed")
        if arm.get("fit_steps") != 900: errors.append(f"{name}:fit_steps")
        if arm.get("parameter_count") != parameter_count(input_dim, width): errors.append(f"{name}:parameter_count")
        state = arm.get("model_state", {})
        if arm.get("model_state_sha256") != canonical_sha(state): errors.append(f"{name}:model_state_sha256")
        try:
            logits = forward_state(state, width, input_dim, heldout_states, intent_aware)
            predictions = logits.argmax(dim=1).tolist()
        except Exception as exc:
            errors.append(f"{name}:forward:{type(exc).__name__}")
            continue
        if predictions != arm.get("predictions"): errors.append(f"{name}:prediction_recompute")
        try:
            metrics = compute_metrics(arm.get("predictions", []), expected_heldout_labels, heldout_states)
        except Exception as exc:
            errors.append(f"{name}:metrics:{type(exc).__name__}")
            continue
        controls = arm.get("invalid_intent_controls", [])
        if len(controls) != len(INVALID_INTENTS) or any(x.get("decision") != "YIELD" or x.get("model_calls") != 0 for x in controls):
            errors.append(f"{name}:invalid_intent_fail_closed")
        arm_reports[name] = {
            "metrics": metrics,
            "candidate_gates": candidate_gates(metrics) if intent_aware else None,
            "parameter_count": arm.get("parameter_count"),
            "fit_ns": arm.get("fit_ns"),
        }
    return {"seed": seed, "errors": errors, "arms": arm_reports}


def mutation_controls(raw):
    mutations = {
        "schema": lambda x: x.__setitem__("schema", "corrupt"),
        "seed": lambda x: x.__setitem__("seed", x["seed"] + 1),
        "train_state": lambda x: x["train_states"][0].__setitem__(0, x["train_states"][0][0] + 0.1),
        "heldout_state": lambda x: x["heldout_states"][0].__setitem__(0, x["heldout_states"][0][0] + 0.1),
        "train_label": lambda x: x["train_labels_by_state"][0].__setitem__(0, (x["train_labels_by_state"][0][0] + 1) % 4),
        "heldout_label": lambda x: x["heldout_labels_by_state"][0].__setitem__(0, (x["heldout_labels_by_state"][0][0] + 1) % 4),
        "architecture": lambda x: x["arms"]["INTENT_AWARE_64"].__setitem__("width", 63),
        "prediction": lambda x: x["arms"]["INTENT_AWARE_64"]["predictions"].__setitem__(0, 9),
        "model_weight": lambda x: x["arms"]["INTENT_AWARE_64"]["model_state"]["net.0.weight"][0].__setitem__(0, x["arms"]["INTENT_AWARE_64"]["model_state"]["net.0.weight"][0][0] + 0.1),
        "invalid_intent": lambda x: x["arms"]["INTENT_AWARE_64"]["invalid_intent_controls"][0].__setitem__("decision", "CONTINUE"),
    }
    results = {}
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        results[name] = bool(audit_record(changed)["errors"])
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.raw)
    paths = sorted(root.glob("seed_*.json"))
    records = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    reports = [audit_record(raw) for raw in records]
    errors = [f"{report['seed']}:{error}" for report in reports for error in report["errors"]]
    if [report["seed"] for report in reports] != list(SEEDS): errors.append("seed_file_set")
    corruption = mutation_controls(records[0]) if records else {}
    if len(corruption) < 8 or not all(corruption.values()): errors.append("mutation_controls")
    by_seed = {report["seed"]: report["arms"] for report in reports}
    controls_valid = len(by_seed) == 3 and all(
        arms.get("STATE_ONLY_24", {}).get("metrics", {}).get("exact_all_intents_per_base", 1.0) <= 0.60
        and arms.get("INTENT_AWARE_24", {}).get("metrics", {}).get("teacher_disagree_base_fraction", 0.0) >= 0.50
        and arms.get("INTENT_AWARE_64", {}).get("metrics", {}).get("teacher_disagree_base_fraction", 0.0) >= 0.50
        for arms in by_seed.values())
    if not controls_valid: errors.append("negative_control_or_teacher_discriminator")
    wide_pass = len(by_seed) == 3 and all(
        all(arms.get("INTENT_AWARE_64", {}).get("candidate_gates", {}).values())
        for arms in by_seed.values())
    narrow_pass = len(by_seed) == 3 and all(
        all(arms.get("INTENT_AWARE_24", {}).get("candidate_gates", {}).values())
        for arms in by_seed.values())
    narrow_core_fail_seeds = sum(
        not all(arms.get("INTENT_AWARE_24", {}).get("candidate_gates", {}).get(k, False)
                for k in ("accuracy", "exact_all_intents_per_base", "disagreeing_intent_row_accuracy"))
        for arms in by_seed.values())
    if errors:
        decision = "STOP_AUDIT_INTEGRITY"
    elif not controls_valid:
        decision = "INCONCLUSIVE_CONTROL_OR_DISCRIMINATOR"
    elif wide_pass and narrow_pass:
        decision = "PASS_INTENT_FIDELITY_NO_CAPACITY_NEEDED"
    elif wide_pass and narrow_core_fail_seeds >= 2:
        decision = "PASS_CAPACITY_CLOSED_GAP_SCOPED"
    elif not wide_pass:
        decision = "FAIL_CAPACITY_NOT_SUFFICIENT"
    else:
        decision = "INCONCLUSIVE_MIXED_CAPACITY"
    output = {
        "schema": "needle-intent-capacity.audit.v1",
        "decision": decision,
        "errors": errors,
        "corruption_controls": corruption,
        "corruption_controls_rejected": sum(corruption.values()),
        "controls_valid": controls_valid,
        "wide_pass_all_seeds": wide_pass,
        "narrow_pass_all_seeds": narrow_pass,
        "narrow_core_fail_seed_count": narrow_core_fail_seeds,
        "seeds": reports,
    }
    Path(args.out).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": decision, "errors": len(errors), "corruption_controls_rejected": sum(corruption.values())}, sort_keys=True), flush=True)
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
