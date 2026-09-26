"""Independent raw-output auditor; does not import runner.py or formal.py."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path

import torch

ALLOCATION = "needle-lora-rank1-online-skill-v1"
SEEDS = (73111, 73222, 73333)
D, H, C = 8, 16, 4
N_SUPPORT, N_HELDOUT = 16, 4096
UPDATES_PER_ARRIVAL, BATCH = 8, 32
SEED_OFFSETS = (1, 2, 3, 4, 10, 20, 21, 30)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def digest_json(obj):
    return digest(canonical(obj))


def ids_from_b64(value):
    return list(base64.b64decode(value, validate=True))


def generate(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))


def expected_labels(x, invert_first=False):
    first = (x[:, 0] > 0).long()
    second = (x[:, 1] > 0).long()
    if invert_first:
        first = 1 - first
    return first * 2 + second


def prediction_from_state(base_state, adapter, rank, x):
    hidden = torch.tanh(x @ torch.tensor(base_state["enc.0.weight"], dtype=torch.float32).T
                        + torch.tensor(base_state["enc.0.bias"], dtype=torch.float32))
    logits = hidden @ torch.tensor(base_state["head.weight"], dtype=torch.float32).T
    logits = logits + torch.tensor(base_state["head.bias"], dtype=torch.float32)
    if adapter is not None:
        a = torch.tensor(adapter["a"], dtype=torch.float32)
        b = torch.tensor(adapter["b"], dtype=torch.float32)
        logits = logits + (hidden @ a @ b) / rank
    return logits.argmax(-1).tolist()


def make_order_and_schedule(seed):
    order = torch.randperm(N_SUPPORT, generator=torch.Generator(device="cpu").manual_seed(seed + 20)).tolist()
    rng = torch.Generator(device="cpu").manual_seed(seed + 21)
    seen, schedule = [], []
    for row in order:
        seen.append(row)
        batches = []
        for _ in range(UPDATES_PER_ARRIVAL):
            indices = torch.randint(len(seen), (BATCH,), generator=rng).tolist()
            batches.append([seen[index] for index in indices])
        schedule.append({"row": row, "seen": list(seen), "batches": batches})
    return order, schedule


def nearest_rank(values, quantile):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)] if ordered else None


def source_audit(source):
    freeze_bytes = (source / "FREEZE.json").read_bytes()
    freeze_sha = digest(freeze_bytes)
    errors = []
    if (source / "FREEZE.sha256").read_text(encoding="ascii").strip() != freeze_sha:
        errors.append("freeze_sidecar_hash")
    freeze = json.loads(freeze_bytes)
    for rel, expected in freeze["source_sha256"].items():
        if digest((source / rel).read_bytes()) != expected:
            errors.append("source_hash:" + rel)
    return freeze, freeze_sha, errors


def audit_seed(path, expected_seed):
    row = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if row.get("schema") != "needle-rank1-online-seed.v1" or row.get("allocation") != ALLOCATION:
        errors.append("seed_identity")
    if row.get("seed") != expected_seed:
        errors.append("seed_value")
    derived = [{seed + offset for offset in SEED_OFFSETS} for seed in SEEDS]
    for index, left in enumerate(derived):
        for right in derived[index + 1:]:
            if not left.isdisjoint(right):
                errors.append("seed_offset_collision")

    base = row.get("base_state")
    if not isinstance(base, dict) or digest_json(base) != row.get("base_sha256"):
        errors.append("base_state_digest")
    if row.get("base_sha256_after") != row.get("base_sha256"):
        errors.append("immutable_base_digest")

    xa = generate(N_HELDOUT, expected_seed + 3)
    ya = expected_labels(xa)
    xb = generate(N_HELDOUT, expected_seed + 4)
    yb = expected_labels(xb, invert_first=True)
    expected = row.get("expected_b64", {})
    if ids_from_b64(expected.get("role_a", "")) != ya.tolist():
        errors.append("role_a_expected_rows")
    if ids_from_b64(expected.get("role_b", "")) != yb.tolist():
        errors.append("role_b_expected_rows")

    predicted_a = ids_from_b64(row.get("role_a_predictions_b64", ""))
    recomputed_a = prediction_from_state(base, None, 1, xa) if isinstance(base, dict) else []
    if predicted_a != recomputed_a:
        errors.append("role_a_prediction_recompute")
    accuracy_a = sum(int(p == y) for p, y in zip(recomputed_a, ya.tolist())) / N_HELDOUT if recomputed_a else -1
    if row.get("role_a_accuracy") != accuracy_a:
        errors.append("role_a_accuracy")

    order, schedule = make_order_and_schedule(expected_seed)
    if row.get("role_b_order") != order:
        errors.append("support_order")
    schedule_hash = digest_json({"order": order, "schedule": schedule})
    if row.get("schedule_sha256") != schedule_hash:
        errors.append("schedule_hash")

    curves = {}
    if set(row.get("arms", {})) != {"1", "2"}:
        errors.append("arm_set")
    for rank_text in ("1", "2"):
        arm = row.get("arms", {}).get(rank_text, {})
        rank = int(rank_text)
        latencies = arm.get("update_ms", [])
        snapshots = arm.get("snapshots", [])
        if len(latencies) != N_SUPPORT or len(snapshots) != N_SUPPORT or len(schedule) != N_SUPPORT:
            errors.append(f"arrival_denominator:{rank_text}")
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0 for value in latencies):
            errors.append(f"update_latency_schema:{rank_text}")
        if arm.get("base_copy_sha256_before") != row.get("base_sha256") or arm.get("base_copy_sha256_after") != row.get("base_sha256"):
            errors.append(f"arm_base_copy:{rank_text}")
        accuracy_curve = []
        for index, snapshot in enumerate(snapshots):
            adapter = snapshot.get("adapter", {})
            if (snapshot.get("arrival") != index + 1 or snapshot.get("seen_rows") != order[:index + 1]
                    or len(adapter.get("a", [])) != H or any(len(x) != rank for x in adapter.get("a", []))
                    or len(adapter.get("b", [])) != rank or any(len(x) != C for x in adapter.get("b", []))):
                errors.append(f"snapshot_binding:{rank_text}:{index + 1}")
            recomputed = prediction_from_state(base, adapter, rank, xb) if isinstance(base, dict) else []
            retained = ids_from_b64(snapshot.get("predictions_b64", ""))
            if retained != recomputed:
                errors.append(f"prediction_rows:{rank_text}:{index + 1}")
            score = sum(int(p == y) for p, y in zip(recomputed, yb.tolist())) / N_HELDOUT if recomputed else -1
            if snapshot.get("accuracy") != score:
                errors.append(f"accuracy_curve:{rank_text}:{index + 1}")
            accuracy_curve.append(score)
        curves[rank_text] = {"accuracy": accuracy_curve, "update_ms": latencies}

    controls = row.get("controls", {})
    expected_controls = {
        "valid_base_route": True,
        "valid_skill_route": True,
        "unknown_role_yields": True,
        "stale_skill_version_yields": True,
        "future_skill_version_yields": True,
        "missing_skill_yields": True,
    }
    if controls != expected_controls:
        errors.append("route_controls")
    if row.get("environment", {}).get("device") != "cpu" or row.get("environment", {}).get("threads") != 1:
        errors.append("environment_binding")
    return row, curves, accuracy_a, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source, output = Path(args.source), Path(args.out)
    freeze, freeze_sha, errors = source_audit(source)
    run = json.loads((output / "RUN.json").read_text(encoding="utf-8"))
    if (run.get("schema") != "needle-rank1-online-run.v1" or run.get("allocation") != ALLOCATION
            or run.get("formal_invocations") != 1 or run.get("retry_count") != 0
            or run.get("seeds") != list(SEEDS)):
        errors.append("run_contract")
    metrics_by_seed, all_times = {}, {"1": [], "2": []}
    for seed in SEEDS:
        path = output / f"seed-{seed}.json"
        observed_sha = digest(path.read_bytes())
        if run.get("result_sha256", {}).get(path.name) != observed_sha:
            errors.append("result_hash:" + path.name)
        row, curves, accuracy_a, seed_errors = audit_seed(path, seed)
        errors.extend(f"{seed}:{item}" for item in seed_errors)
        for rank in ("1", "2"):
            all_times[str(rank)].extend(curves[str(rank)]["update_ms"])
        metrics_by_seed[str(seed)] = {
            "role_a_accuracy": accuracy_a,
            "rank1_final_accuracy": curves["1"]["accuracy"][-1] if curves["1"]["accuracy"] else None,
            "rank2_final_accuracy": curves["2"]["accuracy"][-1] if curves["2"]["accuracy"] else None,
            "rank1_accuracy_curve": curves["1"]["accuracy"],
            "rank2_accuracy_curve": curves["2"]["accuracy"],
            "rank1_update_p95_ms": nearest_rank(curves["1"]["update_ms"], .95),
            "rank2_update_p95_ms": nearest_rank(curves["2"]["update_ms"], .95),
        }
    all_rank1_acc = [m["rank1_final_accuracy"] for m in metrics_by_seed.values()]
    all_rank2_acc = [m["rank2_final_accuracy"] for m in metrics_by_seed.values()]
    role_a_acc = [m["role_a_accuracy"] for m in metrics_by_seed.values()]
    rank1_p95, rank2_p95 = nearest_rank(all_times["1"], .95), nearest_rank(all_times["2"], .95)
    if errors:
        decision = "HOLD_AUDIT_INTEGRITY"
    elif min(all_rank1_acc) < .90 or min(role_a_acc) < .90 or any(a < b - .03 for a, b in zip(all_rank1_acc, all_rank2_acc)):
        decision = "FAIL_RANK1_SKILL_CAPACITY"
    elif rank1_p95 > 60 or rank2_p95 <= 0 or rank1_p95 > .80 * rank2_p95:
        decision = "HOLD_NO_REALTIME_BENEFIT"
    else:
        decision = "PASS_RANK1_ONLINE_SKILL_SCOPED"
    report = {
        "schema": "needle-rank1-online-audit.v1",
        "audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "decision": decision,
        "allocation": ALLOCATION,
        "issue": 4507,
        "errors": errors,
        "source_freeze_sha256": freeze_sha,
        "source_sha256": freeze.get("source_sha256", {}),
        "docker_image_id": freeze.get("docker_image_id"),
        "seeds": metrics_by_seed,
        "aggregate": {
            "rank1_update_n": len(all_times["1"]),
            "rank2_update_n": len(all_times["2"]),
            "rank1_update_p50_ms": nearest_rank(all_times["1"], .50),
            "rank1_update_p95_ms": rank1_p95,
            "rank2_update_p95_ms": rank2_p95,
            "rank1_to_rank2_p95_ratio": rank1_p95 / rank2_p95 if rank1_p95 is not None and rank2_p95 else None,
        },
        "thresholds": {"per_seed_rank1_accuracy_min": .90, "per_seed_role_a_accuracy_min": .90,
                        "max_accuracy_loss_vs_rank2": .03, "rank1_update_p95_ms_max": 60,
                        "rank1_to_rank2_p95_ratio_max": .80},
    }
    with (output / "AUDIT.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    print(json.dumps({"audit": report["audit"], "decision": decision,
                      "errors": len(errors), "rank1_p95_ms": rank1_p95,
                      "rank2_p95_ms": rank2_p95}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
