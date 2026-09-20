"""Offline structural audit for the frozen Issue #3701 result; reads one JSON object from stdin."""
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
if result["outcome"] != "PASS_MULTI_SKILL_ROUTING_SCOPED":
    fail("unexpected_outcome")
if result["execution"]["formal_allocations"] != 1 or result["execution"]["retries"] != 0:
    fail("allocation_count_mismatch")
if result["execution"]["mode"] != "Windows host; Docker Desktop daemon unavailable (not a container run)":
    fail("execution_mode_misreported")
if result["execution"]["device"] != "NVIDIA GeForce RTX 3080 Laptop GPU":
    fail("unexpected_device")
if sorted(result["measurements"]["routed_accuracy"]) != ["A", "B", "C"]:
    fail("routed_skill_set_mismatch")
if not all(v >= 0.90 for v in result["measurements"]["routed_accuracy"].values()):
    fail("routed_accuracy_gate_failed")
if set(result["invalid_routes"].values()) != {"YIELD"} or len(result["invalid_routes"]) != 6:
    fail("invalid_route_gate_failed")
if not all(result["gates"].values()):
    fail("declared_gate_failed")
if set(result["measurements"]["snapshots"]) != {"global", "B", "C"}:
    fail("snapshot_set_mismatch")
for key, snap in result["measurements"]["snapshots"].items():
    if snap["bytes"] <= 0 or len(snap["sha256"]) != 64:
        fail(f"bad_snapshot_metadata:{key}")
    if not snap["roundtrip_tensor_exact"] or not snap["rollback_tensor_exact"]:
        fail(f"snapshot_or_rollback_failed:{key}")
if result["gates"]["base_immutable"] is not True:
    fail("base_mutability_gate_failed")
if result["data_sha256"].keys() != {"A_train","B_support","C_support","A_eval","B_eval","C_eval"}:
    fail("data_hash_set_mismatch")
if not all(len(v) == 64 for v in result["data_sha256"].values()):
    fail("malformed_data_hash")
print(json.dumps({
    "audit":"PASS_OFFLINE_STRUCTURAL_AUDIT",
    "runner_sha256":sha,
    "outcome":result["outcome"],
    "routed_accuracy":result["measurements"]["routed_accuracy"],
    "checks":result["gates"],
    "invalid_route_count":len(result["invalid_routes"])
}, indent=2, sort_keys=True))
