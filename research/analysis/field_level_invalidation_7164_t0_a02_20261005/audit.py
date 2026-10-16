#!/usr/bin/env python3
"""Independent oracle and mutation-tested auditor for #7164 T0."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

UNKNOWN = {"status": "UNKNOWN", "value": None}
METHODS = ("whole_record", "independent_field", "dependency_aware")
EXPECTED_EVENT_RECOMPUTES = {
    "parent_surface_replacement": {"whole_record": 5, "independent_field": 0, "dependency_aware": 3},
    "transitive_layout_and_sibling": {"whole_record": 5, "independent_field": 0, "dependency_aware": 2},
    "mode_dependent_branch": {"whole_record": 5, "independent_field": 0, "dependency_aware": 1},
    "delayed_older_update": {"whole_record": 5, "independent_field": 0, "dependency_aware": 2},
    "object_id_reuse_new_generation": {"whole_record": 0, "independent_field": 0, "dependency_aware": 0},
    "missing_source_and_dependency_coverage": {"whole_record": 0, "independent_field": 0, "dependency_aware": 0},
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def current(value):
    return {"status": "CURRENT", "value": value}


def get(fields, name):
    v = fields.get(name, UNKNOWN)
    return v.get("value") if v.get("status") == "CURRENT" else None


def fresh(fields, complete):
    """Fresh-input semantics, deliberately separate from candidate reducer."""
    if not complete:
        return {n: copy.deepcopy(UNKNOWN) for n in
                ("screen_position", "contextual_role", "recovery_anchor", "enabled", "object_caption")}
    o, p = get(fields, "surface_origin"), get(fields, "local_position")
    role, scope = get(fields, "surface_role"), get(fields, "task_scope")
    surface, mode = get(fields, "surface_id"), get(fields, "ui_mode")
    label, text = get(fields, "accessible_name"), get(fields, "text_value")
    ep = get(fields, "enabled_edit") if mode == "edit" else get(fields, "enabled_preview") if mode == "preview" else None
    pos = [o[0] + p[0], o[1] + p[1]] if o is not None and p is not None else None
    values = {
        "screen_position": pos,
        "contextual_role": role + ":" + scope if role is not None and scope is not None else None,
        "recovery_anchor": surface + "@" + str(pos[0]) + "," + str(pos[1]) + "#" + scope if pos is not None and surface is not None and scope is not None else None,
        "enabled": ep,
        "object_caption": label + "|" + text if label is not None and text is not None else None,
    }
    return {k: current(v) if v is not None else copy.deepcopy(UNKNOWN) for k, v in values.items()}


def oracle(case):
    base = case["base"]
    key, epoch, complete = copy.deepcopy(base["key"]), base["epoch"], base["coverage_complete"]
    fields = {k: current(v) for k, v in base["fields"].items()}
    fields.update(fresh(fields, complete))
    accepted, rejected = [], []
    for ev in case["events"]:
        ek = ev["key"]
        if ek != key:
            old, new = key.get("generation"), ek.get("generation")
            if (ek.get("object_id") == key.get("object_id") and isinstance(old, int)
                    and isinstance(new, int) and new > old and "snapshot" in ev):
                key, epoch = copy.deepcopy(ek), ev["epoch"]
                snap = ev["snapshot"]
                complete = snap["coverage_complete"]
                fields = {k: copy.deepcopy(UNKNOWN) for k in (
                    "object_token", "accessible_name", "surface_id", "surface_role",
                    "surface_origin", "local_position", "ui_mode", "enabled_edit",
                    "enabled_preview", "task_scope", "text_value")}
                fields.update({k: current(v) for k, v in snap["fields"].items()})
                fields.update(fresh(fields, complete))
                accepted.append({"event_id": ev["event_id"], "status": "NEW_GENERATION_RESET"})
            else:
                rejected.append({"event_id": ev["event_id"], "status": "REJECTED_WRONG_GENERATION"})
            continue
        if ev["epoch"] <= epoch:
            rejected.append({"event_id": ev["event_id"], "status": "REJECTED_STALE_EPOCH"})
            continue
        for n, v in ev.get("updates", {}).items():
            fields[n] = current(v)
        for n in ev.get("invalidate_fields", []):
            fields.pop(n, None)
        epoch, complete = ev["epoch"], ev["coverage_complete"]
        fields.update(fresh(fields, complete))
        accepted.append({"event_id": ev["event_id"], "status": "ACCEPTED"})
    return {"key": key, "epoch": epoch, "coverage_complete": complete,
            "accepted_events": accepted, "rejected_events": rejected, "fields": fields}


def check_one(case, method, result):
    expected = oracle(case)
    errors = []
    for key in ("key", "epoch", "coverage_complete", "accepted_events", "rejected_events"):
        if result.get(key) != expected[key]:
            errors.append("receipt/identity mismatch: " + key)
    if result.get("case_id") != case["case_id"] or result.get("method") != method:
        errors.append("case/method identity mismatch")
    for name, want in expected["fields"].items():
        got = result.get("fields", {}).get(name)
        if got != want:
            errors.append("field mismatch: " + name)
    # A missing derived field is also a failure; unsupported data must be UNKNOWN.
    for name in ("screen_position", "contextual_role", "recovery_anchor", "enabled", "object_caption"):
        if name not in result.get("fields", {}):
            errors.append("missing derived field: " + name)
    if result.get("event_recomputed_derived") != EXPECTED_EVENT_RECOMPUTES[case["case_id"]][method]:
        errors.append("derived recomputation count mismatch")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--freeze", required=True)
    p.add_argument("--candidate-output", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    paths = {name: Path(__file__).parent / name for name in json.loads(Path(a.freeze).read_text())["sha256"]}
    freeze = json.loads(Path(a.freeze).read_text())
    actual = {name: digest(path) for name, path in paths.items()}
    for name, value in actual.items():
        if freeze["sha256"].get(name) != value:
            raise SystemExit("FREEZE_HASH_MISMATCH:" + name)
    if digest(a.input) != actual["INPUT.json"] or digest(a.schema) != actual["SCHEMA.json"]:
        raise SystemExit("ARGUMENT_HASH_MISMATCH")
    fixture = json.loads(Path(a.input).read_text())
    candidate = json.loads(Path(a.candidate_output).read_text())
    by_key = {(r["case_id"], r["method"]): r for r in candidate["results"]}
    audit_errors = []
    expected_counterexamples = []
    classifications = {m: {"cases": 0, "oracle_matches": 0, "stale_or_wrong": 0} for m in METHODS}
    for case in fixture["cases"]:
        for method in METHODS:
            key = (case["case_id"], method)
            result = by_key.get(key)
            if result is None:
                audit_errors.append({"case_id": key[0], "method": method, "errors": ["missing result"]})
                continue
            errs = check_one(case, method, result)
            c = classifications[method]
            c["cases"] += 1
            c["oracle_matches"] += int(not errs)
            c["stale_or_wrong"] += int(bool(errs))
            if errs and method == "independent_field":
                # This comparator is intentionally defective. Its stale-derived
                # field mismatches are the planned negative-control evidence,
                # while receipt/identity and metric errors remain gate failures.
                expected = [e for e in errs if e.startswith("field mismatch:")]
                unexpected = [e for e in errs if not e.startswith("field mismatch:")]
                if expected:
                    expected_counterexamples.append({"case_id": key[0], "method": method, "errors": expected})
                if unexpected:
                    audit_errors.append({"case_id": key[0], "method": method, "errors": unexpected})
            elif errs:
                audit_errors.append({"case_id": key[0], "method": method, "errors": errs})
    expected_keys = {(c["case_id"], m) for c in fixture["cases"] for m in METHODS}
    if set(by_key) != expected_keys:
        audit_errors.append({"errors": ["result cardinality or duplicate identity mismatch"]})

    # Auditor self-check: every adversarial mutation below must be rejected.
    controls = {}
    targets = {
        "corrupt_derived_anchor": ("transitive_layout_and_sibling", "whole_record", "recovery_anchor", current("forged")),
        "wrong_dynamic_enabled_branch": ("mode_dependent_branch", "whole_record", "enabled", current(True)),
        "current_claim_missing_support": ("missing_source_and_dependency_coverage", "whole_record", "screen_position", current([1, 2])),
    }
    for label, (cid, method, field, bad) in targets.items():
        case = next(c for c in fixture["cases"] if c["case_id"] == cid)
        original = copy.deepcopy(by_key[(cid, method)])
        mutant = copy.deepcopy(original)
        mutant["fields"][field] = bad
        controls[label] = bool(check_one(case, method, mutant))
    for label, cid, method, event_id in (
        ("accept_old_epoch", "delayed_older_update", "whole_record", "late-2"),
        ("accept_previous_generation", "object_id_reuse_new_generation", "whole_record", "late-old-generation-6"),
    ):
        case = next(c for c in fixture["cases"] if c["case_id"] == cid)
        mutant = copy.deepcopy(by_key[(cid, method)])
        mutant["rejected_events"] = [x for x in mutant["rejected_events"] if x["event_id"] != event_id]
        mutant["accepted_events"].append({"event_id": event_id, "status": "ACCEPTED"})
        controls[label] = bool(check_one(case, method, mutant))

    independent_counterexamples = expected_counterexamples
    whole_ok = classifications["whole_record"]["stale_or_wrong"] == 0
    dep_ok = classifications["dependency_aware"]["stale_or_wrong"] == 0
    independent_fails = bool(independent_counterexamples)
    recompute_gain = any(
        EXPECTED_EVENT_RECOMPUTES[cid]["dependency_aware"] < EXPECTED_EVENT_RECOMPUTES[cid]["whole_record"]
        for cid in EXPECTED_EVENT_RECOMPUTES
        if cid not in ("object_id_reuse_new_generation", "missing_source_and_dependency_coverage")
    )
    output = {
        "format": "field-invalidation-independent-audit-v1",
        "freeze_id": freeze["freeze_id"], "input_sha256": actual["INPUT.json"],
        "schema_sha256": digest(a.schema), "audit_sha256": actual["audit.py"],
        "result_count": len(candidate.get("results", [])), "classifications": classifications,
        "hypothesis": {"D_whole_record_matches_fresh_oracle": whole_ok,
                       "D_dependency_aware_matches_fresh_oracle": dep_ok,
                       "H_independent_field_has_stale_counterexample": independent_fails,
                       "H_dependency_aware_recomputes_less_than_whole_record": recompute_gain},
        "mutation_controls_all_rejected": bool(controls) and all(controls.values()),
        "mutation_controls": controls, "expected_counterexamples": expected_counterexamples,
        "errors": audit_errors,
        "gate": "PASS_METHOD_SCOPED" if whole_ok and dep_ok and independent_fails and recompute_gain and all(controls.values()) and not audit_errors else "FAIL",
        "scope": "finite synthetic T0 only; no live UI, model, user-data, latency, or task-effect evidence",
    }
    Path(a.output).write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")
    print(output["gate"])
    if output["gate"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
