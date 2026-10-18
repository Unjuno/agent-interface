"""One-shot paired synthetic mutable-record custody candidate and probe."""
import copy
import hashlib
import importlib.util
import json
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN_LABEL = "formal_02"
OUT = HERE / "results/formal_02/candidate.json"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite frozen output: {OUT}")

PINNED = {
    "input_owner_v13_candidate.py": "0e3c65aadfba76b644f1ca99afa267bc873bc120320a4b0cac67dafb82cfa814",
    "bridge_v2_candidate.py": "81e759b0484ac5b7854da0ebcffa917035f56b83a3dbfda40cafbb7f9f5138d1",
}
for name, expected in PINNED.items():
    path = ROOT / "research/doom/map01_v39_expiry_pending_owner_current_a03_20261005/candidate_source" / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"source hash mismatch {name}: {actual}")

test = ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
spec = importlib.util.spec_from_file_location("mutable_record_owner_harness", test)
harness_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness_mod
spec.loader.exec_module(harness_mod)
fixture = harness_mod.load_v12_test_harness()
source_dir = (ROOT / "research/doom/map01_v39_expiry_pending_owner_current_a03_20261005" / "candidate_source")
sys.path.insert(0, str(source_dir))
owner_path = source_dir / "input_owner_v13_candidate.py"
owner_spec = importlib.util.spec_from_file_location("input_owner_v13_candidate", owner_path)
owner_mod = importlib.util.module_from_spec(owner_spec)
sys.modules[owner_spec.name] = owner_mod
owner_spec.loader.exec_module(owner_mod)
fixture.owner_module = owner_mod
sys.path.insert(0, str(HERE))
bridge_path = source_dir / "bridge_v2_candidate.py"
bridge_spec = importlib.util.spec_from_file_location("bridge_v2_candidate", bridge_path)
bridge_mod = importlib.util.module_from_spec(bridge_spec)
sys.modules[bridge_spec.name] = bridge_mod
bridge_spec.loader.exec_module(bridge_mod)
probe_spec = importlib.util.spec_from_file_location("bridge_neutral_revisit_probe", HERE / "bridge_neutral_revisit_probe.py")
probe_mod = importlib.util.module_from_spec(probe_spec)
sys.modules[probe_spec.name] = probe_mod
probe_spec.loader.exec_module(probe_mod)


def run_case(label, backend_type):
    harness = fixture.Harness(owner_mod)
    owner = harness.owner
    backend = object.__new__(backend_type)
    lease = fixture.Lease(intent=f"intent-{label}")
    events = []
    backend.owner = owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = (f"mutable-record-{label}", 0)
    backend._owner_record_cursor = len(owner.records)
    backend.emit = events.append

    at_aggregate_gate = threading.Event()
    unblock_aggregate = threading.Event()
    original_query_pointer = fixture.Root.query_pointer
    def gated_query_pointer(root):
        at_aggregate_gate.set()
        if not unblock_aggregate.wait(3):
            raise TimeoutError("aggregate query gate timed out")
        return original_query_pointer(root)

    worker_error = []
    try:
        backend.raw("F8", True)
        query_before_release = harness.d.query_i
        # Release pre-sample is +1; release post-sample is +2. Fail only the
        # post-sample. The later aggregate query is +3 and succeeds.
        harness.d.query_fail_on.add(query_before_release + 2)
        fixture.Root.query_pointer = gated_query_pointer
        def release_owner():
            try:
                owner.call("release", lease)
            except BaseException as exc:
                worker_error.append({"type": type(exc).__name__, "message": str(exc)})
        worker = threading.Thread(target=release_owner, name=f"release-{label}")
        worker.start()
        if not at_aggregate_gate.wait(3):
            raise TimeoutError("owner did not append partial record before aggregate gate")
        snapshot_at_gate = copy.deepcopy(owner.records)
        backend._drain_owner_records()
        events_after_partial_drain = copy.deepcopy(events)
        cursor_after_partial_drain = backend._owner_record_cursor
        held_after_partial_drain = sorted(backend.held)
        unblock_aggregate.set()
        worker.join(3)
        if worker.is_alive():
            raise TimeoutError("owner cleanup thread did not finish")
        final_records = copy.deepcopy(owner.records)
        final_owner_state = owner.call("input_state", lease)
        events_before_final_drain = copy.deepcopy(events)
        backend._drain_owner_records()
        events_after_final_drain = copy.deepcopy(events)
        output = {
            "case": label,
            "owner_error": worker_error,
            "query_before_release": query_before_release,
            "query_fail_indices": sorted(harness.d.query_fail_on),
            "snapshot_at_aggregate_gate": snapshot_at_gate,
            "events_after_partial_drain": events_after_partial_drain,
            "cursor_after_partial_drain": cursor_after_partial_drain,
            "held_after_partial_drain": held_after_partial_drain,
            "final_owner_records": final_records,
            "events_before_final_drain": events_before_final_drain,
            "events_after_final_drain": events_after_final_drain,
            "final_owner_held_codes": final_owner_state["owned_keycodes"],
            "final_fake_physical_keys": sorted(harness.d.physical),
            "final_bridge_held": sorted(backend.held),
            "final_cursor": backend._owner_record_cursor,
            "final_drain_added_event_count": len(events_after_final_drain) - len(events_before_final_drain),
        }
        return output
    finally:
        unblock_aggregate.set()
        fixture.Root.query_pointer = original_query_pointer
        harness.close()


result = {
    "schema": "map01-v39-mutable-release-record-custody-a01-v1",
    "source_sha256": PINNED,
    "run_label": RUN_LABEL,
    "cases": [
        run_case("baseline", bridge_mod.Backend),
        run_case("neutral_revisit_probe", probe_mod.Backend),
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT)
