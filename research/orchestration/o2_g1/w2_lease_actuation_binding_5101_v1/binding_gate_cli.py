"""Additive CLI wrapper for the experimental W2 lease-actuation binding gate."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from binding_candidate import evaluate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_binding(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected CASE_ID=ACTUATION_ID or CASE_ID=MISSING")
    case_id, actuation_id = value.split("=", 1)
    if not case_id or not actuation_id:
        raise argparse.ArgumentTypeError("case and binding value must be non-empty")
    return case_id, actuation_id


def apply_open_bindings(document, mutations):
    by_case = {}
    for case_id, value in mutations:
        if case_id in by_case:
            raise ValueError(f"duplicate mutation for {case_id}")
        by_case[case_id] = value
    found = set()
    for case in document["cases"]:
        case_id = case["case_id"]
        if case_id not in by_case:
            continue
        opens = [e for e in case["events"] if e.get("event_type") == "LEASE_OPEN"]
        if len(opens) != 1:
            raise ValueError(f"expected one LEASE_OPEN in {case_id}; found {len(opens)}")
        lineage = opens[0].setdefault("lineage", {})
        value = by_case[case_id]
        if value == "MISSING":
            lineage.pop("actuation_id", None)
        else:
            lineage["actuation_id"] = value
        found.add(case_id)
    absent = set(by_case) - found
    if absent:
        raise ValueError(f"unknown case ids: {sorted(absent)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--open-binding", action="append", default=[], type=parse_binding,
                        help="version a copy by setting one LEASE_OPEN binding; repeat as CASE=ID")
    args = parser.parse_args()

    source_bytes = args.traces.read_bytes()
    document = copy.deepcopy(json.loads(source_bytes))
    apply_open_bindings(document, args.open_binding)
    effective_bytes = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    out = args.output_dir
    if out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    out.mkdir(parents=True)
    effective_path = out / "effective-traces.json"
    report_path = out / "candidate-report.json"
    effective_path.write_bytes(effective_bytes)

    cases = []
    for case in document["cases"]:
        decisions = evaluate(case["events"])
        cases.append({
            "case_id": case["case_id"],
            "baseline_disposition": case.get("expected", {}).get("disposition"),
            "binding_decisions": decisions,
        })
    candidate_bytes = Path(__file__).read_bytes()
    report = {
        "schema": "w2-lease-actuation-candidate-cli-v1",
        "input_sha256": digest(source_bytes),
        "effective_trace_sha256": digest(effective_bytes),
        "candidate_sha256": digest(candidate_bytes),
        "mutations": [{"case_id": c, "lease_open_actuation_id": a} for c, a in args.open_binding],
        "case_count": len(cases),
        "cases": cases,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_report": str(report_path), "effective_trace_sha256": report["effective_trace_sha256"], "case_count": len(cases)}))


if __name__ == "__main__":
    main()
