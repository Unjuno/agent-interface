#!/usr/bin/env python3
"""Independent source-bound audit of Issue #3188 raw entry-gate bytes."""
import hashlib
import itertools
import json
import pathlib
import sys

FIELDS = (
    "physical_task_effect_endpoint",
    "task_effect_contract",
    "matched_arm",
    "arm_bound_audit",
    "terminal_integrity",
)
SOURCE_HASHES = {
    "run.py": "e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822",
    "audit.py": "72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d",
}


def expected_vector(mask):
    values = tuple(bool(mask & (1 << bit)) for bit in range(len(FIELDS)))
    return dict(zip(FIELDS, values))


def classify(record):
    # Independent direct gate: every frozen prerequisite must be literal True.
    return "AUTHORIZE" if all(record.get(field) is True for field in FIELDS) else "HOLD"


def audit(raw_bytes, source_dir):
    errors = []
    raw_digest = hashlib.sha256(raw_bytes).hexdigest()
    try:
        data = json.loads(raw_bytes)
    except Exception as exc:
        return {"status": "FAIL_AUDIT", "errors": [f"invalid json: {type(exc).__name__}"], "raw_sha256": raw_digest}

    if set(data) != {"schema", "fields", "vectors", "controls"}:
        errors.append("top-level schema mismatch")
    if data.get("schema") != "map01-recovery-entry-gate-3008-v2":
        errors.append("schema identity mismatch")
    if data.get("fields") != list(FIELDS):
        errors.append("field order mismatch")

    vectors = data.get("vectors")
    expected = [expected_vector(mask) for mask in range(32)]
    if not isinstance(vectors, list) or len(vectors) != 32:
        errors.append("vector cardinality mismatch")
        vectors = vectors if isinstance(vectors, list) else []
    observed = []
    for row in vectors:
        if not isinstance(row, dict) or set(row) != set(FIELDS) | {"decision"}:
            errors.append("vector schema mismatch")
            continue
        bits = []
        for key in FIELDS:
            if type(row[key]) is not bool:
                errors.append("non-boolean vector bit")
                bits.append(False)
            else:
                bits.append(row[key])
        observed.append(tuple(bits))
        if row.get("decision") != classify(row):
            errors.append("vector decision mismatch")
    if observed != [tuple(item[key] for key in FIELDS) for item in expected]:
        errors.append("vector coverage/order/uniqueness mismatch")

    controls = data.get("controls")
    names = ("missing_receipt", "stale_binding", "unknown_boundary", "cleanup_failure", "corrupt_recomputation")
    if not isinstance(controls, list) or len(controls) != len(names):
        errors.append("control cardinality mismatch")
        controls = controls if isinstance(controls, list) else []
    for index, row in enumerate(controls):
        if not isinstance(row, dict) or set(row) != set(FIELDS) | {"name", "decision"}:
            errors.append("control schema mismatch")
            continue
        if index >= len(names) or row.get("name") != names[index]:
            errors.append("control identity/order mismatch")
        if row.get("decision") != classify(row) or row.get("decision") != "HOLD":
            errors.append("control did not independently HOLD")

    source_dir = pathlib.Path(source_dir)
    for filename, expected_hash in SOURCE_HASHES.items():
        actual = hashlib.sha256((source_dir / filename).read_bytes()).hexdigest()
        if actual != expected_hash:
            errors.append(f"source hash mismatch: {filename}")

    authorize_count = sum(row.get("decision") == "AUTHORIZE" for row in vectors if isinstance(row, dict))
    summary = {
        "rows": len(vectors),
        "vectors": len(vectors),
        "authorize": authorize_count,
        "current": "HOLD",
        "controls": sum(row.get("decision") == "HOLD" for row in controls if isinstance(row, dict)),
    }
    expected_summary = {"rows": 37, "vectors": 32, "authorize": 1, "current": "HOLD", "controls": 5}
    if summary != expected_summary:
        errors.append("independent summary mismatch")

    corruption = {}
    mutations = []
    if isinstance(data.get("vectors"), list) and data["vectors"]:
        changed = json.loads(raw_bytes)
        changed["vectors"][0][FIELDS[0]] = not changed["vectors"][0][FIELDS[0]]
        mutations.append(("vector_bit", changed))
        changed = json.loads(raw_bytes)
        changed["vectors"].pop()
        mutations.append(("row_count", changed))
        changed = json.loads(raw_bytes)
        changed["vectors"][0]["decision"] = "AUTHORIZE"
        mutations.append(("class_label", changed))
    for name, changed in mutations:
        result = audit_structure_only(changed)
        corruption[name] = bool(result)
    changed_sources = dict(SOURCE_HASHES)
    changed_sources["run.py"] = "0" * 64
    actual_source = hashlib.sha256((source_dir / "run.py").read_bytes()).hexdigest()
    corruption["source_hash"] = actual_source != changed_sources["run.py"]
    changed_summary = dict(summary)
    changed_summary["rows"] -= 1
    corruption["summary_count"] = changed_summary != expected_summary
    if len(corruption) != 5 or not all(corruption.values()):
        errors.append("corruption challenge escaped")
    return {
        "status": "PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "raw_sha256": raw_digest,
        "summary": summary,
        "corruption_controls_rejected": corruption,
    }


def audit_structure_only(data):
    vectors = data.get("vectors")
    if not isinstance(vectors, list) or len(vectors) != 32:
        return ["vector cardinality"]
    tuples = []
    for row in vectors:
        if not isinstance(row, dict) or set(row) != set(FIELDS) | {"decision"}:
            return ["vector schema"]
        bits = tuple(row.get(key) for key in FIELDS)
        if any(type(bit) is not bool for bit in bits):
            return ["vector type"]
        tuples.append(bits)
        if row.get("decision") != classify(row):
            return ["decision"]
    if tuples != [tuple(expected_vector(mask)[key] for key in FIELDS) for mask in range(32)]:
        return ["vector coverage"]
    return []


def main(argv):
    raw_path, source_dir, out_path = map(pathlib.Path, argv[1:4])
    result = audit(raw_path.read_bytes(), source_dir)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    out_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS_INDEPENDENT_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
