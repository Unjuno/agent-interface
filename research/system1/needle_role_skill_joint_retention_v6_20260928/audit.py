"""Independent v6 raw audit; imports the frozen predecessor oracle, not runner.py."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

import torch

ALLOCATION = "needle-role-skill-joint-retention-20260928-v6"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (9980211, 9980311, 9980411)
ARMS = ("SHARED_B_ONLY", "SHARED_A_REPLAY", "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS")
SCHEMA = "needle-role-skill-joint-retention-raw-v3-online-window"
ARRIVALS = 16
MICROSTEPS_PER_FEEDBACK = 8
QUERY_BATCH = 256
ROOT = Path(__file__).resolve().parent
LEGACY_AUDIT_PATH = Path(__file__).resolve().parent / "lineage/audit.py"
LEGACY_FREEZE_PATH = LEGACY_AUDIT_PATH.with_name("FORMAL_FREEZE.json")
LEGACY_FREEZE_SIDECAR_PATH = LEGACY_AUDIT_PATH.with_name("FORMAL_FREEZE.sha256")
LEGACY_FORMAL_FREEZE_SHA256 = "482449e97f3b399b166da11fe54a2be2b9df1f13fab1e95753b283614a20cd7c"
LEGACY_AUDIT_SHA256 = "6abf8cc48d81c5b4267d993e9d992a15d9015f39f0a50558acfcc6d11bcc4558"


def load_lineage_auditor():
    freeze_bytes = LEGACY_FREEZE_PATH.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(freeze_bytes).hexdigest() != LEGACY_FORMAL_FREEZE_SHA256:
        raise ValueError("legacy_freeze_sha256")
    if LEGACY_FREEZE_SIDECAR_PATH.read_bytes().replace(b"\r\n", b"\n") != (LEGACY_FORMAL_FREEZE_SHA256 + "\n").encode("ascii"):
        raise ValueError("legacy_freeze_sidecar")
    source_bytes = LEGACY_AUDIT_PATH.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(source_bytes).hexdigest() != LEGACY_AUDIT_SHA256:
        raise ValueError("legacy_auditor_sha256")
    spec = importlib.util.spec_from_file_location("needle_role_v5_independent_oracle", LEGACY_AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise ValueError("legacy_auditor_import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load_lineage_auditor()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_docker_argv(source_path: str, output_path: str) -> list[str] | None:
    try:
        source, output = Path(source_path).resolve(strict=True), Path(output_path).resolve(strict=True)
    except (OSError, TypeError):
        return None
    if (not source.is_dir() or not output.is_dir() or source == output
            or source in output.parents or output in source.parents
            or source != Path(__file__).resolve().parent):
        return None
    return [
        "docker", "run", "--pull=never", "--platform=linux/amd64",
        "--network=none", "--read-only", "--cpus=1", "--memory=2g",
        "--pids-limit=64", "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m",
        "--entrypoint=python",
        "--mount", f"type=bind,source={source},target=/src,readonly",
        "--mount", f"type=bind,source={output},target=/out",
        "--workdir=/src", "--env=NEEDLE_OUTPUT=/out",
        "--env=NEEDLE_SEEDS=" + ",".join(map(str, SEEDS)),
        IMAGE_ID, "-B", "/src/runner.py",
    ]


def independent_online_window_errors(record: object) -> list[str]:
    """Auditor-owned reconstruction; does not import the candidate validator."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["event_record_not_object"]
    queries, feedback = record.get("queries"), record.get("feedback")
    if not isinstance(queries, list) or not queries:
        return ["queries_missing"]
    if not isinstance(feedback, list) or not feedback:
        return ["feedback_missing"]
    by_id = {}
    for qi, query in enumerate(queries):
        if not isinstance(query, dict):
            errors.append(f"query_invalid:{qi}"); continue
        qid, worker = query.get("query_id"), query.get("worker_id")
        qs, qe = query.get("inference_start_ns"), query.get("inference_end_ns")
        if (not isinstance(qid, str) or not qid or qid in by_id or not isinstance(worker, str)
                or not worker or type(qs) is not int or type(qe) is not int or qs < 0 or qe <= qs):
            errors.append(f"query_invalid:{qi}"); continue
        calls = query.get("inference_calls")
        valid_calls = []
        if not isinstance(calls, list) or not calls:
            errors.append(f"query_inference_calls_missing:{qid}")
        else:
            for ci, call in enumerate(calls):
                if not isinstance(call, dict):
                    errors.append(f"inference_call_invalid:{qid}:{ci}"); continue
                cs, ce = call.get("call_start_ns"), call.get("call_end_ns")
                if (type(cs) is not int or type(ce) is not int or not qs <= cs < ce <= qe):
                    errors.append(f"inference_call_invalid:{qid}:{ci}")
                else:
                    valid_calls.append((cs, ce))
        by_id[qid] = (qs, qe, worker, valid_calls)
    ids, overlap_count = set(), 0
    for fi, item in enumerate(feedback):
        if not isinstance(item, dict):
            errors.append(f"feedback_invalid:{fi}"); continue
        fid, qid = item.get("feedback_id"), item.get("query_id")
        if not isinstance(fid, str) or not fid or fid in ids:
            errors.append(f"feedback_id_invalid_or_duplicate:{fi}"); continue
        ids.add(fid)
        query = by_id.get(qid)
        arrived, consumed = item.get("arrived_ns"), item.get("consumed_ns")
        start, end = item.get("update_start_ns"), item.get("update_end_ns")
        trainer = item.get("trainer_worker_id")
        if (type(arrived) is not int or type(consumed) is not int or arrived < 0 or consumed < arrived):
            errors.append(f"feedback_clock_invalid:{fid}"); continue
        if query is None:
            errors.append(f"feedback_query_missing:{fid}"); continue
        qs, qe, qworker, calls = query
        if not qs < arrived <= consumed < qe:
            errors.append(f"feedback_not_consumed_inside_query:{fid}")
        if type(start) is not int or type(end) is not int or start < 0 or end <= start or not start <= consumed < end:
            errors.append(f"update_interval_does_not_cover_consumption:{fid}"); continue
        if not isinstance(trainer, str) or not trainer or trainer == qworker:
            errors.append(f"workers_not_independent:{fid}")
        if any(start < call_end and call_start < end for call_start, call_end in calls):
            overlap_count += 1
        else:
            errors.append(f"update_does_not_overlap_inference_call:{fid}")
    # This allocation registers one online query/update event for every
    # feedback item. Do not let a single overlapping event mask a disjoint
    # event elsewhere in the three-seed/four-arm record.
    if overlap_count != len(feedback):
        errors.append("not_every_feedback_update_overlaps_inference")
    return errors


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def expected_feedback(seed: int) -> tuple[list[list[float]], list[int]]:
    rows, labels = [], []
    for arrival in range(ARRIVALS):
        generator = random.Random(seed * 1009 + 303 + arrival * 7919)
        bit = float(arrival % 2)
        row = [bit, *[generator.random() for _ in range(7)], 1.0]
        rows.append(torch.tensor(row, dtype=torch.float32).tolist())
        labels.append(1 - int(bit))
    return rows, labels


def digest_tensor_state(state: dict) -> str:
    return sha(canonical(state))


def audit_online_arm(seed: int, arm: str, arm_row: dict, support_x: list,
                     support_y: list, test_b: torch.Tensor, init: dict) -> list[str]:
    errors: list[str] = []
    record = arm_row.get("online_window")
    protocol_errors = independent_online_window_errors(record)
    errors.extend(f"{seed}:{arm}:online:{item}" for item in protocol_errors)
    queries = record.get("queries", []) if isinstance(record, dict) else []
    feedback = record.get("feedback", []) if isinstance(record, dict) else []
    if len(queries) != ARRIVALS or len(feedback) != ARRIVALS:
        return errors + [f"{seed}:{arm}:online_cardinality"]

    separate = arm == "ROUTED_SEPARATE_SKILLS"
    adapter_id = "skill-B-online-v1" if separate else (
        "role-shared-online-v1" if arm == "ROUTED_SHARED_ADAPTER" else "shared-online-v1")
    previous_b = {"left": init["left"], "right": init["right"]}
    previous_a = {"left": init["left"], "right": init["right"]}
    core, _, _, _ = legacy.make_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    for arrival, (query, item) in enumerate(zip(queries, feedback)):
        expected_id = f"{seed}:{arm}:q{arrival + 1:02d}"
        expected_feedback_id = f"{seed}:{arm}:f{arrival + 1:02d}"
        if query.get("query_id") != expected_id or query.get("role") != "B" or query.get("scope") != "synthetic-role-v1":
            errors.append(f"{seed}:{arm}:{arrival}:query_identity")
        if (query.get("generation") != 3 or query.get("adapter_generation") != arrival
                or query.get("adapter_id") != adapter_id):
            errors.append(f"{seed}:{arm}:{arrival}:query_route_generation")
        if item.get("feedback_id") != expected_feedback_id or item.get("query_id") != expected_id:
            errors.append(f"{seed}:{arm}:{arrival}:feedback_identity")
        expected_state = previous_b if separate or arm in ("SHARED_B_ONLY", "SHARED_A_REPLAY", "ROUTED_SHARED_ADAPTER") else previous_a
        snapshot = query.get("snapshot")
        if snapshot != expected_state or query.get("snapshot_sha256") != digest_tensor_state(expected_state):
            errors.append(f"{seed}:{arm}:{arrival}:snapshot_version")
        calls = query.get("inference_calls", [])
        audit_adapter = legacy.AuditAdapter()
        with torch.no_grad():
            audit_adapter.left.copy_(torch.tensor(expected_state["left"], dtype=torch.float32))
            audit_adapter.right.copy_(torch.tensor(expected_state["right"], dtype=torch.float32))
        probe = test_b[:QUERY_BATCH]
        expected_prediction = legacy.predictions(core, audit_adapter, probe)
        expected_prediction_sha = sha(canonical(expected_prediction))
        for call_index, call in enumerate(calls):
            if call.get("call_index") != call_index or call.get("n") != QUERY_BATCH:
                errors.append(f"{seed}:{arm}:{arrival}:{call_index}:inference_call_schema")
            if call.get("prediction_sha256") != expected_prediction_sha:
                errors.append(f"{seed}:{arm}:{arrival}:{call_index}:inference_snapshot_replay")
        expected_row = support_x[arrival]
        expected_row_sha = sha(canonical(expected_row))
        if item.get("feedback_sha256") != expected_row_sha or support_y[arrival] != 1 - int(expected_row[0]):
            errors.append(f"{seed}:{arm}:{arrival}:feedback_bytes")
        update_ns = arm_row.get("update_ns", [])
        step_start = arrival * MICROSTEPS_PER_FEEDBACK
        step_end = step_start + MICROSTEPS_PER_FEEDBACK
        if (len(update_ns) != ARRIVALS * MICROSTEPS_PER_FEEDBACK
                or item.get("optimizer_step_start") != step_start
                or item.get("optimizer_step_count") != MICROSTEPS_PER_FEEDBACK
                or item.get("update_total_ns") != item.get("update_end_ns", 0) - item.get("update_start_ns", 0)
                or item.get("optimizer_steps") != MICROSTEPS_PER_FEEDBACK):
            errors.append(f"{seed}:{arm}:{arrival}:update_receipt_binding")
        checkpoint = arm_row.get("arrivals", [])
        if arrival >= len(checkpoint):
            errors.append(f"{seed}:{arm}:{arrival}:checkpoint_missing")
            continue
        skills = checkpoint[arrival].get("skills", {})
        previous_a = skills.get("A", previous_a)
        previous_b = skills.get("B", previous_b)
    return errors


def audit_document(raw: dict, receipt: dict | None = None, raw_sha256: str | None = None) -> dict:
    errors: list[str] = []
    scientific_failures: list[str] = []
    results = []
    if (raw.get("schema") != SCHEMA or raw.get("allocation") != ALLOCATION
            or raw.get("seeds") != list(SEEDS) or raw.get("arms") != list(ARMS)):
        errors.append("raw_identity")
    environment = raw.get("environment", {})
    if (environment.get("image_id") != IMAGE_ID or environment.get("network") != "none"
            or environment.get("pull") != "never" or environment.get("device") != "cpu"
            or environment.get("threads") != 1 or environment.get("interop_threads") != 1):
        errors.append("environment")
    if receipt is None:
        errors.append("formal_receipt_missing")
    else:
        argv = receipt.get("command_argv")
        try:
            expected_argv = expected_docker_argv(receipt["source_path"], receipt["output_path"])
        except (KeyError, TypeError, ValueError, OSError):
            expected_argv = None
        if expected_argv is None or not isinstance(argv, list) or argv != expected_argv:
            errors.append("formal_argv_contract")
        if (receipt.get("command_argv_sha256") != sha(canonical(argv))
                if isinstance(argv, list) else True):
            errors.append("formal_argv_digest")
        if (receipt.get("allocation") != ALLOCATION or receipt.get("issue") != 5081
                or receipt.get("lease_issue") != 5085
                or receipt.get("image_id") != IMAGE_ID or receipt.get("seeds") != list(SEEDS)
                or not isinstance(receipt.get("main_sha"), str) or len(receipt["main_sha"]) != 40
                or not isinstance(receipt.get("branch"), str)
                or not isinstance(receipt.get("docker_context"), str)
                or receipt.get("exit_code") != 0 or receipt.get("formal_invocations") != 1
                or receipt.get("retries") != 0):
            errors.append("formal_receipt_identity")
        if (not isinstance(receipt.get("lease_id"), str) or not receipt["lease_id"]
                or not isinstance(receipt.get("owner_comment_url"), str)):
            errors.append("formal_owner_lease")
        comment = receipt.get("owner_lease_comment")
        if (not isinstance(comment, dict)
                or comment.get("html_url") != receipt.get("owner_comment_url")
                or comment.get("issue_url") != "https://api.github.com/repos/Unjuno/agent-interface/issues/5085"
                or comment.get("user_login") != "Unjuno"):
            errors.append("formal_owner_comment_provenance")
        else:
            body = comment.get("body")
            blocks = (re.findall(r"<!-- needle-docker-owner-lease-v1\n(\{.*?\})\n-->",
                                 body, re.DOTALL) if isinstance(body, str) else [])
            try:
                owner_payload = json.loads(blocks[0]) if len(blocks) == 1 else None
            except (TypeError, json.JSONDecodeError):
                owner_payload = None
            expected_payload = {
                "schema": "needle-docker-owner-lease-v1", "allocation": ALLOCATION,
                "issue": 5085, "main_sha": receipt.get("main_sha"),
                "branch": receipt.get("branch"), "docker_context": receipt.get("docker_context"),
                "lease_id": receipt.get("lease_id"), "slot_start_utc": receipt.get("slot_start_utc"),
                "slot_end_utc": receipt.get("slot_end_utc"), "expires_at_utc": receipt.get("expires_at_utc"),
            }
            if owner_payload != expected_payload:
                errors.append("formal_owner_comment_payload")
        try:
            slot_start = datetime.fromisoformat(receipt["slot_start_utc"].replace("Z", "+00:00"))
            slot_end = datetime.fromisoformat(receipt["slot_end_utc"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(receipt["expires_at_utc"].replace("Z", "+00:00"))
            started = datetime.fromisoformat(receipt["started_at_utc"].replace("Z", "+00:00"))
            finished = datetime.fromisoformat(receipt["finished_at_utc"].replace("Z", "+00:00"))
            if not (slot_start <= started <= finished < min(slot_end, expires)):
                errors.append("formal_outside_owner_slot")
        except (KeyError, TypeError, ValueError):
            errors.append("formal_slot_timestamps")
        if receipt.get("formal_result_present") is not True:
            errors.append("formal_result_missing")
        if (not isinstance(receipt.get("raw_result_sha256"), str)
                or len(receipt["raw_result_sha256"]) != 64
                or receipt.get("raw_result_sha256") != raw_sha256):
            errors.append("formal_raw_digest_type")
    runs = raw.get("runs", [])
    if [item.get("seed") for item in runs] != list(SEEDS):
        errors.append("seed_denominator")

    for run_row in runs:
        seed = run_row.get("seed")
        if seed not in SEEDS:
            errors.append("unexpected_seed")
            continue
        core, train_x, train_y, schedule = legacy.make_base(seed)
        for parameter in core.parameters():
            parameter.requires_grad_(False)
        base = legacy.state_dict_json(core)
        if (run_row.get("base") != base or run_row.get("base_sha256") != sha(canonical(base))
                or run_row.get("base_after_sha256") != sha(canonical(base))
                or run_row.get("base_immutable") is not True):
            errors.append(f"{seed}:base_identity_immutability")
        memory, test_a, test_b = legacy.sample(16, seed, 202, 0), legacy.sample(256, seed, 404, 0), legacy.sample(256, seed, 505, 1)
        support_x, support_y = expected_feedback(seed)
        expected_fields = {
            "base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(),
            "base_row_indices": schedule, "memory_x": memory.tolist(),
            "memory_y": legacy.a_labels(memory).tolist(), "support_x": support_x,
            "support_y": support_y, "test_a_x": test_a.tolist(),
            "test_a_y": legacy.a_labels(test_a).tolist(), "test_b_x": test_b.tolist(),
            "test_b_y": legacy.b_labels(test_b).tolist(),
        }
        for key, expected in expected_fields.items():
            if run_row.get(key) != expected:
                errors.append(f"{seed}:{key}")
        hashes = run_row.get("dataset_sha256", {})
        if set(hashes) != set(expected_fields):
            errors.append(f"{seed}:dataset_hash_key_set")
        for key, expected in expected_fields.items():
            if hashes.get(key) != sha(canonical(expected)):
                errors.append(f"{seed}:{key}:digest")
        all_rows = [set(tuple(row) for row in expected_fields[key]) for key in
                    ("base_train_x", "memory_x", "support_x", "test_a_x", "test_b_x")]
        if any(all_rows[i] & all_rows[j] for i in range(len(all_rows)) for j in range(i + 1, len(all_rows))):
            errors.append(f"{seed}:split_overlap")
        torch.manual_seed(seed + 500)
        init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
        if run_row.get("init_adapter") != init:
            errors.append(f"{seed}:initial_adapter")
        arm_rows = {row.get("arm"): row for row in run_row.get("arms", [])}
        if set(arm_rows) != set(ARMS):
            errors.append(f"{seed}:arm_set")
            continue
        final = {}
        for arm in ARMS:
            arm_row = arm_rows[arm]
            errors.extend(audit_online_arm(seed, arm, arm_row, support_x, support_y,
                                           test_b, init))
            arm_errors, curves, max_update = legacy.replay_arm(
                arm, core, torch.tensor(support_x, dtype=torch.float32),
                torch.tensor(support_y, dtype=torch.long), memory, legacy.a_labels(memory),
                test_a, test_b, init, arm_row)
            errors.extend(f"{seed}:{item}" for item in arm_errors)
            final[arm] = {"A": curves["A"][-1], "B": curves["B"][-1],
                          "max_update_ms": max_update}
        routed = final["ROUTED_SEPARATE_SKILLS"]
        if (routed["A"] < .90 or routed["B"] < .90
                or any(routed["A"] < final[arm]["A"] + .10 for arm in ARMS[:3])
                or routed["B"] < max(final[arm]["B"] for arm in ARMS[:3]) - .10):
            scientific_failures.append(f"{seed}:retention_or_comparator_threshold:{final}")
        results.append({"seed": seed, "final": final})

    decision = ("HOLD_AUDIT_INTEGRITY" if errors else
                "FAIL_QUALITY_GATE" if scientific_failures else
                "PASS_ROLE_SKILL_JOINT_RETENTION_SCOPED")
    return {"schema": "needle-role-skill-joint-retention-audit-v1",
            "audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
            "decision": decision, "errors": errors,
            "scientific_failures": scientific_failures,
            "n_seeds": len(results), "n_online_queries": sum(
                len(arm.get("online_window", {}).get("queries", []))
                for run in runs for arm in run.get("arms", [])),
            "thresholds": {"routed_A": .90, "routed_B": .90,
                           "A_gain_each_shared": .10,
                           "routed_B_gap_to_best_shared": .10,
                           "update_ms_strict": 60},
            "results": results}


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py RAW_JSON RECEIPT_JSON AUDIT_JSON")
    raw_path, receipt_path, audit_path = map(Path, sys.argv[1:])
    raw_bytes, receipt_bytes = raw_path.read_bytes(), receipt_path.read_bytes()
    raw = json.loads(raw_bytes, object_pairs_hook=unique_pairs)
    receipt = json.loads(receipt_bytes, object_pairs_hook=unique_pairs)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    raw_digest = sha(raw_bytes)
    result = audit_document(raw, receipt, raw_digest)
    result["raw_sha256"] = raw_digest
    result["receipt_sha256"] = sha(receipt_bytes)
    payload = canonical(result) + b"\n"
    with audit_path.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"audit": result["audit"], "decision": result["decision"],
                      "errors": len(result["errors"]),
                      "scientific_failures": len(result["scientific_failures"]),
                      "queries": result["n_online_queries"]}, sort_keys=True))
    raise SystemExit(0 if result["audit"] == "PASS_AUDIT" else 2)


if __name__ == "__main__":
    main()
