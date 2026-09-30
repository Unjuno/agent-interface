"""Independent raw-only audit for the #5518 finite conformance spike."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "reference-direct": "CONFORMANT",
    "reference-hidden-batch-retry": "CONFORMANT",
    "forbidden-target-switch": "NONCONFORMANT",
    "forbidden-stale-admission": "NONCONFORMANT",
    "forbidden-unauthorized-admission": "NONCONFORMANT",
    "forbidden-semantic-false-success": "NONCONFORMANT",
    "delayed-unknown-and-explicit-quiescence": "CONFORMANT",
    "missing-output-is-not-quiescence": "UNKNOWN",
}


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def evaluate_independently(spec, trace):
    """Auditor-owned transition walk, intentionally not importing contract.py."""
    state = spec["initial"]
    for position, exchange in enumerate(trace, 1):
        selected = [t for t in spec["transitions"]
                    if t["from"] == state and _canon(t["input"]) == _canon(exchange["input"])]
        if len(selected) != 1:
            why = "INPUT_NOT_SPECIFIED" if not selected else "AMBIGUOUS_SPEC_TRANSITION"
            return {"status": "NONCONFORMANT", "reason": why,
                    "counterexample": {"prefix_length": position, "index": position,
                                       "state": state, "input": exchange["input"],
                                       "observed_outputs": exchange.get("outputs", []),
                                       "allowed_outputs": [], "reason": why}}
        transition = selected[0]
        actual = exchange.get("outputs")
        if not isinstance(actual, list) or len(actual) == 0:
            return {"status": "UNKNOWN", "reason": "MISSING_OUTPUT_NOT_QUIESCENCE",
                    "prefix_length": position, "state": state, "input": exchange["input"]}
        permitted = transition["allowed_outputs"]
        if len(actual) != 1 or all(_canon(actual[0]) != _canon(item) for item in permitted):
            return {"status": "NONCONFORMANT", "reason": "OUTPUT_NOT_ALLOWED",
                    "counterexample": {"prefix_length": position, "index": position,
                                       "state": state, "input": exchange["input"],
                                       "observed_outputs": actual,
                                       "allowed_outputs": permitted,
                                       "reason": "OUTPUT_NOT_ALLOWED"}}
        state = transition["to"]
    return {"status": "CONFORMANT", "reason": "ALL_PREFIXES_ALLOWED",
            "prefix_length": len(trace), "final_state": state}


def verify_source_manifest(freeze, observed_hashes, root=ROOT):
    errors = []
    expected = freeze.get("frozen_sources", {})
    if set(observed_hashes) != set(expected):
        errors.append("source_inventory")
    for relative, expected_hash in expected.items():
        path = Path(root) / relative
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            errors.append("source_missing:" + relative)
            continue
        if actual != expected_hash or observed_hashes.get(relative) != actual:
            errors.append("source_hash:" + relative)
    return errors


def _check(raw, spec, corpus):
    errors = []
    rows = raw.get("results")
    if not isinstance(rows, list):
        return ["results_not_list"]
    indexed = {row.get("case_id"): row for row in rows if isinstance(row, dict)}
    expected_ids = [case["case_id"] for case in corpus["cases"]]
    if len(indexed) != len(rows) or set(indexed) != set(expected_ids):
        errors.append("case_inventory")
    for case in corpus["cases"]:
        row = indexed.get(case["case_id"])
        if row is None:
            continue
        rebuilt = evaluate_independently(spec, case["trace"])
        if row.get("implementation") != case["implementation"] or row.get("result") != rebuilt:
            errors.append("raw_row:" + case["case_id"])
        if rebuilt["status"] != EXPECTED[case["case_id"]]:
            errors.append("decision:" + case["case_id"])

    by_id = {case["case_id"]: case for case in corpus["cases"]}
    direct = by_id["reference-direct"]["trace"]
    hidden = by_id["reference-hidden-batch-retry"]["trace"]
    expected_baseline = {
        "compared": ["reference-direct", "reference-hidden-batch-retry"],
        "exact_raw_trace_equal": direct == hidden,
        "agent_visible_io_equal": [
            {"input": x["input"], "outputs": x["outputs"]} for x in direct
        ] == [
            {"input": x["input"], "outputs": x["outputs"]} for x in hidden
        ],
    }
    if raw.get("baseline") != expected_baseline:
        errors.append("baseline_comparison")
    if raw.get("frozen_sources_verified") is not True:
        errors.append("source_freeze_not_verified")
    return errors


def audit_document(spec, corpus, raw, freeze, root=ROOT):
    errors = _check(raw, spec, corpus)
    errors.extend(verify_source_manifest(freeze, raw.get("source_sha256", {}), root=root))
    if raw.get("allocation_id") != freeze.get("allocation_id"):
        errors.append("allocation_id")
    if raw.get("source_base_main_sha") != freeze.get("base_main_sha"):
        errors.append("base_main_sha")
    expected_freeze_sha = hashlib.sha256((Path(root) / "FREEZE.json").read_bytes()).hexdigest()
    if raw.get("freeze_sha256") != expected_freeze_sha:
        errors.append("freeze_sha256")
    commit = raw.get("source_commit_sha", "")
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        errors.append("source_commit_sha")
    controls = []

    forged = json.loads(json.dumps(raw))
    for row in forged["results"]:
        if row["case_id"] == "forbidden-target-switch":
            row["result"]["status"] = "CONFORMANT"
            break
    controls.append(("forged_pass", bool(_check(forged, spec, corpus))))

    omitted = json.loads(json.dumps(raw))
    omitted["results"].pop()
    controls.append(("omitted_row", bool(_check(omitted, spec, corpus))))

    silenced_as_quiescent = json.loads(json.dumps(raw))
    for row in silenced_as_quiescent["results"]:
        if row["case_id"] == "missing-output-is-not-quiescence":
            row["result"]["status"] = "CONFORMANT"
            break
    controls.append(("silence_promoted_to_success", bool(_check(silenced_as_quiescent, spec, corpus))))

    baseline_forgery = json.loads(json.dumps(raw))
    baseline_forgery["baseline"]["exact_raw_trace_equal"] = True
    controls.append(("forged_baseline", bool(_check(baseline_forgery, spec, corpus))))

    counts = {}
    for row in raw.get("results", []):
        status = row.get("result", {}).get("status", "MALFORMED")
        counts[status] = counts.get(status, 0) + 1
    controls_ok = all(passed for _, passed in controls)
    disposition = "PASS_T0_IOCO_SYNTHETIC_CONTRACT" if not errors and controls_ok else "FAIL_T0_AUDIT"
    return {
        "schema": "agent-interface-ioco-audit-t0-v1",
        "disposition": disposition,
        "errors": errors,
        "case_count": len(raw.get("results", [])),
        "status_counts": counts,
        "mutation_controls": {name: passed for name, passed in controls},
        "all_mutations_rejected": controls_ok,
        "limits": [
            "Finite hand-authored synthetic traces only; not a full formal ioco implementation.",
            "One output event per input is enforced by this T0 profile.",
            "No GUI, runtime adapter, model, timing distribution, task-effect, or cross-platform behavior was tested.",
            "Conformance is only relative to this explicit input/output alphabet and quiescence policy.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    spec = json.loads((root / "spec.json").read_text(encoding="utf-8"))
    corpus = json.loads((root / "cases.json").read_text(encoding="utf-8"))
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    result = audit_document(spec, corpus, raw, freeze, root=root)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")
    if result["disposition"] != "PASS_T0_IOCO_SYNTHETIC_CONTRACT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
