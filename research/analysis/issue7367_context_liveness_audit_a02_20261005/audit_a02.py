#!/usr/bin/env python3
"""Audit-only v2 revalidation of retained #7367 A01 bytes; no candidate run."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def policy_visible_bytes(records, selected_ids):
    selected = set(selected_ids)
    rows = [r for r in records if r["id"] in selected]
    return len(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())


def binding_errors(workload_bytes, raw_bytes, prerun, frozen_raw_sha):
    """Bind both present inputs to the already frozen A01 source/artifact digests."""
    errors = []
    expected_workload = prerun["source_sha256"]["workload.json"]
    actual_workload = sha(workload_bytes)
    if actual_workload != expected_workload:
        errors.append("workload_bytes_match_prerun")
    try:
        raw = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return errors + ["raw_json_parseable"]
    if raw.get("workload_sha256") != expected_workload:
        errors.append("raw_declares_prerun_workload_sha256")
    if raw.get("workload_sha256") != actual_workload:
        errors.append("raw_declared_workload_matches_bytes")
    if sha(raw_bytes) != frozen_raw_sha:
        errors.append("raw_artifact_matches_frozen_sha256")
    return errors


def package_hash_errors(freeze):
    return [name for name, expected in freeze["sha256"].items()
            if not (ROOT / name).is_file() or file_sha(ROOT / name) != expected]


def run_legacy_audit(raw_path, output_path):
    spec = importlib.util.spec_from_file_location("frozen_a01_auditor", ROOT / "audit_a01.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = ROOT
    passed = module.audit(raw_path, output_path)
    result = json.loads(Path(output_path).read_text(encoding="utf-8"))
    return passed, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    package_bad = package_hash_errors(freeze)
    if package_bad:
        raise SystemExit("A02_FREEZE_HASH_MISMATCH:" + ",".join(package_bad))

    prerun_bytes = (ROOT / "PRE-RUN.json").read_bytes()
    prerun = json.loads(prerun_bytes)
    workload_bytes = (ROOT / "workload.json").read_bytes()
    raw_bytes = (ROOT / "A01_RAW.json").read_bytes()
    a01_source_checks = {
        "run_a01.py": file_sha(ROOT / "run_a01.py") == prerun["source_sha256"]["run_a01.py"],
        "audit_a01.py": file_sha(ROOT / "audit_a01.py") == prerun["source_sha256"]["audit_a01.py"],
        "workload.json": file_sha(ROOT / "workload.json") == prerun["source_sha256"]["workload.json"],
    }
    binding = binding_errors(workload_bytes, raw_bytes, prerun, freeze["sha256"]["A01_RAW.json"])
    if binding:
        raise SystemExit("A01_INPUT_BINDING_FAILED:" + ",".join(binding))

    legacy_passed, legacy_output = run_legacy_audit(ROOT / "A01_RAW.json", args.out)
    retained_a01_audit = json.loads((ROOT / "A01_AUDIT_V1.json").read_text(encoding="utf-8"))

    repro = json.loads((ROOT / "CONSTRUCTION_REPRO.json").read_text(encoding="utf-8"))
    mutant_workload = (ROOT / repro["mutant_workload_path"]).read_bytes()
    mutant_raw = (ROOT / repro["mutant_raw_path"]).read_bytes()
    mutant_audit = json.loads((ROOT / repro["mutant_audit_path"]).read_text(encoding="utf-8"))
    mutant_errors = binding_errors(mutant_workload, mutant_raw, prerun, freeze["sha256"]["A01_RAW.json"])
    mutant_workload_obj = json.loads(mutant_workload)
    mutant_raw_obj = json.loads(mutant_raw)
    changed_record = next(r for r in mutant_workload_obj["records"] if r["id"] == "stale-summary")
    mutant_graph_sha = sha(json.dumps({"nodes": mutant_workload_obj["nodes"],
                                      "edges": mutant_workload_obj["edges"]},
                                     sort_keys=True, separators=(",", ":")).encode())
    mutant_policy_bytes_ok = all(
        row.get("visible_bytes") == policy_visible_bytes(mutant_workload_obj["records"], row["selected_ids"])
        for row in mutant_raw_obj["policies"])
    mutant_record_hash_ok = (mutant_raw_obj["canonical_record_sha256"].get("stale-summary")
                             == canonical_sha(changed_record))
    checks = {
        "a01_frozen_sources_match_prerun": all(a01_source_checks.values()),
        "a01_workload_bytes_match_prerun": not binding_errors(workload_bytes, raw_bytes, prerun,
                                                                freeze["sha256"]["A01_RAW.json"]),
        "a01_original_raw_reaudited_pass": bool(legacy_passed and legacy_output.get("passed")
                                                   and legacy_output.get("classification") == "PASS_METHOD_SCOPED"),
        "a01_reaudited_output_matches_preserved_audit": legacy_output == retained_a01_audit,
        "mutation_graph_unchanged": mutant_graph_sha == prerun["graph_sha256"],
        "v1_mutant_raw_self_consistent": mutant_raw_obj.get("workload_sha256") == sha(mutant_workload),
        "v1_mutant_record_hash_self_consistent": mutant_record_hash_ok,
        "v1_mutant_policy_bytes_self_consistent": mutant_policy_bytes_ok,
        "v1_mutant_all_audit_checks_passed": bool(mutant_audit.get("passed")
                                                    and mutant_audit.get("checks")
                                                    and all(mutant_audit["checks"].values())
                                                    and repro.get("legacy_workload_hash_check_passed")),
        "v1_auditor_accepted_mutant": bool(mutant_audit.get("passed")),
        "v2_rejects_mutant_workload_and_raw": ("workload_bytes_match_prerun" in mutant_errors
                                                and "raw_artifact_matches_frozen_sha256" in mutant_errors),
        "candidate_invocations": 0,
        "a02_auditor_invocations": 1,
    }
    passed = all(value is True for key, value in checks.items()
                 if key not in ("candidate_invocations", "a02_auditor_invocations"))
    output = {
        "schema": "issue7367-a02-audit-v2",
        "passed": passed,
        "classification": "PASS_AUDIT_BINDING_REVALIDATED" if passed else "FAIL_AUDIT_V2",
        "checks": checks,
        "a01_workload_sha256": prerun["source_sha256"]["workload.json"],
        "a01_raw_sha256": sha(raw_bytes),
        "a01_reaudited_semantic_checks": legacy_output.get("checks", {}),
        "mutation": {
            "added_payload_bytes": repro["added_payload_bytes"],
            "mutant_audit_padding_length": len(changed_record.get("audit_padding", "")),
            "original_graph_sha256": prerun["graph_sha256"],
            "mutated_graph_sha256": mutant_graph_sha,
            "legacy_v1_binding_errors": [],
            "v2_binding_errors": mutant_errors,
        },
        "scope": "read-only audit of preserved A01 candidate output; candidate not replayed; finite declared workflow only",
    }
    Path(args.out).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"classification": output["classification"], "checks": checks}, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
