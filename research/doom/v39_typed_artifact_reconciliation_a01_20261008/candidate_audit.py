import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "results" / "a01" / "AUDIT_CANDIDATE.json"
if AUDIT.exists():
    raise SystemExit("STOP_CANDIDATE_AUDIT_EXISTS")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze = json.loads((ROOT / "CANDIDATE_FREEZE.json").read_text(encoding="utf-8"))
    baseline_freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    result_path = ROOT / "results" / "a01" / "RESULT_CANDIDATE.json"
    baseline_path = ROOT / "results" / "a01" / "RESULT.json"
    baseline_audit_path = ROOT / "results" / "a01" / "AUDIT_V2.json"
    failure_path = ROOT / "results" / "a01" / "AUDIT_INITIAL_FAILURE.json"
    raw_bytes = result_path.read_bytes()
    raw = json.loads(raw_bytes)
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    checks = {
        "candidate_freeze_sha": sha(ROOT / "candidate/research/doom/doom_typed_observation_v1.py")
            == freeze["candidate_source_sha256"],
        "candidate_runner_sha": sha(ROOT / "candidate_probe.py")
            == freeze["candidate_probe_sha256"],
        "baseline_raw_sha": hashlib.sha256(baseline_bytes).hexdigest()
            == freeze["baseline_result_sha256"],
        "baseline_audit_sha": sha(baseline_audit_path) == freeze["baseline_audit_sha256"],
        "initial_audit_failure_preserved": sha(failure_path)
            == freeze["baseline_audit_failure_sha256"],
        "baseline_source_blob": baseline.get("source_blob")
            == baseline_freeze["source_files"]["research/doom/doom_typed_observation_v1.py"]["git_blob"],
        "candidate_base_blob": raw.get("baseline_source_blob")
            == baseline_freeze["source_files"]["research/doom/doom_typed_observation_v1.py"]["git_blob"],
        "candidate_source_hash": raw.get("candidate_source_sha256")
            == freeze["candidate_source_sha256"],
        "candidate_raw_sha": hashlib.sha256(raw_bytes).hexdigest()
            == "f10e9e839cf0de59c9ba4e9568ff5f24e89900f77de6db5fa1afdd71bd4661e9",
    }
    names = [
        "control_exact", "id_bool_int_alias", "step_bool_int_alias",
        "sequence_bool_int_alias", "capture_bool_int_alias",
        "binding_nested_bool_int_alias",
    ]
    rows = raw.get("rows")
    checks["candidate_case_order"] = (
        type(rows) is list and [row.get("case") for row in rows] == names
    )
    checks["candidate_control_passes"] = (
        type(rows) is list and rows[0].get("matched") is True and
        type(rows[0].get("checks")) is dict and
        all(value is True for value in rows[0]["checks"].values())
    )
    checks["candidate_rejects_all_aliases"] = (
        type(rows) is list and all(row.get("matched") is False for row in rows[1:])
        and raw.get("accepted_aliases") == []
    )
    checks["baseline_reproduces_all_aliases"] = (
        baseline.get("result") == "FAIL_BOOL_INT_ALIAS_ACCEPTED" and
        len(baseline.get("accepted_aliases", [])) == 5
    )
    checks["candidate_result_label"] = raw.get("result") == "PASS_EXACT_IDENTITY"
    output = {
        "schema": "issue8566-reconcile-alias-a01-independent-candidate-audit-v1",
        "candidate_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "baseline_raw_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "passed": all(checks.values()),
        "classification": raw.get("result"),
        "audit_scope": "frozen input/output/source integrity and baseline-vs-candidate result reconstruction",
    }
    AUDIT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(json.dumps({"passed": output["passed"],
                      "classification": output["classification"],
                      "checks_passed": output["checks_passed"],
                      "checks_total": output["checks_total"],
                      "candidate_raw_sha256": output["candidate_raw_sha256"]},
                     sort_keys=True))
    if not output["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
