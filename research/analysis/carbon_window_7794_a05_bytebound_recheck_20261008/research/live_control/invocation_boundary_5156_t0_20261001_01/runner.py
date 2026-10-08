"""Candidate: classify invocation identity and allocation-level attempt bounds."""
import json
from pathlib import Path


def classify(case, max_invocations):
    invocations = case.get("invocations", [])
    errors = []
    ids = [item.get("invocation_id") for item in invocations]
    if any(not value for value in ids):
        errors.append("invocation identity missing; legacy artifacts remain unbound")
    if len([value for value in ids if value]) != len(set(value for value in ids if value)):
        errors.append("invocation identity duplicated")
    for item in invocations:
        invocation_id = item.get("invocation_id")
        if not invocation_id:
            continue
        prefix = f"results/{invocation_id}/"
        if any(not path.startswith(prefix) for path in item.get("artifact_paths", [])):
            errors.append(f"artifact path escapes invocation namespace: {invocation_id}")
        events = item.get("raw_events", [])
        if events and not item.get("runner_started"):
            errors.append(f"raw events exist before runner start: {invocation_id}")
        if item.get("audit_invoked") and item.get("runner_exit_code") != 0:
            errors.append(f"audit invoked without runner exit 0: {invocation_id}")
    count_is_bound = all(ids) and len(set(ids)) == len(ids)
    attempt_count = (sum(bool(item.get("container_invoked")) for item in invocations)
                     if count_is_bound else None)
    if attempt_count is not None and attempt_count > max_invocations:
        errors.append(f"allocation invocation limit exceeded: {attempt_count}>{max_invocations}")
    if case.get("legacy_artifact_refs") and not count_is_bound:
        errors.append("legacy artifact set cannot establish invocation count")
    if errors:
        decision = "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY"
    else:
        decision = "PASS_INVOCATION_BOUNDARY_CONTRACT"
    return {"case_id": case["case_id"], "decision": decision,
            "invocation_count": attempt_count, "errors": errors,
            "invocation_ids": ids}


def main(input_path, output_path):
    source = json.loads(Path(input_path).read_text(encoding="utf-8"))
    rows = [classify(case, source["max_container_invocations"])
            for case in source["cases"]]
    Path(output_path).write_text("".join(json.dumps(row, sort_keys=True) + "\n"
                                                 for row in rows), encoding="utf-8")
    print(json.dumps({"cases": len(rows), "rows": len(rows), "exit_code": 0}))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: runner.py INPUT.json RAW.jsonl")
    main(sys.argv[1], sys.argv[2])
