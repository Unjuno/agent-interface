"""One-shot deterministic fake-display probe of owner cleanup query failures."""
import hashlib
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "results/construction-a01/outcome.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def check_sources():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for path, expected in freeze["inputs"].items():
        if digest(REPO / path) != expected["sha256"]:
            raise SystemExit(f"STOP_SOURCE_HASH {path}")
    for path, expected in freeze["local_inputs"].items():
        if digest(HERE / path) != expected["sha256"]:
            raise SystemExit(f"STOP_LOCAL_SOURCE_HASH {path}")


def run_case(harness_module, owner_module, bridge_module, mode):
    harness = harness_module.Harness(owner_module)
    lease = harness_module.Lease(intent="intent-release-query-probe-a01")
    backend = object.__new__(bridge_module.Backend)
    backend.owner = harness.owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = None
    backend._owner_record_cursor = len(harness.owner.records)
    backend.events = []
    backend.emit = backend.events.append
    armed = threading.Event()
    injected = threading.Event()

    original_root_query = harness_module.Root.query_pointer
    original_keymap = harness.d.query_keymap
    original_fail_set = set(harness.d.query_fail_on)

    def root_query_with_failure(root):
        if mode == "pointer_failure" and armed.is_set() and not injected.is_set() and not harness.d.physical:
            injected.set()
            raise RuntimeError("injected aggregate query_pointer failure")
        return original_root_query(root)

    harness_module.Root.query_pointer = root_query_with_failure
    fail_query_at = None
    if mode == "keymap_failure":
        def keymap_with_failure():
            next_call = harness.d.query_i + 1
            if armed.is_set() and not injected.is_set() and next_call == fail_query_at:
                harness.d.query_i += 1
                injected.set()
                raise RuntimeError("injected aggregate query_keymap failure")
            return original_keymap()
        harness.d.query_keymap = keymap_with_failure

    def action(self, _identifier, _index):
        nonlocal fail_query_at
        self.raw("F8", True)
        if mode == "keymap_failure":
            # Two per-key down samples already occurred. During cleanup, two
            # more samples bracket KeyRelease; the next call is aggregate.
            fail_query_at = harness.d.query_i + 3
        armed.set()
        self.lease.cancel.set()

    parent = bridge_module.Backend.__bases__[0].__bases__[0]
    missing = object()
    previous = parent.__dict__.get("execute", missing)

    def execute(self, _step, _cancel, identifier, index):
        return action(self, identifier, index)

    parent.execute = execute
    escaped = None
    try:
        try:
            backend.execute({}, lease.cancel, f"query-failure-{mode}", 4)
        except BaseException as exc:  # retained as raw outcome, not hidden
            escaped = f"{type(exc).__name__}: {exc}"

        deadline = time.monotonic() + 1.0
        while harness.d.physical and time.monotonic() < deadline:
            time.sleep(0.001)
        if harness.d.physical:
            escaped = escaped or "STOP: fake key did not release before boundary"

        records = list(harness.owner.records)
        state = harness.owner.call("input_state", lease)
        return {
            "case": mode,
            "injected_failure_observed": injected.is_set(),
            "injected_failure_count": int(injected.is_set()),
            "execution_exception": escaped,
            "fake_physical_keys_at_boundary": sorted(harness.d.physical),
            "owner_records_at_boundary": records,
            "owner_release_record_count": sum(r.get("event") == "owner_release" for r in records),
            "owner_release_measurement_rows": sum(
                len(r.get("per_key_release_measurements", []))
                for r in records if r.get("event") == "owner_release"),
            "bridge_release_measurement_rows": sum(
                r.get("event") == "input_release_measurement" for r in backend.events),
            "bridge_event_rows": list(backend.events),
            "bridge_held_at_boundary": sorted(backend.held),
            "owner_state_at_boundary": state,
            "query_keymap_count": harness.d.query_i,
        }
    finally:
        if previous is missing:
            delattr(parent, "execute")
        else:
            parent.execute = previous
        harness_module.Root.query_pointer = original_root_query
        harness.d.query_keymap = original_keymap
        harness.d.query_fail_on = original_fail_set
        harness.close()
def main():
    if OUT.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS {OUT}")
    check_sources()
    bridge_test_path = REPO / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
    bridge_test = load("v39_release_query_probe_bridge_test", bridge_test_path)
    harness_module = bridge_test.load_v12_test_harness()
    source_dir = HERE / "SOURCE"
    sys.path.insert(0, str(source_dir))
    owner_module = harness_module.load("input_owner_v13_candidate", source_dir / "input_owner_v13_candidate.py")
    bridge_module = load("bridge_v2_candidate", source_dir / "bridge_v2_candidate.py")

    cases = [run_case(harness_module, owner_module, bridge_module, mode)
             for mode in ("control", "pointer_failure", "keymap_failure")]
    control, pointer, keymap = cases
    defects = []
    if control["injected_failure_observed"] or control["owner_release_measurement_rows"] != 1:
        defects.append("control-did-not-emit-one-uninjected-owner-measurement")
    if (control["bridge_release_measurement_rows"] != 1 or control["fake_physical_keys_at_boundary"]
            or control["bridge_held_at_boundary"] or control["owner_state_at_boundary"].get("owned_keycodes")):
        defects.append("control-not-neutral-with-one-release-row")
    for case in (pointer, keymap):
        if not case["injected_failure_observed"]:
            defects.append(f"{case['case']}:injection-not-observed")
        if case["fake_physical_keys_at_boundary"]:
            defects.append(f"{case['case']}:fake-key-not-up")
        if case["owner_release_record_count"] or case["owner_release_measurement_rows"]:
            defects.append(f"{case['case']}:owner-record-retained")
        if case["bridge_release_measurement_rows"]:
            defects.append(f"{case['case']}:bridge-release-row-emitted")
        if case["bridge_held_at_boundary"] != ["F8"]:
            defects.append(f"{case['case']}:bridge-held-state-did-not-remain-F8")
        if case["owner_state_at_boundary"].get("owned_keycodes") != [74]:
            defects.append(f"{case['case']}:owner-held-state-did-not-remain-keycode-74")

    outcome = {
        "schema": "map01-v39-release-query-failure-probe-a01-raw-v1",
        "invocation": 1,
        "source_commit": "1ef5611356ff217f0981843ae854ef871967e999",
        "base_main": "16c74566b64f32d7fe035c7724bcfe3865863a91",
        "cases": cases,
        "decision": "PASS_REPRODUCED_RECORD_LOSS" if not defects else "FAIL_HYPOTHESIS_NOT_REPRODUCED",
        "defects": defects,
        "scope": "deterministic fake-display owner/bridge control-flow boundary only",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps({"decision": outcome["decision"], "case_count": len(cases),
                      "release_rows": [c["bridge_release_measurement_rows"] for c in cases],
                      "defects": defects}))
    if defects:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
