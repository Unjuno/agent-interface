"""Posthoc verifier for immutable outputs of allocation issue-3690-dockerdesktop-host-01.

This reads saved logs/JSON only. It never invokes Docker, the candidate auditor,
or the unittest suite. It independently records the PowerShell result-count bug.
"""
import hashlib
import json
import pathlib
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    repo = pathlib.Path(__file__).resolve().parents[3]
    root = pathlib.Path(__file__).resolve().parent
    output = root / "results" / "formal01"
    bundle = repo / "research" / "issue_3676_audit_hardening_v1"
    result_bytes = (output / "hardening_audit.json").read_bytes()
    baseline_bytes = (bundle / "evidence" / "hardening_audit.json").read_bytes()
    result = json.loads(result_bytes)
    tests_log = (output / "tests.log").read_text(encoding="utf-8")
    manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    sum_path = root / "SHA256SUMS"
    expected_sums = {}
    for line in sum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        digest, relative = line.split(None, 1)
        expected_sums[relative.strip()] = digest.lower()
    checksum_checks = {
        relative: sha(root / relative) == digest
        for relative, digest in expected_sums.items()
        if relative != "results/formal01/verification-posthoc.json"
    }
    source_checks = {}
    for entry in manifest["files"]:
        source_checks[entry["path"]] = sha(bundle / entry["path"]) == entry["sha256"]
    named_tests = re.findall(r"^test_[^(]+ \(test_audit\.StrictAuditTests\.test_[^)]+\) \.\.\. ok$",
                             tests_log, re.MULTILINE)
    controls = result.get("corruption_controls_rejected", {})
    checks = {
        "docker_test_exit_zero": (output / "tests.exit").read_text().strip() == "0",
        "five_unittests_passed": len(named_tests) == 5,
        "docker_cli_exit_zero": (output / "cli.exit").read_text().strip() == "0",
        "cli_status_pass": result.get("status") == "PASS_OFFLINE_STRUCTURAL_AUDIT",
        "cli_errors_empty": result.get("errors") == [],
        "all_21_mutations_rejected": len(controls) == 21 and all(value is True for value in controls.values()),
        "cli_sha_matches_frozen": sha(output / "hardening_audit.json") == manifest["protocol"]["expected_cli_sha256"],
        "cli_bytes_match_retained": result_bytes == baseline_bytes,
        "all_source_hashes_match": all(source_checks.values()),
        "checksum_inventory_matches": all(checksum_checks.values()),
        "formal_wrapper_assertion_bug_identified": True,
    }
    report = {
        "allocation": manifest["allocation"],
        "decision": "PASS_DOCKERDESKTOP_HOST_VALIDATION_SCOPED_POSTHOC_AUDIT" if all(
            value for key, value in checks.items() if key != "formal_wrapper_assertion_bug_identified")
            else "HOLD_POSTHOC_VALIDATION_INCOMPLETE",
        "execution_record": "Both Docker containers exited zero; frozen PowerShell wrapper then exited nonzero because PSCustomObject.Count was treated as the map key count. No container was repeated.",
        "checks": checks,
        "test_names": named_tests,
        "cli_status": result.get("status"),
        "cli_error_count": len(result.get("errors", [])),
        "mutation_count": len(controls),
        "cli_sha256": sha(output / "hardening_audit.json"),
        "cli_byte_identical_to_retained": result_bytes == baseline_bytes,
        "source_checks": source_checks,
        "checksum_checks": checksum_checks,
        "container_stdout_sha256": {
            "tests.log": sha(output / "tests.log"),
            "cli.log": sha(output / "cli.log"),
        },
        "limitations": [
            "Posthoc verification reads retained outputs only; no Docker or candidate process was rerun.",
            "The frozen orchestration script itself ended with an assertion error; this is retained, not rewritten.",
            "This is an exact-source, finite container host-path validation, not arbitrary auditor soundness or XRes correctness evidence."
        ],
    }
    report_path = output / "verification-posthoc.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "checks_passed": sum(
        bool(value) for key, value in checks.items() if key != "formal_wrapper_assertion_bug_identified"),
        "check_count": len(checks) - 1}, sort_keys=True))
    return 0 if report["decision"] == "PASS_DOCKERDESKTOP_HOST_VALIDATION_SCOPED_POSTHOC_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
