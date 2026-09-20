"""Structural/result-shape audit for Issue #3701; accepts base64 source/result/prereg on stdin.
This does not regenerate data or independently recompute aggregate accuracy.
"""
import base64, hashlib, json, sys

def fail(message):
    print(json.dumps({"audit":"FAIL","error":message}, sort_keys=True))
    raise SystemExit(1)

try:
    bundle = json.load(sys.stdin)
    runner = base64.b64decode(bundle["runner_b64"], validate=True)
    result_raw = base64.b64decode(bundle["result_b64"], validate=True)
    prereg = base64.b64decode(bundle["prereg_b64"], validate=True).decode("utf-8")
    result = json.loads(result_raw)
except Exception as exc:
    fail(f"input_decode:{type(exc).__name__}:{exc}")

sha = hashlib.sha256(runner).hexdigest()
if sha != result["source"]["sha256"] or sha not in prereg:
    fail("frozen_runner_hash_mismatch")
if len(runner) != result["source"]["bytes"]:
    fail("frozen_runner_length_mismatch")
if result["outcome"] != "HOLD_PROTOCOL_DEVIATION":
    fail("disposition_mismatch")
if result["execution"]["formal_allocations_on_this_branch"] != 1 or result["execution"]["retries_on_this_branch"] != 0:
    fail("branch_allocation_count_mismatch")
if result["execution"]["mode"] != "Windows host; Docker Desktop daemon unavailable (not a container run)":
    fail("execution_mode_misreported")
if result["execution"]["device"] != "NVIDIA GeForce RTX 3080 Laptop GPU":
    fail("unexpected_device")
reported_routed = result["measurements"]["routed_accuracy"]
reported_shared = result["measurements"]["shared_sequential_accuracy"]
if set(reported_routed) != {"A", "B", "C"} or not all(v >= 0.90 for v in reported_routed.values()):
    fail("reported_routed_accuracy_gate_not_met")
if not any(reported_shared[k] < 0.90 for k in ("B", "C")):
    fail("reported_shared_interference_discriminator_not_met")
if set(result["invalid_routes"].values()) != {"YIELD"} or len(result["invalid_routes"]) != 6:
    fail("invalid_route_record_mismatch")
if not all(result["gates"].values()):
    fail("recorded_observed_gate_mismatch")
protocol = result["protocol_audit"]
if protocol["full_module_state_dict_tensor_roundtrip_verified"] is not False:
    fail("protocol_deviation_not_disclosed")
if protocol["setup_time_measured"] is not False or protocol["per_row_predictions_retained"] is not False:
    fail("measurement_limits_not_disclosed")
if protocol["snapshot_scope"] != "adapter trainable tensors a/b only; full LoRA module state_dict was not included in snapshot payload":
    fail("snapshot_scope_mismatch")
snapshots = result["measurements"]["snapshots"]
if set(snapshots) != {"global", "B", "C"}:
    fail("snapshot_set_mismatch")
for key, snap in snapshots.items():
    if snap["bytes"] <= 0 or len(snap["sha256"]) != 64:
        fail(f"bad_snapshot_metadata:{key}")
    if not snap["roundtrip_tensor_exact"] or not snap["rollback_tensor_exact"]:
        fail(f"adapter_trainable_tensor_check_failed:{key}")
if set(result["data_sha256"]) != {"A_train","B_support","C_support","A_eval","B_eval","C_eval"}:
    fail("data_hash_set_mismatch")
if not all(len(v) == 64 for v in result["data_sha256"].values()):
    fail("malformed_data_hash")
if not result.get("related_attempts") or result["related_attempts"][0]["outcome"] != "STOP_FORMAL_CUBLAS_DETERMINISM_CONFIGURATION":
    fail("parallel_STOP_not_disclosed")
print(json.dumps({
    "audit":"PASS_OFFLINE_STRUCTURAL_RESULT_SHAPE_AUDIT",
    "metric_recomputation":"NOT_PERFORMED_NO_PER_ROW_PREDICTIONS",
    "runner_sha256":sha,
    "disposition":result["outcome"],
    "recorded_routed_accuracy":reported_routed,
    "recorded_shared_accuracy":reported_shared,
    "snapshot_scope":protocol["snapshot_scope"],
    "invalid_route_count":len(result["invalid_routes"]),
    "setup_time_measured":False
}, indent=2, sort_keys=True))
