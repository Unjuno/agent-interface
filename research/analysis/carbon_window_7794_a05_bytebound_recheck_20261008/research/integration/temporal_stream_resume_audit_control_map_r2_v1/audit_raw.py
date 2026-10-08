from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


EXPECTED_NAMES = {
    "batch_incomplete", "duplicate_case_id", "candidate_suffix", "candidate_rc",
    "checkpoint_digest", "prefix_label", "comparator_status", "authority",
    "prepare_rc", "control_accept_case48", "comparator_rc",
}
MANIFEST_SHA = "1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855"
ALLOCATION = "temporal-resume-control-map-cleanup-20260928-01"


def cleanup_errors(item: dict, label: str) -> list[str]:
    if item.get("copy_exists_inside_scope") is True and item.get("copy_exists_after_scope") is False and item.get("copy_removed_after_scope") is True:
        return []
    return [f"cleanup {label}"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        raw = path.read_bytes()
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return hashlib.sha256(canonical(rows)).hexdigest()


def corruption_controls(record: dict, evidence: Path) -> list[dict]:
    probes = []
    cases = {}
    missing = copy.deepcopy(record)
    missing["mutations"].pop()
    cases["missing_mutation"] = missing
    accepted = copy.deepcopy(record)
    accepted["mutations"][0]["rejected"] = False
    cases["accepted_mutation"] = accepted
    cleanup = copy.deepcopy(record)
    cleanup["mutations"][0]["copy_removed_after_scope"] = False
    cases["false_cleanup_receipt"] = cleanup
    mapping = copy.deepcopy(record)
    target = next(x for x in mapping["mutations"] if x["name"] == "control_accept_case48")
    target["case_id"] = 45
    cases["wrong_case_identity"] = mapping
    positive = copy.deepcopy(record)
    positive["positive_control"]["rejected"] = True
    cases["positive_control_rejected"] = positive
    original = copy.deepcopy(record)
    original["original_evidence_tree_sha256_after"] = "0" * 64
    cases["original_evidence_changed"] = original
    stale = copy.deepcopy(record)
    stale["original_source_tree_sha256_after"] = "f" * 64
    cases["original_source_changed"] = stale
    unchanged = copy.deepcopy(record)
    unchanged["positive_control"]["tree_hash_unchanged_inside_scope"] = False
    cases["positive_bytes_changed"] = unchanged
    for name, candidate in cases.items():
        errors = validate(candidate, evidence)
        probes.append({"name": name, "rejected": bool(errors), "errors": errors})
    return probes


def validate(record: dict, evidence: Path) -> list[str]:
    errors: list[str] = []
    if record.get("allocation") != ALLOCATION:
        errors.append("allocation")
    baseline = record.get("baseline", {})
    try:
        base_doc = json.loads(baseline["stdout"])
    except Exception:
        base_doc = None
        errors.append("baseline stdout JSON")
    if baseline.get("returncode") != 0 or not isinstance(base_doc, dict) or base_doc.get("errors") != []:
        errors.append("baseline disposition")
    expected_base = {"rows": 54, "candidate_ok": 48, "comparator_disagreements": 40, "corruption_refusals": 6}
    if isinstance(base_doc, dict):
        for key, value in expected_base.items():
            if base_doc.get(key) != value:
                errors.append(f"baseline {key}")
        if base_doc.get("artifact_manifest_sha256") != MANIFEST_SHA:
            errors.append("baseline manifest binding")

    controls = record.get("mutations")
    if not isinstance(controls, list) or len(controls) != 11:
        errors.append("mutation denominator")
        controls = controls if isinstance(controls, list) else []
    names = [x.get("name") for x in controls if isinstance(x, dict)]
    if set(names) != EXPECTED_NAMES or len(set(names)) != 11:
        errors.append("mutation names")
    for item in controls:
        if not isinstance(item, dict):
            errors.append("mutation record type")
            continue
        name = item.get("name")
        changed_by_hash = item.get("copy_tree_sha256") != record.get("original_evidence_tree_sha256_before")
        if item.get("bytes_changed") is not True or not changed_by_hash or item.get("rejected") is not True:
            errors.append(f"mutation disposition {name}")
        errors.extend(cleanup_errors(item, name))
        verifier_rc = item.get("verifier", {}).get("returncode")
        if type(verifier_rc) is not int or verifier_rc == 0 or item.get("rejected") is not (verifier_rc != 0):
            errors.append(f"mutation verifier accepted {name}")
        if name == "control_accept_case48":
            try:
                batch5 = json.loads((evidence / "BATCH5.json").read_text(encoding="utf-8"))
                source_row = [x for x in batch5["rows"] if x.get("case_id") == 48]
                source_match = len(source_row) == 1 and source_row[0]["parsed"]["mutation"] == "foreign_epoch" and source_row[0]["parsed"]["candidate"]["parsed"]["status"] == "REFUSE_CHECKPOINT"
            except Exception:
                source_match = False
            if item.get("case_id") != 48 or item.get("identity_asserted") is not True or not source_match:
                errors.append("case 48 identity")

    positive = record.get("positive_control", {})
    if positive.get("bytes_changed") is not False or positive.get("tree_hash_unchanged_inside_scope") is not True:
        errors.append("positive unchanged bytes")
    if positive.get("tree_sha256_before") != record.get("original_evidence_tree_sha256_before") or positive.get("tree_sha256_after") != record.get("original_evidence_tree_sha256_before"):
        errors.append("positive tree identity")
    if positive.get("rejected") is not False or positive.get("verifier", {}).get("returncode") != 0:
        errors.append("positive accepted")
    errors.extend(cleanup_errors(positive, "positive"))

    if record.get("original_evidence_tree_sha256_before") != record.get("original_evidence_tree_sha256_after"):
        errors.append("original evidence changed")
    if record.get("original_source_tree_sha256_before") != record.get("original_source_tree_sha256_after"):
        errors.append("original source changed")
    manifest = evidence / "ARTIFACT_MANIFEST.json"
    if not manifest.is_file() or hashlib.sha256(manifest.read_bytes()).hexdigest() != MANIFEST_SHA:
        errors.append("input manifest commitment")
    if record.get("original_evidence_tree_sha256_after") != tree_hash(evidence):
        errors.append("evidence final tree hash")
    return errors


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--controls-output", type=Path, required=True)
    args = p.parse_args()
    record = json.loads((args.results / "CONTROL_RESULTS.json").read_text(encoding="utf-8"))
    errors = validate(record, args.evidence)
    controls = corruption_controls(record, args.evidence)
    control_errors = [x["name"] for x in controls if not x["rejected"]]
    audit = {"allocation": ALLOCATION, "decision": "PASS_CONTROL_MAP_CLEANUP_SCOPED" if not errors and not control_errors else "HOLD_RAW_AUDIT", "errors": errors, "mutation_count": len(record.get("mutations", [])), "effective_rejections": sum(x.get("bytes_changed") is True and x.get("rejected") is True for x in record.get("mutations", []) if isinstance(x, dict)), "input_manifest_sha256": hashlib.sha256((args.evidence / "ARTIFACT_MANIFEST.json").read_bytes()).hexdigest(), "source_tree_sha256": tree_hash(args.source), "evidence_tree_sha256": tree_hash(args.evidence), "corruption_controls_rejected": len(controls) - len(control_errors), "corruption_controls_total": len(controls), "corruption_control_errors": control_errors}
    args.output.write_bytes(json.dumps(audit, sort_keys=True, indent=2).encode() + b"\n")
    args.controls_output.write_bytes(json.dumps({"controls": controls}, sort_keys=True, indent=2).encode() + b"\n")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors and not control_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
