"""Independently audit both successful authored-condition transfer pairs."""
import hashlib
import json
from pathlib import Path

from audit_local_displacement_x11_v1 import audit_case


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_pair(root, decision):
    plan = read(root / "preregistration.json")
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    assert sha(HERE / plan["authored_source_relative"]) == plan["authored_source_sha256"]
    authored_value = read(root / "authored-postcondition.json")
    if "authored_output_sha256" in plan:
        authored_identity = plan["authored_output_sha256"]
        assert sha(root / "authored-postcondition.json") == authored_identity
    else:
        authored_identity = hashlib.sha256(json.dumps(
            authored_value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert authored_identity == plan["authored_output_canonical_sha256"]
    report = read(root / "report.json")
    assert report["passed"] is True and report["decision"] == decision
    target = audit_case(root / "target")
    partial = audit_case(root / "partial")
    assert target["delta"] == [24, 0]
    assert target["outcome"]["reason"] == "met" and 4 in target["steps_started"]
    assert abs((target["saved_x"] - 50) * 1.18 - 24) <= 1
    assert partial["delta"] == [20, 0]
    assert partial["outcome"]["reason"] == "target_not_reached" and 4 not in partial["steps_started"]
    assert partial["saved_x"] == 50
    assert target["terminal"]["release"]["verified"] is True
    assert partial["terminal"]["release"]["verified"] is True
    source_sha = sha(root / "target/001.png")
    assert source_sha == sha(root / "partial/001.png")
    return {"order": plan["order"], "authored_value": authored_value,
            "authored_identity": authored_identity,
            "source_sha256": source_sha, "target": target, "partial": partial}


def main():
    failed = read(HERE / "results/local-displacement-transfer-04/failure.json")
    assert failed["status"] == "preregistration_failed_before_input"
    assert failed["input_issued"] is False
    assert failed["prior_canonical_json_sha256"] == failed["generated_canonical_json_sha256"]
    first = check_pair(HERE / "results/local-displacement-transfer-03",
                       "RETAIN_MODEL_AUTHORED_FRESH_TRANSFER;_REPLICATE_BEFORE_PROMOTION")
    second = check_pair(HERE / "results/local-displacement-transfer-05",
                        "RETAIN_UNCHANGED_REPLICATION;_ASSESS_SCOPED_PROMOTION")
    assert first["authored_value"] == second["authored_value"]
    assert first["source_sha256"] == second["source_sha256"]
    audit = {
        "audit_passed": True,
        "v4_preregistration_failure_retained": True,
        "pairs": 2, "cases": 4,
        "orders": [first["order"], second["order"]],
        "authored_condition_unchanged": True,
        "fresh_initial_source_identical_across_all_four_cases": True,
        "authored_output_canonical_sha256": hashlib.sha256(json.dumps(
            first["authored_value"], sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "initial_source_sha256": first["source_sha256"],
        "target_deltas": [first["target"]["delta"], second["target"]["delta"]],
        "partial_deltas": [first["partial"]["delta"], second["partial"]["delta"]],
        "target_save_started": [True, True],
        "partial_save_started": [False, False],
        "all_terminal_releases_verified": True,
        "exact_frames": sum(case[side]["exact_frames"] for case in (first, second)
                            for side in ("target", "partial")),
        "sample_spans_ms": [case[side]["outcome"]["sample_span_ms"]
                            for case in (first, second) for side in ("target", "partial")],
        "decision": "PROMOTE_ONLY_AS_SCOPED_MOVED_OBJECT_LOCAL_POSTCONDITION_CANDIDATE",
        "scope": "two fresh same-task target/partial pairs, opposite order, unchanged first Luna-authored patch; scripted pointer paths and no in-episode model call; no placement, unseen geometry, speed, token, cross-domain or broad autonomy claim",
        "audit_sha256": sha(Path(__file__)),
        "audit_correction": "first audit invocation expected the v3 byte-hash field in v5; no execution artifact changed",
    }
    out = HERE / "results/local-displacement-transfer-05/audit.json"
    out.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
