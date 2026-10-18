"""Interpret retained app-server diagnostic receipts without replaying probes."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
RECEIPTS = ROOT.parents[1] / "live_control" / "appserver_closed_diagnostic_59_20261003_01a0ff52"
SOURCE_SHA = "8ed4e3496ef8154d3c4573fb1386efe6e036292a3809e43aa37fc22aecc5b42b"
INPUT_MANIFEST_SHA = "e16b8b33e7dc787aff10ab049c1f76af2b27e1088a2d7ef2bd859a5d67c673e1"
CASE_IDS = [
    "request-healthy", "notification-healthy", "request-closed_both", "notification-closed_both",
    "request-stderr_retained", "notification-stderr_retained",
    "request-stderr_retained-local", "notification-stderr_retained-local",
]


def load_case(case_id):
    local = case_id.endswith("-local")
    base_id = case_id[:-6] if local else case_id
    run = "construction02-local-deadline" if local else "construction01"
    directory = RECEIPTS / run
    files = {
        "outer_receipt": directory / (base_id + ".receipt.json"),
        "result": directory / base_id / "result.json",
        "child_events": directory / base_id / "child-events.jsonl",
        "journal": directory / base_id / "journal.jsonl",
        "stdout": directory / (base_id + ".stdout"),
        "stderr": directory / (base_id + ".stderr"),
        "input_manifest": RECEIPTS / "SHA256SUMS",
    }
    row = json.loads(files["result"].read_text())
    outer = json.loads(files["outer_receipt"].read_text())
    events = [json.loads(line) for line in files["child_events"].read_text().splitlines()]
    journal = [json.loads(line) for line in files["journal"].read_text().splitlines()]
    stdout = files["stdout"].read_bytes()
    stderr = files["stderr"].read_bytes()
    source_meta = json.loads((RECEIPTS / "SOURCE.json").read_text())
    source = (RECEIPTS / "codex_app_server_client_v2.py.txt").read_text()
    files["source_meta"] = RECEIPTS / "SOURCE.json"
    files["source"] = RECEIPTS / "codex_app_server_client_v2.py.txt"
    repo_root = ROOT.parents[2]
    input_hashes = {str(path.relative_to(repo_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in files.values()}
    manifest_text = files["input_manifest"].read_text()
    manifest_hashes = {line.split("  ", 1)[1]: line.split("  ", 1)[0]
                       for line in manifest_text.splitlines() if "  " in line}
    manifest_inputs = {str(path.relative_to(RECEIPTS)): hashlib.sha256(path.read_bytes()).hexdigest()
                       for key, path in files.items() if key != "input_manifest"
                       and path.is_relative_to(RECEIPTS)}
    return {"id": case_id, "base_id": base_id, "local": local, "result": row,
            "outer": outer, "child_events": events, "journal": journal,
            "stdout": stdout, "stderr": stderr, "source_meta": source_meta,
            "source": source, "input_hashes": input_hashes,
            "manifest_hash": hashlib.sha256(files["input_manifest"].read_bytes()).hexdigest(),
            "manifest_inputs": manifest_inputs, "manifest_expected": manifest_hashes}


def _integrity_errors(case):
    r, outer = case["result"], case["outer"]
    errors = []
    if case["manifest_hash"] != INPUT_MANIFEST_SHA:
        errors.append("input_manifest_identity")
    for path, digest in case["manifest_inputs"].items():
        if case["manifest_expected"].get(path) != digest:
            errors.append("frozen_input_digest")
    if r.get("source_sha256") != SOURCE_SHA or case["source_meta"].get("sha256") != SOURCE_SHA:
        errors.append("source_identity")
    if hashlib.sha256(case["source"].encode()).hexdigest() != SOURCE_SHA:
        errors.append("source_bytes")
    if outer.get("exit_code") != 0 or outer.get("outer_timeout") is not False:
        errors.append("outer_exit")
    for stream in ("stdout", "stderr"):
        if hashlib.sha256(case[stream]).hexdigest() != outer.get(stream + "_sha256"):
            errors.append(stream + "_digest")
    if outer.get("probe_pid") != r.get("probe_pid"):
        errors.append("probe_pid")
    if outer.get("sources", {}).get("codex_app_server_client_v2.py") != SOURCE_SHA:
        errors.append("outer_source_identity")
    child_pid = r.get("child_pid")
    if not case["child_events"] or any(e.get("pid") != child_pid for e in case["child_events"]):
        errors.append("child_identity")
    if (case["child_events"] != r.get("checkpoint", {}).get("child_events")
            or case["child_events"] != r.get("final", {}).get("child_events")):
        errors.append("child_event_join")
    if (len(case["child_events"]) < 2 or case["child_events"][0].get("event") != "started"
            or case["child_events"][1].get("event") != "ready"
            or case["child_events"][0].get("api") != r.get("api")):
        errors.append("child_lifecycle")
    if len(case["stdout"]) > 65536 or len(case["stderr"]) > 65536:
        errors.append("log_cap")
    if r.get("api") == "request":
        call = r.get("checkpoint", {}).get("call_record", {})
        request_events = [e for e in case["journal"] if e.get("direction") == "sent"]
        received = [e for e in case["child_events"] if e.get("event") == "request_received"]
        if (len(request_events) != 1 or len(received) != 1
                or request_events[0].get("message") != {"method": "owned/probe", "id": 1}
                or received[0].get("request_id") != 1
                or received[0].get("method") != "owned/probe"
                or not call.get("started_ns", 0) <= received[0].get("monotonic_ns", -1)
                   <= r.get("checkpoint", {}).get("at_ns", 0)):
            errors.append("request_event_join")
    elif any(event.get("direction") != "received" for event in case["journal"]):
        errors.append("unexpected_notification_journal")
    try:
        if json.loads(case["stdout"]) != r:
            errors.append("stdout_row_join")
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("stdout_json")
    return errors


def evaluate_case(case):
    r = case["result"]
    if _integrity_errors(case):
        return {"id": case["id"], "mechanism": "EVIDENCE_CONFLICT_OR_INCOMPLETE",
                "mechanism_boundary": None, "blame": "UNLOCALIZED", "blamed_component": None,
                "repair_route": "SAFE_YIELD"}
    events = case["child_events"]
    ready = events[1] if len(events) > 1 else {}
    checkpoint = r.get("checkpoint", {})
    call = checkpoint.get("call_record", {})
    before = r.get("before_call", {})
    api = r.get("api")
    if (before.get("transport_closed") is False and checkpoint.get("caller_alive") is False
            and call.get("outcome") == "RETURN"):
        return {"id": case["id"], "mechanism": "EXPECTED_RETURN", "mechanism_boundary": None,
                "blame": "NONE", "blamed_component": None, "repair_route": "NONE"}
    if (ready.get("stdout_closed") is True and ready.get("stderr_closed") is True
            and checkpoint.get("caller_alive") is False and call.get("exception", {}).get("type") == "AppServerError"):
        return {"id": case["id"], "mechanism": "EXPECTED_CLOSED_TRANSPORT_ERROR",
                "mechanism_boundary": None, "blame": "NONE", "blamed_component": None,
                "repair_route": "NONE"}
    stack = checkpoint.get("stack", [])
    expected_line = 75 if api == "request" else 101
    source_lines = case["source"].splitlines()
    frame_at_literal_read = bool(stack) and stack[0] == {
        "file": "codex_app_server_client_v2.py",
        "function": "request" if api == "request" else "wait_notification",
        "line": expected_line,
    } and expected_line <= len(source_lines) and "self.process.stderr.read()" in source_lines[expected_line - 1]
    retained = ready.get("stdout_closed") is True and ready.get("stderr_closed") is False
    blocked = checkpoint.get("caller_alive") is True and frame_at_literal_read
    if retained and blocked:
        deadline = checkpoint.get("local_deadline")
        if case["local"] and isinstance(deadline, dict):
            expired = (type(deadline.get("deadline_s")) is float
                       and type(deadline.get("remaining_s_at_read_entry")) is float
                       and type(deadline.get("observed_monotonic_s")) is float
                       and 0 < deadline["remaining_s_at_read_entry"] <= 0.05
                       and deadline["observed_monotonic_s"] - deadline["deadline_s"] > 0.20)
            if expired:
                mechanism = "DEADLINE_EXPIRED_DURING_DIAGNOSTIC_READ"
            else:
                mechanism = "BLOCKED_DIAGNOSTIC_READ_OBSERVED"
        else:
            mechanism = "BLOCKED_DIAGNOSTIC_READ_OBSERVED"
        return {"id": case["id"], "mechanism": mechanism,
                "mechanism_boundary": "APP_SERVER_CLIENT_DIAGNOSTIC_READ",
                "blame": "UNLOCALIZED", "blamed_component": None, "repair_route": "SAFE_YIELD"}
    return {"id": case["id"], "mechanism": "INSUFFICIENT_DIRECT_BOUNDARY_EVIDENCE",
            "mechanism_boundary": None, "blame": "UNLOCALIZED", "blamed_component": None,
            "repair_route": "SAFE_YIELD"}


def main():
    cases = []
    for case_id in CASE_IDS:
        case = load_case(case_id)
        decision = evaluate_case(case)
        cases.append({"id": decision["id"], "input_sha256": case["input_hashes"],
                      "classification": {k: v for k, v in decision.items() if k != "id"}})
    output = {"cases": cases, "formal_native_or_model_replays": 0}
    path = ROOT / "results" / "candidate.raw.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
