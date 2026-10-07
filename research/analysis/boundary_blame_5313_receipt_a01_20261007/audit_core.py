"""Independent read-only oracle for retained #59 app-server receipt records."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT.parents[2]
DATA = REPO / "research/live_control/appserver_closed_diagnostic_59_20261003_01a0ff52"
SOURCE_SHA = "8ed4e3496ef8154d3c4573fb1386efe6e036292a3809e43aa37fc22aecc5b42b"
INPUT_MANIFEST_SHA = "e16b8b33e7dc787aff10ab049c1f76af2b27e1088a2d7ef2bd859a5d67c673e1"
ROSTER = [
    "request-healthy", "notification-healthy", "request-closed_both", "notification-closed_both",
    "request-stderr_retained", "notification-stderr_retained",
    "request-stderr_retained-local", "notification-stderr_retained-local",
]


def _read(case_id):
    local = case_id.endswith("-local")
    base_id = case_id[:-6] if local else case_id
    run_id = "construction02-local-deadline" if local else "construction01"
    run = DATA / run_id
    paths = {
        "outer_receipt": run / (base_id + ".receipt.json"),
        "result": run / base_id / "result.json",
        "child_events": run / base_id / "child-events.jsonl",
        "journal": run / base_id / "journal.jsonl",
        "stdout": run / (base_id + ".stdout"),
        "stderr": run / (base_id + ".stderr"),
        "source_meta": DATA / "SOURCE.json",
        "source": DATA / "codex_app_server_client_v2.py.txt",
        "input_manifest": DATA / "SHA256SUMS",
    }
    raw = {k: p.read_bytes() for k, p in paths.items()}
    row = json.loads(raw["result"])
    driver = json.loads(raw["outer_receipt"])
    events = [json.loads(x) for x in raw["child_events"].decode().splitlines()]
    source_meta = json.loads(raw["source_meta"])
    digest = {str(p.relative_to(REPO)): hashlib.sha256(raw[k]).hexdigest() for k, p in paths.items()}
    manifest = {}
    for line in raw["input_manifest"].decode().splitlines():
        if "  " in line:
            value, name = line.split("  ", 1)
            manifest[name] = value
    manifest_digest = hashlib.sha256(raw["input_manifest"]).hexdigest()
    manifest_inputs = {
        str(p.relative_to(DATA)): hashlib.sha256(raw[k]).hexdigest()
        for k, p in paths.items() if k != "input_manifest"
    }
    return {"local": local, "row": row, "driver": driver, "events": events,
            "source_meta": source_meta, "source": raw["source"].decode(),
            "journal": raw["journal"], "stdout": raw["stdout"], "stderr": raw["stderr"],
            "input_sha256": digest, "manifest": manifest,
            "manifest_digest": manifest_digest, "manifest_inputs": manifest_inputs}


def _decision(case_id, x):
    r, d = x["row"], x["driver"]
    events = x["events"]
    checks = []
    if x["manifest_digest"] != INPUT_MANIFEST_SHA:
        checks.append("input_manifest_identity")
    if any(x["manifest"].get(path) != value for path, value in x["manifest_inputs"].items()):
        checks.append("frozen_input_digest")
    if (r.get("source_sha256") != SOURCE_SHA or x["source_meta"].get("sha256") != SOURCE_SHA
            or d.get("sources", {}).get("codex_app_server_client_v2.py") != SOURCE_SHA
            or hashlib.sha256(x["source"].encode()).hexdigest() != SOURCE_SHA):
        checks.append("source")
    if (d.get("exit_code") != 0 or d.get("outer_timeout") is not False
            or d.get("probe_pid") != r.get("probe_pid")):
        checks.append("driver_receipt")
    if hashlib.sha256(x["stdout"]).hexdigest() != d.get("stdout_sha256"):
        checks.append("stdout_digest")
    if hashlib.sha256(x["stderr"]).hexdigest() != d.get("stderr_sha256"):
        checks.append("stderr_digest")
    try:
        if json.loads(x["stdout"]) != r:
            checks.append("stdout_binding")
    except (UnicodeDecodeError, json.JSONDecodeError):
        checks.append("stdout_parse")
    if not events or any(type(e.get("pid")) is not int or e.get("pid") != r.get("child_pid") for e in events):
        checks.append("child_pid")
    if len(x["stdout"]) > 65536 or len(x["stderr"]) > 65536:
        checks.append("log_cap")
    if (len(events) < 2 or events[0].get("event") != "started"
            or events[1].get("event") != "ready" or events[0].get("api") != r.get("api")):
        checks.append("child_lifecycle")
    if events != r.get("checkpoint", {}).get("child_events") or events != r.get("final", {}).get("child_events"):
        checks.append("child_event_binding")
    if r.get("api") == "request":
        journal = [json.loads(line) for line in x["journal"].decode().splitlines()]
        sent = [e for e in journal if e.get("direction") == "sent"]
        received = [e for e in events if e.get("event") == "request_received"]
        call = r.get("checkpoint", {}).get("call_record", {})
        if (len(sent) != 1 or len(received) != 1
                or sent[0].get("message") != {"method": "owned/probe", "id": 1}
                or received[0].get("request_id") != 1 or received[0].get("method") != "owned/probe"
                or not call.get("started_ns", 0) <= received[0].get("monotonic_ns", -1)
                   <= r.get("checkpoint", {}).get("at_ns", 0)):
            checks.append("request_event_join")
    elif any(e.get("direction") != "received" for e in
             (json.loads(line) for line in x["journal"].decode().splitlines())):
        checks.append("unexpected_notification_journal")
    if checks:
        return {"mechanism": "EVIDENCE_CONFLICT_OR_INCOMPLETE", "mechanism_boundary": None,
                "blame": "UNLOCALIZED", "blamed_component": None, "repair_route": "SAFE_YIELD"}

    ready = events[1] if len(events) > 1 else {}
    checkpoint = r.get("checkpoint", {})
    call = checkpoint.get("call_record", {})
    if r.get("before_call", {}).get("transport_closed") is False and call.get("outcome") == "RETURN":
        return {"mechanism": "EXPECTED_RETURN", "mechanism_boundary": None,
                "blame": "NONE", "blamed_component": None, "repair_route": "NONE"}
    if (ready.get("stdout_closed") is True and ready.get("stderr_closed") is True
            and call.get("outcome") == "RAISE" and call.get("exception", {}).get("type") == "AppServerError"):
        return {"mechanism": "EXPECTED_CLOSED_TRANSPORT_ERROR", "mechanism_boundary": None,
                "blame": "NONE", "blamed_component": None, "repair_route": "NONE"}

    api = r.get("api")
    line = 75 if api == "request" else 101
    function = "request" if api == "request" else "wait_notification"
    frame = checkpoint.get("stack", [{}])[0] if checkpoint.get("stack") else {}
    source_line = x["source"].splitlines()[line - 1] if line <= len(x["source"].splitlines()) else ""
    on_diagnostic_read = (frame == {"file": "codex_app_server_client_v2.py", "function": function, "line": line}
                          and "self.process.stderr.read()" in source_line)
    retained = ready.get("stdout_closed") is True and ready.get("stderr_closed") is False
    blocked = checkpoint.get("caller_alive") is True and on_diagnostic_read
    if retained and blocked:
        local = checkpoint.get("local_deadline") if x["local"] else None
        expired = (isinstance(local, dict) and type(local.get("deadline_s")) is float
                   and type(local.get("remaining_s_at_read_entry")) is float
                   and type(local.get("observed_monotonic_s")) is float
                   and 0 < local["remaining_s_at_read_entry"] <= 0.05
                   and local["observed_monotonic_s"] - local["deadline_s"] > 0.20)
        mechanism = "DEADLINE_EXPIRED_DURING_DIAGNOSTIC_READ" if expired else "BLOCKED_DIAGNOSTIC_READ_OBSERVED"
        return {"mechanism": mechanism, "mechanism_boundary": "APP_SERVER_CLIENT_DIAGNOSTIC_READ",
                "blame": "UNLOCALIZED", "blamed_component": None, "repair_route": "SAFE_YIELD"}
    return {"mechanism": "INSUFFICIENT_DIRECT_BOUNDARY_EVIDENCE", "mechanism_boundary": None,
            "blame": "UNLOCALIZED", "blamed_component": None, "repair_route": "SAFE_YIELD"}


def audit(raw):
    errors = []
    cases = raw.get("cases") if isinstance(raw, dict) else None
    if not isinstance(cases, list) or [x.get("id") for x in cases] != ROSTER:
        return {"status": "FAIL", "case_count": len(cases) if isinstance(cases, list) else 0,
                "checks": 0, "errors": ["case_roster_or_order"]}
    checks = 0
    for candidate_row, case_id in zip(cases, ROSTER):
        x = _read(case_id)
        expected = _decision(case_id, x)
        checks += 6
        if candidate_row.get("input_sha256") != x["input_sha256"]:
            errors.append(case_id + ":input_sha256_mismatch")
        if candidate_row.get("classification") != expected:
            errors.append(case_id + ":classification_mismatch")
    return {"status": "PASS" if not errors else "FAIL", "case_count": len(cases),
            "checks": checks, "errors": errors,
            "scoped_mechanism_localization": sum(1 for r in cases if r["classification"].get("mechanism") == "DEADLINE_EXPIRED_DURING_DIAGNOSTIC_READ"),
            "unsafe_component_blames": sum(1 for r in cases if r["classification"].get("blame") not in ("NONE", "UNLOCALIZED"))}
