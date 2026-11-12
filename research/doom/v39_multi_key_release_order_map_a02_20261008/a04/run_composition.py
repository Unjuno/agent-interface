"""Connect exact V19 capture/finalization and exact V3 scorer adapter on producer-shaped schedules."""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path
import socket
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
V19_SHA = "2c5304bd246118f8124d5f7b50b81f869fb35ea3ee76887f4682748fdf95618a"
V3_SHA = "48518dd27d8271c2b9be271b0e48bd2827240a53883d07713563faa6e7e731cc"
V1_SHA = "ab0558555725644c940639bbb9577d5c37eda009edeb3f298149825981f2a481"
POLL_SHA = "32a1a4add2949c2dc65933bef0edb1903452851b44f2ee6da4a74c18dd4ade84"
PROGRESS_SHA = "3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613"
sys.path.insert(0, str(ROOT))

import map01_scorer_stdio_adapter_v3 as adapter  # noqa: E402
from run_candidate import identity, mutate_row  # noqa: E402


def exact_functions():
    raw = (ROOT / "session_map01_v19.py").read_bytes()
    tree = ast.parse(raw, filename=str(ROOT / "session_map01_v19.py"))
    selected = {name: next(node for node in tree.body
                           if isinstance(node, ast.FunctionDef) and node.name == name)
                for name in ("_capture_backend", "_run_measured_tail")}
    namespace = {"Path": Path, "json": json, "MeasuredReleaseError": adapter.MeasuredReleaseError,
                 "TAIL_DURATION_NS": 0, "TAIL_MAX_SAMPLES": 1}
    module = ast.fix_missing_locations(ast.Module(body=list(selected.values()), type_ignores=[]))
    exec(compile(module, str(ROOT / "session_map01_v19.py"), "exec"), namespace)
    return namespace["_capture_backend"], namespace["_run_measured_tail"]


class Backend:
    def __init__(self, session, out, emit, signal_readers):
        self.emit = emit
        self.held = set()

    def capture(self, row):
        self.emit(row)


def candidate_capture_backend(base_backend, state):
    """Candidate-only nested-identity variant; follows the exact V19 wrapper seam."""
    class CapturingPerKeyBackend(base_backend):
        def __init__(self, session, out, emit, signal_readers):
            def capture_emit(row):
                emit(row)
                if row.get("event") not in ("input_admission", "input_release_measurement"):
                    return
                state["backend"] = self
                if row.get("event") == "input_admission":
                    key = identity(row)
                    state["candidate"] = None
                    if key is None or key in state["admissions"]:
                        state["ambiguous"] = True
                        return
                    state["admissions"][key] = dict(row)
                    return
                key = identity(row)
                down = state["admissions"].pop(key, None) if key is not None else None
                if down is None or self.held or state["ambiguous"]:
                    state["candidate"] = None
                    return
                state["candidate"] = (dict(down), dict(row), list(self.held))

            super().__init__(session, out, capture_emit, signal_readers)
            state["backend"] = self
    return CapturingPerKeyBackend


def actual_scorer_tail(pair, tail):
    tail["samples_taken"] = 0
    left, right = socket.socketpair()
    stream = left.makefile("rb")
    try:
        polling = adapter.MainThreadScorerStdin(stream, lambda: None, lambda _row: None)
        result = polling.sample_measured_tail(
            admission_event=pair[0], release_measurement=pair[1],
            backend_held_after=pair[2], max_duration_ns=0, max_samples=1)
        tail["samples_taken"] = result["tail_samples"]
        return {"termination": result["termination"],
                "disposition": result["disposition"],
                "release_evidence_schema": result.get("release_evidence_schema"),
                "release_key": result.get("release_key"),
                "actuation_id": result.get("actuation_id"),
                "tail_samples": result["tail_samples"]}
    finally:
        stream.close()
        left.close()
        right.close()


def run_one(capture_factory, run_tail, admissions, releases, down_template, up_template):
    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    if capture_factory is exact_capture:
        state = {}
    backend = capture_factory(Backend, state)(None, None, lambda _row: None, None)
    down_rows = {}
    for ordinal, key in enumerate(admissions):
        row = mutate_row(down_template, edge_name="down", key=key, step=ord(key)-ord("A"),
                         start_ns=1_000_000 + ordinal * 100, actuation_id=f"act-{key}")
        down_rows[key] = row
        backend.held.add(key)
        backend.capture(row)
    final_pair = None
    for ordinal, key in enumerate(releases):
        row = mutate_row(up_template, edge_name="up", key=key, step=ord(key)-ord("A"),
                         start_ns=2_000_000 + ordinal * 100, actuation_id=f"act-{key}")
        backend.held.remove(key)
        backend.capture(row)
        final_pair = state.get("candidate")
    outcome = {"termination": "no_candidate", "disposition": "CENSORED", "tail_samples": 0}
    if final_pair is not None:
        tail = {"samples_taken": None}
        outcome = run_tail(final_pair, tail)
        outcome["samples_taken"] = tail["samples_taken"]
    expected = releases[-1]
    boundary = outcome.get("tail", {})
    accepted = (boundary.get("release_evidence_schema") == "map01-v39-perkey-tail-boundary-v1"
                and boundary.get("release_key") == expected
                and boundary.get("actuation_id") == f"act-{expected}"
                and outcome.get("tail_samples") == 0 and "error_type" not in outcome)
    return {"admission_order": list(admissions), "release_order": list(releases),
            "candidate_down_key": None if final_pair is None else final_pair[0]["key"],
            "candidate_up_key": None if final_pair is None else final_pair[1]["key"],
            "candidate_held_after": None if final_pair is None else final_pair[2],
            "scorer": outcome, "boundary_accepted": accepted}


def main():
    global exact_capture
    v19_path = ROOT / "session_map01_v19.py"
    v19_hash = hashlib.sha256(v19_path.read_bytes()).hexdigest()
    v3_hash = hashlib.sha256((ROOT / "map01_scorer_stdio_adapter_v3.py").read_bytes()).hexdigest()
    support_hashes = {
        "map01_scorer_stdio_adapter_v1.py": hashlib.sha256((ROOT / "map01_scorer_stdio_adapter_v1.py").read_bytes()).hexdigest(),
        "main_thread_scorer_polling_v1.py": hashlib.sha256((ROOT / "main_thread_scorer_polling_v1.py").read_bytes()).hexdigest(),
        "independent_progress_clock_v2.py": hashlib.sha256((ROOT / "independent_progress_clock_v2.py").read_bytes()).hexdigest(),
    }
    if ((v19_hash, v3_hash) != (V19_SHA, V3_SHA) or
            support_hashes != {"map01_scorer_stdio_adapter_v1.py": V1_SHA,
                               "main_thread_scorer_polling_v1.py": POLL_SHA,
                               "independent_progress_clock_v2.py": PROGRESS_SHA}):
        raise SystemExit("pinned V19/scorer/support source hash mismatch")
    down_template, up_template = [None, None]
    producer = [json.loads(line) for line in (ROOT / "INPUT_EVENTS.jsonl").read_text(encoding="utf-8").splitlines()]
    down_template = next(row for row in producer if row.get("event") == "input_admission")
    up_template = next(row for row in producer if row.get("event") == "input_release_measurement")
    assert "actuation_id" not in down_template
    exact_capture, exact_tail = exact_functions()

    def composed_tail(pair, tail_state):
        finalized = []
        with tempfile.TemporaryDirectory() as tmp:
            class Polling:
                def sample_measured_tail(self, **kwargs):
                    return actual_scorer_tail((kwargs["admission_event"],
                                               kwargs["release_measurement"],
                                               kwargs["backend_held_after"]), tail_state)

            result = exact_tail(Polling(), tmp, pair, lambda: finalized.append(True))
            saved = json.loads((Path(tmp) / "scorer-post-release-tail.json").read_text(encoding="utf-8"))
            assert result == saved
            assert finalized == [True]
            result["final_sample_called"] = True
            return result

    cases = []
    for label, factory in (("exact_v19_single_slot", exact_capture),
                           ("candidate_nested_identity_map", candidate_capture_backend)):
        rows_by_n = []
        for n in (1, 2, 3):
            keys = tuple(chr(ord("A") + i) for i in range(n))
            schedules = [run_one(factory, composed_tail, a, r,
                                 down_template, up_template)
                         for a in itertools.permutations(keys)
                         for r in itertools.permutations(keys)]
            rows_by_n.append({"key_count": n, "schedule_count": len(schedules),
                              "accepted_boundaries": sum(item["boundary_accepted"] for item in schedules),
                              "censored_or_mismatched": sum(not item["boundary_accepted"] for item in schedules),
                              "schedules": schedules})
        cases.append({"capture": label, "cases": rows_by_n})

    result = {"schema": "issue59-pr7692-release-order-map-a04-v1",
              "kind": "exact_backend_capture_and_tail_finalizer_with_exact_v3_scorer_adapter",
              "source": {"pr7692_head": "7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e",
                         "v19_sha256": v19_hash, "v3_sha256": v3_hash,
                         "support_sha256": support_hashes,
                         "producer_row_count": len(producer),
                         "producer_actuation_id_location": "physical_key_measurement.actuation_id"},
              "cases": cases,
              "limits": "Executes exact V19 capture factory and tail finalizer plus exact V3 scorer adapter over synthetic schedules cloned from retained producer rows. Tail duration is deliberately zero: this validates boundary acceptance only and collects no progress samples. No V19 main, X server, physical input, controller, GUI, model, game, or live allocation.",
              "decision": "PASS_COMPOSED_BOUNDARY_CANDIDATE iff exact single-slot yields 15/41 accepted identity boundaries and nested map yields 41/41, all with empty held-after state and zero scorer samples."}
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{"capture": case["capture"], "counts": [
        {k: v for k, v in c.items() if k != "schedules"} for c in case["cases"]]} for case in cases], indent=2))


if __name__ == "__main__":
    main()
