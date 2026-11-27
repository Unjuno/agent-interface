"""Audit and sanitize the one-shot standard-caller Fake X characterization."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def audit(raw, expected_revision):
    first = raw["first_cancel"]
    second = raw["second_cancel"]
    result = raw["terminal_interface_results"]
    require(raw["source_revision"] == expected_revision, "source revision mismatch")
    for source_path, expected_hash in raw["source_sha256"].items():
        require(digest(source_path) == expected_hash,
                f"source digest mismatch for {source_path}")
    require(raw["status"] == "trial_complete", "trial did not complete")
    require(raw["initial_owner_keys_down"] == [1], "Fake X did not record held CTRL")
    require(raw["release_attempt_count"] == 1, "release helper count is not one")
    require(first["status"] == "cancel_requested", "first cancel status changed")
    require(first["owner_process_retired"] is True, "owner retirement missing")
    require(first["owner_process_exitcode"] == -15, "owner exit result changed")
    require(first["cleanup_status"] == "UNKNOWN", "unsafe cleanup promotion")
    require(first["release_confirmed"] is False, "release was falsely confirmed")
    require(first["task_success"] is None, "task success was falsely inferred")
    require(first["replay_allowed"] is False, "replay was allowed")
    require(second["status"] == "not_active", "duplicate response changed")
    require("cancellation_operation_id" not in first, "unexpected operation ID")
    require("cancellation_operation_id" not in second, "unexpected duplicate operation ID")
    require(result["status"] == "runtime_failed", "original call terminal status changed")
    require(result["cleanup_status"] == "UNKNOWN", "terminal cleanup promoted")
    require(result["release_confirmed"] is False, "terminal release was falsely confirmed")
    require(result["task_success"] is None, "terminal task success was falsely inferred")
    require(result["replay_allowed"] is False, "terminal replay was allowed")
    require("cancellation" not in result, "unexpected retained cancellation subrecord")
    session_owner = result["session"]["owner_process"]
    require(session_owner["alive"] is True and session_owner["retired"] is False,
            "stale action-owner snapshot changed")
    return {
        "decision": "PASS_CHARACTERIZATION_GAP_REPRODUCED",
        "errors": [],
        "trials": 1,
        "release_attempt_count": 1,
        "duplicate_status": "not_active",
        "stable_cancellation_operation_id": False,
        "separate_cancellation_result": False,
        "action_result_cleanup": "UNKNOWN",
        "release_confirmed": False,
        "task_success": None,
        "replay_allowed": False,
        "owner_liveness_snapshot_conflicts_with_cancel_retirement": True,
        "scope": "public standard MCP composition over local Fake X with synthetic cleanup receipts",
    }


def sanitize(raw):
    public = copy.deepcopy(raw)
    call_id = public["call_id"]
    public["call_id"] = "CALL_R02"
    public["terminal_interface_results"]["call_id"] = "CALL_R02"
    public["terminal_interface_results"]["retained_call"]["call_id"] = "CALL_R02"
    public["terminal_interface_results"]["call_directory"] = "<TEMP>/CALL_R02"
    public["terminal_interface_results"]["owner_process"]["pid"] = "OWNER_PID_R02"
    public["terminal_interface_results"]["session"]["session_id"] = "SESSION_R02"
    public["terminal_interface_results"]["session"]["compiled_scope"] = "<SYNTHETIC_SCOPE>"
    public["terminal_interface_results"]["session"]["owner_process"]["pid"] = "OWNER_PID_R02"
    public["terminal_interface_results"]["session"]["owner_process"]["alive"] = True
    public["terminal_interface_results"]["session"]["owner_process"]["exitcode"] = None
    public["terminal_interface_results"]["session"]["owner_process"]["retired"] = False
    public["terminal_interface_results"]["session"]["owner_process_pid"] = "OWNER_PID_R02"
    public["terminal_interface_results"]["session"]["compiled_surface"] = "<SYNTHETIC_SURFACE>"
    public["terminal_interface_results"]["session"]["target"] = "<SYNTHETIC_TARGET>"
    public["terminal_interface_results"]["session"]["targets"] = {"<SYNTHETIC_TARGET>": 20}
    if call_id in json.dumps(public):
        raise SystemExit("FAIL: call ID remains in sanitized JSON")
    return public


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--public", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    raw = load(args.raw)
    audit_result = audit(raw, args.revision)
    public = sanitize(raw)
    public_path = Path(args.public)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    redaction_result = {
        "policy": "Preserve behavioral fields, statuses, order, and measured timestamps; replace host-local identities and temp paths.",
        "source_revision": args.revision,
        "private_raw_sha256": digest(args.raw),
        "public_raw_sha256": digest(args.public),
        "run_probe_sha256": digest(Path(__file__).with_name("run_probe.py")),
        "replacements": {
            "random call ID": "CALL_R02",
            "random session ID": "SESSION_R02",
            "temporary call directory": "<TEMP>/CALL_R02",
            "OS owner PID": "OWNER_PID_R02",
            "synthetic scope/surface/target labels": "stable synthetic placeholders",
        },
        "unchanged": [
            "cancel responses and statuses",
            "cleanup uncertainty and replay flags",
            "release-attempt count and receipt",
            "monotonic timestamps",
            "source revision and source digests",
            "original action result fields",
        ],
    }
    redaction_path = Path(args.public).parent.parent / "redaction.json"
    redaction_path.write_text(json.dumps(redaction_result, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")
    audit_result["raw_sha256"] = digest(args.raw)
    audit_result["public_sha256"] = digest(args.public)
    audit_result["conditions_sha256"] = digest(Path(__file__).with_name("conditions.json"))
    audit_result["run_probe_sha256"] = digest(Path(__file__).with_name("run_probe.py"))
    audit_result["public_redactions"] = [
        "random call and session IDs", "local temporary directory",
        "OS process ID", "synthetic scope/surface/target labels",
    ]
    Path(args.audit).write_text(
        json.dumps(audit_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps(audit_result, sort_keys=True))


if __name__ == "__main__":
    main()
