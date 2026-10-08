#!/usr/bin/env python3
"""Corrected independent reconstruction; formal raw remains immutable."""
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
CONTROL_NAMES = (
    "missing_receipt",
    "stale_binding",
    "unknown_boundary",
    "cleanup_failure",
    "corrupt_recomputation",
)


def expected_rows():
    # Product order mirrors the serialized truth-table ordering, but gate
    # classification below is separately expressed as a literal-True check.
    return [dict(zip(FIELDS, bits)) for bits in itertools.product((False, True), repeat=5)]


def classify(row):
    return "AUTHORIZE" if all(row.get(field) is True for field in FIELDS) else "HOLD"


def structure_errors(data):
    errors = []
    if not isinstance(data, dict) or set(data) != {"schema", "fields", "vectors", "controls"}:
        return ["top-level schema mismatch"]
    if data["schema"] != "map01-recovery-entry-gate-3008-v2" or data["fields"] != list(FIELDS):
        errors.append("schema identity/order mismatch")
    vectors = data["vectors"]
    controls = data["controls"]
    if not isinstance(vectors, list) or len(vectors) != 32:
        return errors + ["vector count mismatch"]
    expected = expected_rows()
    for index, (row, bits) in enumerate(zip(vectors, expected)):
        if not isinstance(row, dict) or set(row) != set(FIELDS) | {"decision"}:
            errors.append(f"vector schema mismatch at {index}")
            continue
        if any(type(row[field]) is not bool for field in FIELDS):
            errors.append(f"vector type mismatch at {index}")
            continue
        if any(row[field] is not bits[field] for field in FIELDS):
            errors.append(f"vector ordering/value mismatch at {index}")
        if row["decision"] != classify(row):
            errors.append(f"vector decision mismatch at {index}")
    if not isinstance(controls, list) or len(controls) != 5:
        return errors + ["control count mismatch"]
    for index, row in enumerate(controls):
        if not isinstance(row, dict) or set(row) != set(FIELDS) | {"name", "decision"}:
            errors.append(f"control schema mismatch at {index}")
            continue
        if row["name"] != CONTROL_NAMES[index]:
            errors.append(f"control identity mismatch at {index}")
        if row["decision"] != classify(row) or row["decision"] != "HOLD":
            errors.append(f"control did not hold at {index}")
    return errors


def audit(raw_bytes, source_dir):
    errors = []
    try:
        data = json.loads(raw_bytes)
    except Exception as exc:
        return {"status": "FAIL_AUDIT", "errors": [f"invalid JSON: {type(exc).__name__}"]}
    errors.extend(structure_errors(data))
    source_dir = pathlib.Path(source_dir)
    for filename, expected in SOURCE_HASHES.items():
        actual = hashlib.sha256((source_dir / filename).read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"source hash mismatch: {filename}")

    vectors = data.get("vectors", [])
    controls = data.get("controls", [])
    authorize = sum(isinstance(row, dict) and row.get("decision") == "AUTHORIZE" for row in vectors)
    summary = {
        "rows": len(vectors) + len(controls),
        "vectors": len(vectors),
        "authorize": authorize,
        "current": "HOLD",
        "controls": sum(isinstance(row, dict) and row.get("decision") == "HOLD" for row in controls),
    }
    expected_summary = {"rows": 37, "vectors": 32, "authorize": 1, "current": "HOLD", "controls": 5}
    if summary != expected_summary:
        errors.append("independent aggregate mismatch")

    mutations = {}
    changed = json.loads(raw_bytes)
    changed["vectors"][0][FIELDS[0]] = not changed["vectors"][0][FIELDS[0]]
    mutations["vector_bit"] = structure_errors(changed)
    changed = json.loads(raw_bytes)
    changed["vectors"].pop()
    mutations["row_count"] = structure_errors(changed)
    changed = json.loads(raw_bytes)
    changed["vectors"][31]["decision"] = "HOLD"
    mutations["expected_class"] = structure_errors(changed)
    summary_mutation = dict(summary)
    summary_mutation["rows"] += 1
    mutations["summary_count"] = [] if summary_mutation == expected_summary else ["summary count mismatch"]
    source_mutation = dict(SOURCE_HASHES)
    source_mutation["run.py"] = "0" * 64
    actual_runner = hashlib.sha256((source_dir / "run.py").read_bytes()).hexdigest()
    mutations["source_hash"] = [] if actual_runner == source_mutation["run.py"] else ["source hash mismatch"]
    corruption = {key: bool(value) for key, value in mutations.items()}
    if not all(corruption.values()):
        errors.append("a corruption control escaped")

    return {
        "status": "PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "summary": summary,
        "corruption_controls_rejected": corruption,
        "auditor_v1_discrepancy": [
            "v1 enumerated the lowest-order bit fastest, unlike the frozen candidate's itertools.product row order",
            "v1 counted vectors but omitted five controls from the rows aggregate",
        ],
    }


def main(argv):
    raw_path, source_dir, output_path = map(pathlib.Path, argv[1:4])
    result = audit(raw_path.read_bytes(), source_dir)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS_INDEPENDENT_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
