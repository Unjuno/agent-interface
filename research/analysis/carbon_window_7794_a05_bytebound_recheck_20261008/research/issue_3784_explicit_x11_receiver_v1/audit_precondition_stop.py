"""Forensic addendum: independently bind an early receiver-control STOP.

This does not replace the frozen audit.py. It only classifies a STOP that
occurred before map capture or candidate execution, when those later-stage
artifacts are correctly absent.
"""
import hashlib
import json
from pathlib import Path
import sys

EXPECTED_RAW = "34f6e18f90a0af9af75c3fdecf74297f9b562e052b139b076b1aaa060edf9859"
RUNNER_SHA = "bb202694699595887735b9121324b402751c5171087ad993853dde4cde2b1e9e"
CASE_IDS = ["de-01", "de-02", "de-03", "us-control"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != "raw.json"}


def main():
    evidence, source, output = map(lambda p: Path(p).resolve(), sys.argv[1:4])
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    raw_bytes = (evidence / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    runner = (source / "research/issue_3784_explicit_x11_receiver_v1/runner.py").read_text()
    errors, findings = [], []
    if sha(raw_bytes) != EXPECTED_RAW: errors.append("RAW_SHA")
    if sha((source / "research/issue_3784_explicit_x11_receiver_v1/runner.py").read_bytes()) != RUNNER_SHA:
        errors.append("RUNNER_SHA")
    if raw.get("runner_sha256") != RUNNER_SHA: errors.append("RAW_RUNNER_BINDING")
    if raw.get("allocation") != "issue3784-explicit-x11-receiver-formal-01": errors.append("ALLOCATION")
    if raw.get("disposition") != "STOP_GERMAN_FORMULA_DELIVERY": errors.append("RAW_DISPOSITION")
    if inventory(evidence) != raw.get("artifact_sha256"): errors.append("ARTIFACT_INVENTORY")
    rows = raw.get("rows", [])
    if [row.get("case_id") for row in rows] != CASE_IDS: errors.append("CASE_MATRIX")
    for row in rows:
        cid = row.get("case_id")
        if row.get("status") != "STOP_RECEIVER_CONTROL": errors.append("STOP_GATE:" + str(cid))
        recv = row.get("receiver", {})
        if (recv.get("class") != "InputOnly" or recv.get("mapped") is not True or
                recv.get("window_id") != recv.get("focus_window_id") or row.get("focus_verified") is not True):
            errors.append("FOCUS_BINDING:" + str(cid))
        events = row.get("receiver_control", [])
        if not (len(events) == 2 and [e.get("type") for e in events] == ["KeyPress", "KeyRelease"]
                and events[0].get("keycode") == events[1].get("keycode")
                and [e.get("lookup_text") for e in events] == ["a", "a"]
                and [e.get("keysym") for e in events] == [97, 97]):
            errors.append("CONTROL_RECEIPT:" + str(cid))
        if row.get("receiver_control_ok") is not False: errors.append("CONTROL_GATE_RESULT:" + str(cid))
        if row.get("plan_keycodes") is not None or row.get("events") is not None or row.get("unsupported") is not None:
            errors.append("CANDIDATE_SHOULD_NOT_HAVE_RUN:" + str(cid))
        if row.get("xvfb_cleanup", {}).get("reaped") is not True: errors.append("XVFB_REAP:" + str(cid))
        row_path = evidence / "cases" / cid / "row.json"
        if not row_path.is_file() or json.loads(row_path.read_text()) != row:
            errors.append("ROW_ARTIFACT_BINDING:" + str(cid))
        findings.append({"case_id": cid, "status": row.get("status"),
                         "focus_verified": row.get("focus_verified"),
                         "control_events": [(e.get("type"), e.get("keycode"), e.get("lookup_text")) for e in events],
                         "candidate_reached": row.get("plan_keycodes") is not None,
                         "xvfb_reaped": row.get("xvfb_cleanup", {}).get("reaped")})
    wrong_release_oracle = '("KeyRelease", keycode, "")' in runner
    if not wrong_release_oracle: errors.append("EXPECTED_ORACLE_MISMATCH_NOT_FOUND")
    disposition = "FAIL_AUDIT_INTEGRITY" if errors else "PASS_AUDIT_CONFIRMED_HARNESS_STOP"
    audit = {"schema": "agent-interface/issue3784-precondition-stop-audit-v2",
             "raw_sha256": sha(raw_bytes), "runner_sha256": sha(runner.encode()),
             "rows": findings, "identified_harness_defect":
             "runner expected empty XLookupString bytes on KeyRelease, while the frozen construction gate and all formal controls observed 'a'; the control gate therefore stopped before map capture and candidate execution",
             "errors": errors, "disposition": disposition}
    (output / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"disposition": disposition, "errors": errors, "rows": findings}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
