"""Independent raw-evidence auditor; does not import runner.py."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F

ALLOCATION = "needle-online-snapshot-cadence-4621-v2"
SEEDS = (77111, 77222, 77333)
CADENCES = (1, 4, 16)
N_SUPPORT, N_HELDOUT, UPDATES_PER_ARRIVAL = 16, 4096, 8
SNAPSHOT_SCHEMA = "needle-online-skill-snapshot-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_json(value):
    return sha_bytes(canonical(value))


def decode_ids(encoded):
    return list(base64.b64decode(encoded, validate=True))


def nearest(values, q):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)] if ordered else None


def labels(rows, flip=False):
    result = []
    for row in rows:
        a = int(row[0] > 0)
        b = int(row[1] > 0)
        result.append((1 - a if flip else a) * 2 + b)
    return result


def predict(base, adapter, rows):
    enc_w = torch.tensor(base["enc.0.weight"], dtype=torch.float32)
    enc_b = torch.tensor(base["enc.0.bias"], dtype=torch.float32)
    head_w = torch.tensor(base["head.weight"], dtype=torch.float32)
    head_b = torch.tensor(base["head.bias"], dtype=torch.float32)
    a = torch.tensor(adapter["a"], dtype=torch.float32)
    b = torch.tensor(adapter["b"], dtype=torch.float32)
    x = torch.tensor(rows, dtype=torch.float32)
    with torch.no_grad():
        hidden = torch.tanh(F.linear(x, enc_w, enc_b))
        logits = F.linear(hidden, head_w, head_b) + (hidden @ a @ b) / 2
        return logits.argmax(-1).tolist()


def verify_snapshot(snapshot, seed, base_sha, schedule_sha, cursor):
    problems = []
    if snapshot.get("schema") != SNAPSHOT_SCHEMA or snapshot.get("allocation") != ALLOCATION:
        problems.append("identity")
    if snapshot.get("seed") != seed or snapshot.get("role") != "B":
        problems.append("seed_role")
    if snapshot.get("base_sha256") != base_sha or snapshot.get("schedule_sha256") != schedule_sha:
        problems.append("base_schedule")
    if snapshot.get("schedule_version") != "eight-adamw-updates-per-feedback-v1":
        problems.append("schedule_version")
    if snapshot.get("cursor") != cursor:
        problems.append("cursor")
    body = {k: v for k, v in snapshot.items() if k != "snapshot_sha256"}
    if snapshot.get("snapshot_sha256") != sha_json(body):
        problems.append("digest")
    if snapshot.get("optimizer", {}).get("step") != cursor * UPDATES_PER_ARRIVAL:
        problems.append("optimizer_step")
    return problems


def corruption_controls(valid):
    checks = {}
    for name, mutator in {
        "wrong_schema": lambda x: x.update(schema="future-schema"),
        "wrong_role": lambda x: x.update(role="A"),
        "wrong_base": lambda x: x.update(base_sha256="0" * 64),
        "wrong_schedule": lambda x: x.update(schedule_sha256="0" * 64),
        "wrong_version": lambda x: x.update(schedule_version="future"),
        "stale_cursor": lambda x: x.update(cursor=3),
        "duplicate_cursor": lambda x: x.update(cursor=4),
        "skipped_cursor": lambda x: x.update(cursor=6),
        "corrupt_digest": lambda x: x.update(snapshot_sha256="0" * 64),
    }.items():
        sample = json.loads(json.dumps(valid))
        mutator(sample)
        # For all but explicit digest corruption, seal the altered bytes so the intended field check is exercised.
        if name != "corrupt_digest":
            body = {k: v for k, v in sample.items() if k != "snapshot_sha256"}
            sample["snapshot_sha256"] = sha_json(body)
        checks[name] = bool(verify_snapshot(sample, 77111, "a" * 64, "b" * 64, 5))
    return checks


def audit_seed(output, seed, errors):
    raw_path = output / f"input-{seed}.json"
    result_path = output / f"seed-result-{seed}.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    if result.get("schema") != "needle-snapshot-cadence-seed-v1" or result.get("seed") != seed:
        errors.append(f"{seed}:result_identity")
    raw_copy = {k: v for k, v in raw.items() if k != "input_sha256"}
    if raw.get("input_sha256") != sha_json(raw_copy) or result.get("input_sha256") != raw.get("input_sha256"):
        errors.append(f"{seed}:input_hash")
    if raw.get("base_sha256") != sha_json(raw.get("base_state")):
        errors.append(f"{seed}:base_hash")
    if raw.get("schedule_sha256") != sha_json({"order": raw.get("order"), "schedule": raw.get("schedule")}):
        errors.append(f"{seed}:schedule_hash")
    expected_sets = {
        "x_base": (512, 8), "x_a_eval": (N_HELDOUT, 8), "x_support": (N_SUPPORT, 8), "x_b_eval": (N_HELDOUT, 8)
    }
    for name, shape in expected_sets.items():
        rows = raw.get(name, [])
        if len(rows) != shape[0] or any(len(row) != shape[1] for row in rows):
            errors.append(f"{seed}:shape:{name}")
    if raw.get("y_base") != labels(raw.get("x_base", [])):
        errors.append(f"{seed}:base_labels")
    if raw.get("y_a_eval") != labels(raw.get("x_a_eval", [])):
        errors.append(f"{seed}:role_a_labels")
    if raw.get("y_support") != labels(raw.get("x_support", []), flip=True):
        errors.append(f"{seed}:support_labels")
    if raw.get("y_b_eval") != labels(raw.get("x_b_eval", []), flip=True):
        errors.append(f"{seed}:role_b_labels")
    if len(raw.get("schedule", [])) != N_SUPPORT or sorted(raw.get("order", [])) != list(range(N_SUPPORT)):
        errors.append(f"{seed}:schedule_shape")
    if any(len(entry.get("batches", [])) != UPDATES_PER_ARRIVAL or
           any(len(batch) != 32 or any(i < 0 or i >= len(entry["seen"]) for i in batch)
               for batch in entry["batches"]) for entry in raw.get("schedule", [])):
        errors.append(f"{seed}:minibatch_schedule")

    ref = result.get("reference", {})
    ref_records = ref.get("records", [])
    if len(ref_records) != N_SUPPORT:
        errors.append(f"{seed}:reference_rows")
        return result
    # Independently recompute the full held-out predictions for the frozen base and every B state.
    pred_a = predict(raw["base_state"], {"a": raw["initial_adapter"]["a"], "b": raw["initial_adapter"]["b"]}, raw["x_a_eval"])
    if pack := result.get("role_a_predictions_b64"):
        if decode_ids(pack) != pred_a:
            errors.append(f"{seed}:role_a_predictions")
    else:
        errors.append(f"{seed}:role_a_predictions_missing")
    if sum(a == b for a, b in zip(pred_a, raw["y_a_eval"])) / N_HELDOUT != result.get("role_a_accuracy"):
        errors.append(f"{seed}:role_a_accuracy")

    expected_records = {}
    for i, record in enumerate(ref_records, 1):
        if record.get("arrival") != i:
            errors.append(f"{seed}:reference_cursor:{i}")
        pred = predict(raw["base_state"], record.get("adapter", {}), raw["x_b_eval"])
        if decode_ids(record.get("predictions_b64", "")) != pred:
            errors.append(f"{seed}:reference_raw_prediction:{i}")
        acc = sum(a == b for a, b in zip(pred, raw["y_b_eval"])) / N_HELDOUT
        if acc != record.get("accuracy"):
            errors.append(f"{seed}:reference_accuracy:{i}")
        if sha_json(record.get("adapter", {})) != record.get("adapter_sha256"):
            errors.append(f"{seed}:reference_adapter_hash:{i}")
        if sha_json(record.get("optimizer", {})) != record.get("optimizer_sha256"):
            errors.append(f"{seed}:reference_optimizer_hash:{i}")
        expected_records[i] = record

    measured = {}
    for cadence in CADENCES:
        arm = result.get("arms", {}).get(str(cadence), {})
        records = arm.get("records", [])
        if len(records) != N_SUPPORT or arm.get("cadence") != cadence:
            errors.append(f"{seed}:arm_rows:{cadence}")
            continue
        for i, record in enumerate(records, 1):
            ref_record = expected_records.get(i, {})
            if (record.get("adapter") != ref_record.get("adapter") or
                    record.get("optimizer") != ref_record.get("optimizer") or
                    record.get("predictions_b64") != ref_record.get("predictions_b64")):
                errors.append(f"{seed}:resume_divergence:{cadence}:{i}")
            pred = predict(raw["base_state"], record.get("adapter", {}), raw["x_b_eval"])
            if decode_ids(record.get("predictions_b64", "")) != pred:
                errors.append(f"{seed}:arm_raw_prediction:{cadence}:{i}")
        boundaries = arm.get("boundaries", [])
        expected_boundaries = math.ceil(N_SUPPORT / cadence)
        if len(boundaries) != expected_boundaries:
            errors.append(f"{seed}:boundary_count:{cadence}")
            continue
        if arm.get("process_invocations") != expected_boundaries + 1:
            errors.append(f"{seed}:process_count:{cadence}")
        for boundary in boundaries:
            end = boundary.get("end")
            if end is None or end % cadence != 0 and end != N_SUPPORT:
                errors.append(f"{seed}:boundary_cursor:{cadence}")
                continue
            checkpoint_path = output / boundary.get("checkpoint_path", "")
            try:
                blob = checkpoint_path.read_bytes()
                snapshot = json.loads(blob)
                ref_record = expected_records[end]
                if boundary.get("checkpoint_sha256") != snapshot.get("snapshot_sha256"):
                    errors.append(f"{seed}:boundary_digest_record:{cadence}:{end}")
                if snapshot.get("snapshot_sha256") != sha_json({k: v for k, v in snapshot.items() if k != "snapshot_sha256"}):
                    errors.append(f"{seed}:checkpoint_digest:{cadence}:{end}")
                if (snapshot.get("adapter") != ref_record.get("adapter") or
                        snapshot.get("optimizer") != ref_record.get("optimizer")):
                    errors.append(f"{seed}:checkpoint_state:{cadence}:{end}")
                if verify_snapshot(snapshot, seed, raw["base_sha256"], raw["schedule_sha256"], end):
                    errors.append(f"{seed}:checkpoint_contract:{cadence}:{end}")
            except Exception as exc:
                errors.append(f"{seed}:checkpoint_missing:{cadence}:{end}:{type(exc).__name__}")
        final = arm.get("final_checkpoint", {})
        try:
            final_blob = (output / final["path"]).read_bytes()
            final_snapshot = json.loads(final_blob)
            final_check = final.get("validation", {})
            last_ref = expected_records[N_SUPPORT]
            if final.get("sha256") != sha_bytes(final_blob):
                errors.append(f"{seed}:final_checkpoint_bytes:{cadence}")
            if final_check.get("adapter_sha256") != sha_json(last_ref["adapter"]):
                errors.append(f"{seed}:final_restore_adapter:{cadence}")
            if final_check.get("optimizer_sha256") != sha_json(last_ref["optimizer"]):
                errors.append(f"{seed}:final_restore_optimizer:{cadence}")
            if verify_snapshot(final_snapshot, seed, raw["base_sha256"], raw["schedule_sha256"], N_SUPPORT):
                errors.append(f"{seed}:final_snapshot_contract:{cadence}")
        except Exception as exc:
            errors.append(f"{seed}:final_snapshot_missing:{cadence}:{type(exc).__name__}")

        updates = arm.get("update_ms", [])
        if len(updates) != N_SUPPORT:
            errors.append(f"{seed}:update_times:{cadence}")
        else:
            update_flat = updates
            overhead_per_arrival, boundary_ms, total_latency = [], [], []
            for j, boundary in enumerate(boundaries):
                group_size = boundary["end"] - boundary["start"]
                restore_ms = (boundaries[j + 1]["restart_ready_ms"] if j + 1 < len(boundaries)
                              else boundary.get("final_restore_ready_ms"))
                if restore_ms is None:
                    errors.append(f"{seed}:restore_time_missing:{cadence}:{j}")
                    restore_ms = 0.0
                overhead = float(boundary["checkpoint_write_ms"]) + float(restore_ms)
                per_row = overhead / group_size
                boundary_ms.append(overhead)
                for index in range(boundary["start"], boundary["end"]):
                    overhead_per_arrival.append(per_row)
                    total_latency.append(float(update_flat[index]) + per_row)
            measured[str(cadence)] = {
                "update_p95_ms": nearest(update_flat, .95),
                "boundary_p95_ms": nearest(boundary_ms, .95),
                "persistence_per_feedback_mean_ms": sum(overhead_per_arrival) / len(overhead_per_arrival),
                "persistence_per_feedback_p95_ms": nearest(overhead_per_arrival, .95),
                "total_per_feedback_p95_ms": nearest(total_latency, .95),
                "max_unsaved_feedback_on_crash": cadence - 1,
                "n_updates": len(update_flat), "n_checkpoint_boundaries": len(boundaries),
            }
    if not all(result.get("controls", {}).values()):
        errors.append(f"{seed}:route_controls")
    if sha_json(raw["base_state"]) != raw["base_sha256"]:
        errors.append(f"{seed}:base_mutated")
    return {"seed": seed, "role_a_accuracy": result.get("role_a_accuracy"),
            "reference_final_b_accuracy": ref_records[-1].get("accuracy") if ref_records else None,
            "cadences": measured, "role_a_predictions": len(pred_a)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    source, output = Path(args.source), Path(args.out)
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    freeze_sha = sha_bytes((source / "FREEZE.json").read_bytes())
    if (source / "FREEZE.sha256").read_text(encoding="ascii").strip() != freeze_sha:
        errors.append("freeze_sidecar")
    for relative, expected in freeze["source_sha256"].items():
        if sha_bytes((source / relative).read_bytes()) != expected:
            errors.append("source_hash:" + relative)
    invocation = json.loads((output / "FORMAL_INVOCATION.json").read_text(encoding="utf-8"))
    training = output / "training"
    run = json.loads((training / "RUN.json").read_text(encoding="utf-8"))
    if (invocation.get("allocation") != ALLOCATION or invocation.get("formal_invocations") != 1 or
            invocation.get("retry_count") != 0 or invocation.get("freeze_sha256") != freeze_sha):
        errors.append("invocation_contract")
    if run.get("allocation") != ALLOCATION or run.get("seeds") != list(SEEDS) or run.get("retry_count") != 0:
        errors.append("run_contract")
    seed_reports, times_by_cadence = [], {str(k): [] for k in CADENCES}
    for seed in SEEDS:
        name = f"seed-result-{seed}.json"
        if run.get("seed_result_sha256", {}).get(name) != sha_bytes((training / name).read_bytes()):
            errors.append(f"{seed}:result_bytes")
        report = audit_seed(training, seed, errors)
        seed_reports.append(report)
        for k in CADENCES:
            measured = report["cadences"].get(str(k))
            if measured:
                times_by_cadence[str(k)].append(measured)
    control_template = {
        "schema": SNAPSHOT_SCHEMA, "allocation": ALLOCATION, "seed": 77111, "role": "B",
        "base_sha256": "a" * 64, "schedule_sha256": "b" * 64,
        "schedule_version": "eight-adamw-updates-per-feedback-v1", "cursor": 5,
        "adapter": {"a": [[0.0]], "b": [[0.0]]},
        "optimizer": {"step": 40, "exp_avg_a": [[0.0]], "exp_avg_sq_a": [[0.0]],
                      "exp_avg_b": [[0.0]], "exp_avg_sq_b": [[0.0]]},
    }
    control_template["snapshot_sha256"] = sha_json(control_template)
    controls = corruption_controls(control_template)
    if not all(controls.values()):
        errors.append("independent_corruption_controls")
    aggregate = {}
    for k in CADENCES:
        rows = times_by_cadence[str(k)]
        for field in ("update_p95_ms", "boundary_p95_ms", "persistence_per_feedback_mean_ms",
                      "persistence_per_feedback_p95_ms", "total_per_feedback_p95_ms"):
            aggregate.setdefault(str(k), {})[field] = sum(row[field] for row in rows) / len(rows) if rows else None
        aggregate[str(k)]["max_unsaved_feedback_on_crash"] = k - 1
    errors += []
    exact = not errors
    candidates = []
    base_persist = aggregate.get("1", {}).get("persistence_per_feedback_mean_ms")
    if exact and base_persist and base_persist > 0:
        for k in (4, 16):
            row = aggregate[str(k)]
            if (row["update_p95_ms"] <= 60 and row["total_per_feedback_p95_ms"] <= 60 and
                    row["persistence_per_feedback_mean_ms"] <= .8 * base_persist):
                candidates.append(k)
    decision = (f"PASS_CADENCE_{min(candidates)}_SCOPED" if candidates else
                "HOLD_NO_PERSISTENCE_BENEFIT" if exact else "FAIL_AUDIT_OR_RESUME_EQUIVALENCE")
    audit = {"schema": "needle-snapshot-cadence-audit-v1", "allocation": ALLOCATION,
             "audit": "PASS_AUDIT" if exact else "FAIL_AUDIT", "decision": decision,
             "errors": errors, "freeze_sha256": freeze_sha, "seeds": seed_reports,
             "aggregate": aggregate, "corruption_controls": controls,
             "thresholds": {"update_p95_ms_max": 60, "total_per_feedback_p95_ms_max": 60,
                            "persistence_reduction_min": .20, "seeds": list(SEEDS), "cadences": list(CADENCES)}}
    with (output / "AUDIT.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(audit, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    print(json.dumps({"audit": audit["audit"], "decision": decision, "errors": len(errors),
                      "aggregate": aggregate}, sort_keys=True))
    return 0 if exact else 2


if __name__ == "__main__":
    raise SystemExit(main())

