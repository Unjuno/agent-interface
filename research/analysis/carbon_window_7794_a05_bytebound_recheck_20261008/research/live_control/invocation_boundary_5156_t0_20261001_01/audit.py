"""Independent raw-only oracle; intentionally does not import runner.py."""
import json
from pathlib import Path


def expected(case, limit):
    attempts = case.get("invocations", [])
    ids = [x.get("invocation_id") for x in attempts]
    errors = []
    if any(not x for x in ids):
        errors.append("invocation identity missing; legacy artifacts remain unbound")
    present = [x for x in ids if x]
    if len(present) != len(set(present)):
        errors.append("invocation identity duplicated")
    for item in attempts:
        key = item.get("invocation_id")
        if key is None:
            continue
        if any(not p.startswith("results/" + key + "/")
               for p in item.get("artifact_paths", [])):
            errors.append(f"artifact path escapes invocation namespace: {key}")
        if item.get("raw_events") and item.get("runner_started") is not True:
            errors.append(f"raw events exist before runner start: {key}")
        if item.get("audit_invoked") and item.get("runner_exit_code") != 0:
            errors.append(f"audit invoked without runner exit 0: {key}")
    count_is_bound = all(ids) and len(set(ids)) == len(ids)
    count = (sum(item.get("container_invoked") is True for item in attempts)
             if count_is_bound else None)
    if count is not None and count > limit:
        errors.append(f"allocation invocation limit exceeded: {count}>{limit}")
    if case.get("legacy_artifact_refs") and not count_is_bound:
        errors.append("legacy artifact set cannot establish invocation count")
    return {"case_id": case["case_id"],
            "decision": "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY" if errors
            else "PASS_INVOCATION_BOUNDARY_CONTRACT",
            "invocation_count": count, "errors": errors, "invocation_ids": ids}


def main(input_path, raw_path, output_path):
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in Path(raw_path).read_text(encoding="utf-8").splitlines()]
    expected_rows = [expected(case, data["max_container_invocations"])
                     for case in data["cases"]]
    errors = []
    if raw != expected_rows:
        errors.append("candidate raw differs from independent invocation-boundary reconstruction")
    controls = []
    pristine = raw[0]
    mutated = dict(pristine, decision="PASS_INVOCATION_BOUNDARY_CONTRACT")
    controls.append(mutated != expected_rows[0])
    historical = next(c for c in data["cases"] if c["case_id"] == "historical_three_attempt_collision")
    controls.append(expected(historical, data["max_container_invocations"])["decision"]
                    == "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")
    duplicate_case = next(c for c in data["cases"] if c["case_id"] == "duplicate_invocation_id")
    controls.append(expected(duplicate_case, data["max_container_invocations"])["decision"]
                    == "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")
    path_case = next(c for c in data["cases"] if c["case_id"] == "cross_invocation_artifact_path")
    controls.append(expected(path_case, data["max_container_invocations"])["decision"]
                    == "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")
    audit_case = next(c for c in data["cases"] if c["case_id"] == "audit_after_runner_failure")
    controls.append(expected(audit_case, data["max_container_invocations"])["decision"]
                    == "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")
    over_limit_case = next(c for c in data["cases"] if c["case_id"] == "two_tagged_invocations_exceed_limit")
    controls.append(expected(over_limit_case, data["max_container_invocations"])["decision"]
                    == "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")
    if not all(controls):
        errors.append("one or more frozen mutation/negative controls were accepted")
    result = {"decision": "PASS_INVOCATION_BOUNDARY_AUDIT" if not errors
              else "STOP_INVOCATION_BOUNDARY_AUDIT",
              "errors": errors, "cases": len(raw),
              "legacy_collision_decision": raw[1]["decision"],
              "mutation_controls_rejected": sum(controls),
              "mutation_controls_total": len(controls)}
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py INPUT.json RAW.jsonl AUDIT.json")
    raise SystemExit(main(*sys.argv[1:]))
