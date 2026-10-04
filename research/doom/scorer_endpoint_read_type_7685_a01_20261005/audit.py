import hashlib
import json
import subprocess
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PKG = Path(__file__).resolve().parent


def main():
    freeze = json.loads((PKG / "FREEZE.json").read_text())
    result = json.loads((PKG / "RESULT.json").read_text())
    source = subprocess.check_output(["git", "show", f"{freeze['subject_pr_head']}:{freeze['source_path']}"], cwd=ROOT)
    actual = hashlib.sha256(source).hexdigest()
    cases = {row["case"]: row for row in result["cases"]}
    checks = {
        "pinned_subject_and_source_match": result["subject_pr_head"] == freeze["subject_pr_head"] and actual == freeze["source_sha256"] == result["source_sha256"],
        "exact_case_inventory": set(cases) == {"integer_control", "float_alias", "bool_alias"},
        "integer_control_pending_with_values": cases.get("integer_control", {}).get("receipt_status") == "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING" and cases.get("integer_control", {}).get("values_present") is True,
        "float_alias_accepted_by_candidate": cases.get("float_alias", {}).get("readback") == {"value": 11.0, "type": "float"} and cases.get("float_alias", {}).get("after") == {"value": 11, "type": "int"} and cases.get("float_alias", {}).get("receipt_status") == "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
        "bool_alias_accepted_by_candidate": cases.get("bool_alias", {}).get("readback") == {"value": True, "type": "bool"} and cases.get("bool_alias", {}).get("after") == {"value": 1, "type": "int"} and cases.get("bool_alias", {}).get("receipt_status") == "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
        "decision_matches_raw": result["decision"] == "FAIL_OPEN_ENDPOINT_TYPE",
    }
    report = {"schema": "scorer-endpoint-read-type-7685-a01-audit-v1", "pass": all(checks.values()), "checks": checks, "errors": [], "scope": "independent saved-row/source-pin audit; not runtime behavior"}
    if not report["pass"]:
        report["errors"] = [key for key, ok in checks.items() if not ok]
    (PKG / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
