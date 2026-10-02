"""Independent pure-Python audit for the role-context online LoRA allocation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

SPLITS = {"a_support": ("A", 64), "a_heldout": ("A", 128),
          "b_arrival": ("B", 8), "b_heldout": ("B", 128)}
ARMS = ("unconditioned", "role_gated")
SCOPE_INPUTS = {
    "fresh_known": {"scope": "known", "fresh": True, "intent_match": True},
    "stale_known": {"scope": "known", "fresh": False, "intent_match": True},
    "unknown_scope": {"scope": "unknown", "fresh": True, "intent_match": True},
    "intent_mismatch": {"scope": "known", "fresh": True, "intent_match": False},
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest_object(value: object) -> str:
    return sha_bytes(canonical(value))


def target(role: str, features: list[int]) -> int:
    if role == "A":
        return 0
    if role == "B":
        return features[0]
    raise ValueError(role)


def check_dataset(deck: dict, expected_seeds: tuple[int, ...]) -> list[str]:
    errors = []
    if deck.get("schema") != "unjuno.needle.role-context-online.v1":
        errors.append("dataset_schema")
    if deck.get("feature_count") != 8:
        errors.append("feature_count")
    seeds = deck.get("seeds", [])
    if [row.get("seed") for row in seeds] != list(expected_seeds):
        errors.append("seed_set_or_order")
    for seed in seeds:
        splits = seed.get("splits", {})
        vectors_by_split: dict[str, set[tuple[int, ...]]] = {}
        ids = set()
        for key, (role, count) in SPLITS.items():
            rows = splits.get(key, [])
            if len(rows) != count:
                errors.append(f"{seed.get('seed')}:{key}:count")
            vectors = set()
            for index, row in enumerate(rows):
                features = row.get("features", [])
                if row.get("seed") != seed.get("seed") or row.get("role") != role or row.get("split") != key:
                    errors.append(f"{seed.get('seed')}:{key}:{index}:lineage")
                if len(features) != 8 or any(value not in (0, 1) for value in features):
                    errors.append(f"{seed.get('seed')}:{key}:{index}:features")
                    continue
                vector = tuple(features)
                if vector in vectors:
                    errors.append(f"{seed.get('seed')}:{key}:{index}:duplicate_features")
                vectors.add(vector)
                if row.get("label") != target(role, features):
                    errors.append(f"{seed.get('seed')}:{key}:{index}:target")
                if not row.get("id") or row["id"] in ids:
                    errors.append(f"{seed.get('seed')}:{key}:{index}:duplicate_id")
                ids.add(row.get("id"))
            if rows and sum(row["features"][0] for row in rows if len(row.get("features", [])) == 8) != count // 2:
                errors.append(f"{seed.get('seed')}:{key}:feature0_balance")
            vectors_by_split[key] = vectors
        for left, right in (("a_support", "a_heldout"), ("b_arrival", "b_heldout")):
            if vectors_by_split.get(left, set()) & vectors_by_split.get(right, set()):
                errors.append(f"{seed.get('seed')}:{left}_{right}:overlap")
        a_train = vectors_by_split.get("a_support", set())
        b_train = vectors_by_split.get("b_arrival", set())
        a_test = vectors_by_split.get("a_heldout", set())
        b_test = vectors_by_split.get("b_heldout", set())
        a_all = a_train | a_test
        b_all = b_train | b_test
        expected_overlap = len(a_all & b_all)
        if expected_overlap != seed.get("cross_role_overlap_count"):
            errors.append(f"{seed.get('seed')}:cross_role_overlap_count")
        probe = seed.get("role_conflict_probe", {})
        features = probe.get("features", [])
        if len(features) != 8 or any(value not in (0, 1) for value in features):
            errors.append(f"{seed.get('seed')}:role_conflict_probe_features")
        elif probe.get("a_label") != target("A", features) or probe.get("b_label") != target("B", features):
            errors.append(f"{seed.get('seed')}:role_conflict_probe_labels")
        if expected_overlap <= 0:
            errors.append(f"{seed.get('seed')}:no_cross_role_ambiguity_controls")
    return errors


def hidden(state: dict, role: int, features: list[int]) -> list[float]:
    x = [role, *features]
    w1, b1 = state["fc1.weight"], state["fc1.bias"]
    return [max(0.0, b1[j] + sum(w1[j][k] * x[k] for k in range(9))) for j in range(16)]


def predict(state: dict, adapter_a: list, adapter_b: list, role: int,
            features: list[int], gated: bool) -> int:
    actual_role = role if gated else 0
    h = hidden(state, actual_role, features)
    w2, b2 = state["fc2.weight"], state["fc2.bias"]
    logits = [b2[o] + sum(w2[o][j] * h[j] for j in range(16)) for o in range(4)]
    if not gated or role == 1:
        for o in range(4):
            for rank in range(2):
                projection = sum(adapter_a[rank][j] * h[j] for j in range(16))
                logits[o] += adapter_b[o][rank] * projection
    return max(range(4), key=lambda index: logits[index])


def adapter_gate(role: int) -> int:
    if role not in (0, 1):
        raise ValueError("unknown_role")
    return int(role == 1)


def scope_decision(scope: str, fresh: bool, intent_match: bool = True) -> str:
    return "PROPOSE" if scope == "known" and fresh and intent_match else "YIELD"


def reconcile(deck: dict, raw: dict, expected_seeds: tuple[int, ...],
              expected_dataset_sha: str | None = None) -> dict:
    errors = check_dataset(deck, expected_seeds)
    if raw.get("schema") != "unjuno.needle.role-context-candidate.v1":
        errors.append("candidate_schema")
    if expected_dataset_sha and raw.get("dataset_sha256") != expected_dataset_sha:
        errors.append("dataset_digest")
    runs = raw.get("seeds", [])
    if [run.get("seed") for run in runs] != list(expected_seeds):
        errors.append("candidate_seed_set_or_order")
    data_by_seed = {row.get("seed"): row for row in deck.get("seeds", [])}
    quality = True
    for run in runs:
        seed = run.get("seed")
        data = data_by_seed.get(seed)
        if data is None:
            errors.append(f"{seed}:missing_data")
            continue
        base = run.get("base_initial", {})
        base_sha = digest_object(base)
        for arm in ARMS:
            arm_data = run.get("arms", {}).get(arm, {})
            checkpoints = arm_data.get("checkpoints", [])
            if len(checkpoints) != 9 or [cp.get("update_index") for cp in checkpoints] != list(range(9)):
                errors.append(f"{seed}:{arm}:checkpoint_schedule")
            for cp in checkpoints:
                step = cp.get("update_index")
                if cp.get("base_sha256") != base_sha:
                    errors.append(f"{seed}:{arm}:{step}:base_changed")
                for role, split, pred_key in (("A", "a_heldout", "predictions_a"),
                                              ("B", "b_heldout", "predictions_b")):
                    rows = data["splits"][split]
                    role_id = int(role == "B") if arm == "role_gated" else 0
                    expected = [predict(base, cp["adapter_a"], cp["adapter_b"], role_id,
                                        row["features"], arm == "role_gated") for row in rows]
                    preds = cp.get(pred_key, [])
                    if preds != expected:
                        errors.append(f"{seed}:{arm}:{step}:{role}:prediction_replay")
                    if len(preds) != len(rows):
                        errors.append(f"{seed}:{arm}:{step}:{role}:prediction_count")
                        quality = False
                        continue
                    correct = sum(int(p == row["label"]) for p, row in zip(preds, rows, strict=True))
                    if cp.get(f"accuracy_{role.lower()}") != {"correct": correct, "total": len(rows)}:
                        errors.append(f"{seed}:{arm}:{step}:{role}:metric")
                    if arm == "role_gated" and role == "A" and correct / len(rows) < 0.90:
                        quality = False
                    if arm == "role_gated" and role == "B" and step == 8 and correct / len(rows) < 0.90:
                        quality = False
        scope_cases = run.get("scope_cases", {})
        if scope_cases.get("dispatch_count") != 0:
            errors.append(f"{seed}:scope_dispatch_count")
        for name, inputs in SCOPE_INPUTS.items():
            case = scope_cases.get(name, {})
            if {key: case.get(key) for key in inputs} != inputs:
                errors.append(f"{seed}:scope_inputs:{name}")
            if case.get("decision") != scope_decision(**inputs):
                errors.append(f"{seed}:scope_gate:{name}")
    if errors:
        disposition = "STOP_AUDIT_INTEGRITY"
    elif not quality:
        disposition = "HOLD_ROLE_ADAPTATION_QUALITY"
    else:
        disposition = "PASS_ROLE_CONDITIONED_ONLINE_ADAPTATION_SCOPED"
    return {"errors": errors, "quality_gates_pass": quality and not errors,
            "disposition": disposition}


def mutation_controls(deck: dict, raw: dict, seeds: tuple[int, ...]) -> dict:
    cases = {}
    mutated_deck = copy.deepcopy(deck)
    mutated_deck["seeds"][0]["splits"]["a_heldout"][0]["label"] = 1
    cases["wrong_a_target"] = bool(check_dataset(mutated_deck, seeds))
    mutated_deck = copy.deepcopy(deck)
    mutated_deck["seeds"][0]["splits"]["b_heldout"][0]["label"] ^= 1
    cases["wrong_b_target"] = bool(check_dataset(mutated_deck, seeds))
    mutated = copy.deepcopy(raw)
    mutated["seeds"][0]["arms"]["role_gated"]["checkpoints"].pop()
    cases["missing_update"] = bool(reconcile(deck, mutated, seeds)["errors"])
    mutated = copy.deepcopy(raw)
    mutated["seeds"][0]["arms"]["role_gated"]["checkpoints"][1]["predictions_a"][0] ^= 1
    cases["prediction_corruption"] = bool(reconcile(deck, mutated, seeds)["errors"])
    mutated = copy.deepcopy(raw)
    mutated["seeds"][0]["scope_cases"]["stale_known"]["decision"] = "PROPOSE"
    cases["stale_scope_admitted"] = bool(reconcile(deck, mutated, seeds)["errors"])
    mutated = copy.deepcopy(raw)
    mutated["seeds"][0]["arms"]["role_gated"]["checkpoints"][1]["base_sha256"] = "0" * 64
    cases["base_changed"] = bool(reconcile(deck, mutated, seeds)["errors"])
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    expected = freeze["sha256"]
    if digest(args.candidate) != args.candidate_sha256:
        raise SystemExit("STOP_CANDIDATE_OUTPUT_SHA256_MISMATCH")
    if digest(args.dataset) != freeze["dataset_sha256"]:
        raise SystemExit("STOP_DATASET_SHA256_MISMATCH")
    for name, sha in expected.items():
        if digest(args.freeze.parent / name) != sha:
            raise SystemExit(f"STOP_FROZEN_SHA256_MISMATCH:{name}")
    deck = json.loads(args.dataset.read_text(encoding="utf-8"))
    raw = json.loads(args.candidate.read_text(encoding="utf-8"))
    seeds = tuple(freeze["seeds"])
    result = reconcile(deck, raw, seeds, freeze["dataset_sha256"])
    controls = mutation_controls(deck, raw, seeds)
    result["mutation_controls"] = controls
    if not all(controls.values()):
        result["errors"].append("mutation_control_not_rejected")
        result["disposition"] = "STOP_AUDIT_INTEGRITY"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write((json.dumps(result, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
