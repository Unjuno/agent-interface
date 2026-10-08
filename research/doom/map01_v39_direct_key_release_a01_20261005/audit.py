"""Independent raw-only audit; does not import or rerun the candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
OUT = HERE / "results" / "candidate-a01"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    for relative, expected in FREEZE["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            errors.append("source-hash:" + relative)
    for relative, expected in FREEZE["package_sha256"].items():
        if sha(HERE / relative) != expected:
            errors.append("package-hash:" + relative)
    try:
        raw = json.loads((OUT / "raw.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append("raw:" + type(exc).__name__)
        raw = {}
    if raw.get("schema") != "map01-v39-selected-key-owner-raw-v1":
        errors.append("raw-schema")
    if raw.get("run_id") != FREEZE["run_id"] or raw.get("base_commit") != FREEZE["base_commit"]:
        errors.append("source-identity")
    if raw.get("candidate_invocations") != 1:
        errors.append("candidate-invocations")
    if raw.get("environment") != {
        "fake_xlib": True, "x_server": False, "os_input": False,
        "vizdoom": False, "model_calls": 0, "container": False,
    }:
        errors.append("scope")

    cases = raw.get("cases", {})
    control, fault = cases.get("control", {}), cases.get("aggregate_query_failure", {})
    expected_edges = [("key-down", 74), ("key-down", 65),
                      ("key-up", 65), ("key-up", 74)]
    for name, case in (("control", control), ("fault", fault)):
        ops = case.get("operations", [])
        edges = [(row.get("operation"), row.get("keycode")) for row in ops
                 if row.get("operation") in ("key-down", "key-up")]
        if edges != expected_edges:
            errors.append(name + ":edge-order")
        # One keymap query belongs to explicit release_all, one to owner.close.
        qpositions = [i for i, row in enumerate(ops)
                      if row.get("operation") == "keymap-query"]
        uppositions = [i for i, row in enumerate(ops)
                       if row.get("operation") == "key-up"]
        if len(qpositions) != 2 or len(uppositions) != 2:
            errors.append(name + ":query-or-up-count")
        elif not (uppositions[-1] < qpositions[0] < qpositions[1]):
            errors.append(name + ":query-order")
        elif any(row.get("operation") == "keymap-query"
                 for row in ops[uppositions[0] + 1:uppositions[1]]):
            errors.append(name + ":per-key-query-between-ups")
        if case.get("held_before_release_all") != []:
            errors.append(name + ":held-before-release-all")
        if case.get("held_after_release_all") != [] or case.get("physical_after_release_all") != []:
            errors.append(name + ":state-after-release-all")
        if case.get("held_after_close") != [] or case.get("physical_after_close") != []:
            errors.append(name + ":state-after-close")
        if case.get("owner_stopped_after_close") is not True:
            errors.append(name + ":owner-not-stopped")
        events = case.get("events", [])
        if (len(events) != 2 or
                any(row.get("event") != "input_admission" for row in events)):
            errors.append(name + ":unexpected-session-events")
        records = case.get("owner_records_after_close", [])
        if (not records or records[-1].get("event") != "owner_release"
                or records[-1].get("reason") != "close"
                or records[-1].get("verified") is not True
                or records[-1].get("keys_down") != []):
            errors.append(name + ":close-release-not-verified")

    if control.get("release_error_type") is not None:
        errors.append("control:release-error")
    control_release = control.get("release_result")
    if (type(control_release) is not dict
            or control_release.get("event") != "owner_release"
            or control_release.get("verified") is not True
            or control_release.get("keys_down") != []):
        errors.append("control:aggregate-release-unverified")
    if fault.get("release_error_type") != "RuntimeError" or fault.get("release_result") is not None:
        errors.append("fault:aggregate-failure-not-retained")
    fault_queries = [row for row in fault.get("operations", [])
                     if row.get("operation") == "keymap-query"]
    if (len(fault_queries) != 2
            or fault_queries[0].get("outcome") != "injected-unavailable"
            or fault_queries[1].get("outcome") != "returned"):
        errors.append("fault:failure-and-close-query")
    if fault.get("owner_records_before_close") != []:
        errors.append("fault:failed-release-record-unexpected")
    if fault.get("close_error_type") is not None:
        errors.append("fault:close-recovery-failed")

    result = {
        "schema": "map01-v39-selected-key-owner-audit-v1",
        "run_id": FREEZE["run_id"],
        "disposition": "PASS_SELECTED_KEY_PATH_CONTRACT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "control_release_verified": control.get("release_result", {}).get("verified") is True,
        "fault_first_release_unverified": fault.get("release_error_type") == "RuntimeError",
        "fault_close_recovered_neutral": (
            bool(fault.get("owner_records_after_close"))
            and fault["owner_records_after_close"][-1].get("verified") is True
            and fault.get("owner_stopped_after_close") is True),
        "scope": "session_v5 keyboard methods plus exact V10 owner with in-memory fake Xlib",
        "limits": "no X server, full V39 process, ViZDoom, application, physical input, useful feedback, task effect, MAP01 recovery, or latency qualification",
    }
    (OUT / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "errors": errors,
                      "control_release_verified": result["control_release_verified"],
                      "fault_close_recovered_neutral": result["fault_close_recovered_neutral"]},
                     sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
