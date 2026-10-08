"""Test a per-actuation map against real producer rows and the scorer validator."""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IDENTITY = ("id", "step", "owner_id", "intent_token", "key")
V19_SHA256 = "2c5304bd246118f8124d5f7b50b81f869fb35ea3ee76887f4682748fdf95618a"
SCORER_SHA256 = "48518dd27d8271c2b9be271b0e48bd2827240a53883d07713563faa6e7e731cc"


def identity(row):
    if type(row) is not dict:
        return None
    if any(field not in row for field in IDENTITY):
        return None
    if (type(row["id"]) is not str or type(row["step"]) is not int or
            row["step"] < 0 or any(type(row[name]) is not str or not row[name].strip()
                                   for name in IDENTITY[2:])):
        return None
    measurement = row.get("physical_key_measurement")
    if type(measurement) is not dict:
        return None
    actuation_id = measurement.get("actuation_id")
    edge = measurement.get("adapter_edge")
    if (type(actuation_id) is not str or not actuation_id or type(edge) is not dict or
            edge.get("actuation_id") != actuation_id):
        return None
    if any(edge.get(field) != row[field]
           for field in ("owner_id", "intent_token", "key")):
        return None
    return tuple(row[field] for field in IDENTITY) + (actuation_id,)


class FakeBackend:
    def __init__(self, emit):
        self.emit = emit
        self.held = set()


def make_capture_backend(state):
    class CapturingBackend(FakeBackend):
        def capture(self, row):
            self.emit(row)
            event = row.get("event")
            if event not in ("input_admission", "input_release_measurement"):
                return
            state["backend"] = self
            if event == "input_admission":
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
            state["candidate"] = (down, dict(row), list(self.held))
    return CapturingBackend


def production_validator(source_path):
    raw = source_path.read_bytes()
    tree = ast.parse(raw, filename=str(source_path))
    wanted = {"_need", "_exact_ns", "_measure", "validate_measured_release_pair"}
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if {node.name for node in nodes} != wanted:
        raise AssertionError("pinned production validator functions missing")
    class MeasuredReleaseError(ValueError):
        pass

    namespace = {"MeasuredReleaseBoundary": lambda **values: values,
                 "MeasuredReleaseError": MeasuredReleaseError}
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(source_path), "exec"), namespace)
    return namespace["validate_measured_release_pair"]


def mutate_row(template, *, edge_name, key, step, start_ns, actuation_id):
    row = copy.deepcopy(template)
    row.update({"id": "program-0", "step": step, "owner_id": "owner-0",
                "intent_token": "intent-0", "key": key})
    measure = row["physical_key_measurement"]
    measure["actuation_id"] = actuation_id
    edge = measure["adapter_edge"]
    edge.update({"actuation_id": actuation_id, "owner_id": "owner-0",
                 "intent_token": "intent-0", "key": key,
                 "interval": [start_ns, start_ns + 10]})
    bracket = measure["bracket"]
    bracket.update({"owner_id": "owner-0", "intent_token": "intent-0", "key": key})
    if edge_name == "down":
        bracket["physical_down_interval"] = [start_ns, start_ns + 10]
        row["admitted_ns"] = start_ns - 20
        row["input_ack_ns"] = start_ns + 5
        measure["sync_return_ns"] = start_ns + 5
        measure["pre_sample"]["finished_ns"] = start_ns
        measure["post_sample"]["finished_ns"] = start_ns + 10
    else:
        bracket["physical_up_interval"] = [start_ns, start_ns + 10]
        measure["pre_sample"]["finished_ns"] = start_ns
        measure["release_request_ns"] = start_ns + 2
        measure["sync_return_ns"] = start_ns + 5
        measure["post_sample"]["finished_ns"] = start_ns + 10
    return row


def run_schedule(admissions, releases, down_template, up_template, validate):
    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    backend = make_capture_backend(state)(lambda _row: None)
    keys = tuple(chr(ord("A") + index) for index in range(len(admissions)))
    down_rows = {}
    for index, key in enumerate(admissions):
        row = mutate_row(down_template, edge_name="down", key=key, step=ord(key)-ord("A"),
                         start_ns=1_000_000 + index * 100,
                         actuation_id=f"act-{key}")
        down_rows[key] = row
        backend.held.add(key)
        backend.capture(row)
    up_rows = {}
    for index, key in enumerate(releases):
        row = mutate_row(up_template, edge_name="up", key=key, step=ord(key)-ord("A"),
                         start_ns=2_000_000 + index * 100,
                         actuation_id=f"act-{key}")
        up_rows[key] = row
        backend.held.remove(key)
        backend.capture(row)
    candidate = state["candidate"]
    boundary = (validate(candidate[0], candidate[1], backend_held_after=candidate[2])
                if candidate is not None else None)
    expected_key = releases[-1]
    valid = (boundary is not None and boundary["key"] == expected_key and
             boundary["actuation_id"] == f"act-{expected_key}" and
             boundary["step"] == ord(expected_key) - ord("A") and
             candidate[2] == [] and not state["ambiguous"])
    return {"admission_order": list(admissions), "release_order": list(releases),
            "candidate_down_key": None if candidate is None else candidate[0]["key"],
            "candidate_up_key": None if candidate is None else candidate[1]["key"],
            "candidate_has_event_actuation_id": (candidate is not None and
                                                   "actuation_id" in candidate[0]),
            "scorer_boundary": boundary,
            "scorer_boundary_valid": valid,
            "held_after": None if candidate is None else candidate[2]}


def mutation_checks(down_template, up_template, validate):
    down = mutate_row(down_template, edge_name="down", key="A", step=0,
                      start_ns=1_000_000, actuation_id="act-A")
    up = mutate_row(up_template, edge_name="up", key="A", step=0,
                    start_ns=2_000_000, actuation_id="act-A")
    checks = {}
    missing = copy.deepcopy(down)
    missing["physical_key_measurement"].pop("actuation_id")
    checks["missing_nested_id_has_no_map_identity"] = identity(missing) is None
    bad_edge = copy.deepcopy(down)
    bad_edge["physical_key_measurement"]["adapter_edge"]["actuation_id"] = "wrong"
    checks["conflicting_edge_id_has_no_map_identity"] = identity(bad_edge) is None
    bool_step = copy.deepcopy(down)
    bool_step["step"] = True
    checks["bool_step_has_no_map_identity"] = identity(bool_step) is None

    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    backend = make_capture_backend(state)(lambda _row: None)
    backend.held.add("A")
    backend.capture(down)
    backend.capture(copy.deepcopy(down))
    backend.held.remove("A")
    backend.capture(up)
    checks["duplicate_admission_censored"] = (state["ambiguous"] and
                                               state["candidate"] is None)

    state = {"admissions": {}, "candidate": None, "ambiguous": False}
    backend = make_capture_backend(state)(lambda _row: None)
    backend.held.add("A")
    backend.capture(down)
    backend.held.remove("A")
    wrong_up = copy.deepcopy(up)
    wrong_up["physical_key_measurement"]["actuation_id"] = "other"
    wrong_up["physical_key_measurement"]["adapter_edge"]["actuation_id"] = "other"
    backend.capture(wrong_up)
    checks["mismatched_release_censored"] = state["candidate"] is None

    tampered_up = copy.deepcopy(up)
    tampered_up["physical_key_measurement"]["adapter_edge"]["key"] = "B"
    try:
        validate(down, tampered_up, backend_held_after=[])
    except ValueError:
        checks["production_validator_rejects_edge_key_mismatch"] = True
    else:
        checks["production_validator_rejects_edge_key_mismatch"] = False
    return checks


def main():
    v19_path = ROOT / "session_map01_v19.py"
    scorer_path = ROOT / "map01_scorer_stdio_adapter_v3.py"
    raw_path = ROOT / "INPUT_EVENTS.jsonl"
    v19_hash = hashlib.sha256(v19_path.read_bytes()).hexdigest()
    scorer_hash = hashlib.sha256(scorer_path.read_bytes()).hexdigest()
    if v19_hash != V19_SHA256:
        raise SystemExit(f"V19 source hash mismatch: {v19_hash}")
    if scorer_hash != SCORER_SHA256:
        raise SystemExit(f"scorer source hash mismatch: {scorer_hash}")
    events = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    down_template = next(row for row in events if row.get("event") == "input_admission")
    up_template = next(row for row in events if row.get("event") == "input_release_measurement")
    validate = production_validator(scorer_path)
    v19_tree = ast.parse(v19_path.read_bytes(), filename=str(v19_path))
    capture = next(node for node in v19_tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == "_capture_backend")
    baseline_capture = ast.get_source_segment(v19_path.read_text(encoding="utf-8"), capture)
    assert 'state["admission"] = dict(row)' in baseline_capture
    assert "actuation_id" not in set(down_template.keys())
    cases = []
    for n in (1, 2, 3):
        keys = tuple(chr(ord("A") + index) for index in range(n))
        rows = [run_schedule(admission, release, down_template, up_template, validate)
                for admission in itertools.permutations(keys)
                for release in itertools.permutations(keys)]
        cases.append({"key_count": n, "schedule_count": len(rows),
                      "valid_scorer_boundaries": sum(row["scorer_boundary_valid"] for row in rows),
                      "invalid_or_censored": sum(not row["scorer_boundary_valid"] for row in rows),
                      "schedules": rows})
    checks = mutation_checks(down_template, up_template, validate)
    result = {
        "schema": "issue59-pr7692-release-order-map-a03-v1",
        "kind": "offline_real_schema_candidate_and_production_validator_construction",
        "source": {
            "pr": 7692, "head": "7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e",
            "v19_path": "research/doom/session_map01_v19.py", "v19_sha256": v19_hash,
            "scorer_path": "research/doom/map01_scorer_stdio_adapter_v3.py",
            "scorer_sha256": scorer_hash,
            "raw_path": "research/doom/map01_v39_perkey_measurement_consumer_a03_20261005/INPUT_EVENTS.jsonl",
            "raw_event_count": len(events),
            "raw_down_actuation_id_location": "physical_key_measurement.actuation_id",
        },
        "identity": list(IDENTITY) + ["physical_key_measurement.actuation_id"],
        "candidate_schema_compatible": True,
        "cases": cases,
        "mutation_checks": checks,
        "limits": "Candidate wrapper uses synthetic schedules cloned from the exact retained producer event shape and calls the exact scorer pair validator. It does not execute the V19 backend class, sample scorer tail, controller, OS input, GUI, model, or game.",
        "decision": "PASS_SCHEMA_AND_VALIDATOR_CANDIDATE iff all 41 schedules pass the frozen production pair validator and all malformed/mismatched identity controls fail closed."
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{key: value for key, value in case.items() if key != "schedules"}
                      for case in cases], indent=2))
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
