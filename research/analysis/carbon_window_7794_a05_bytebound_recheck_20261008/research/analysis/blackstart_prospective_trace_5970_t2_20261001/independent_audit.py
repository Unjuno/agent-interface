#!/usr/bin/env python3
"""Independent raw-trace audit; does not import candidate or runner."""
import base64
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reconstruct_inputs(freeze):
    repo = next(path for path in ROOT.parents if (path / ".git").exists())
    encoded = bytearray()
    parts_ok = True
    for rel, expected in sorted(freeze["archive_parts"].items()):
        blob = (repo / freeze["archive_path"] / rel).read_bytes()
        parts_ok &= digest(blob) == expected
        encoded.extend(blob)
    archive = base64.b64decode(bytes(encoded), validate=True)
    archive_ok = len(archive) == freeze["archive_bytes"] and digest(archive) == freeze["archive_sha256"]
    found = {}
    expanded = lzma.decompress(archive)
    with tarfile.open(fileobj=io.BytesIO(expanded), mode="r:") as tf:
        members = tf.getmembers()
        inventory_ok = len(members) == freeze["expanded_file_count"]
        for basename, expected in freeze["upstream_sources_sha256"].items():
            matches = [m for m in members if Path(m.name).name == basename and m.isfile()]
            if len(matches) != 1:
                found[basename] = False
                continue
            found[basename] = digest(tf.extractfile(matches[0]).read()) == expected
    return parts_ok, archive_ok, inventory_ok, found


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def audit_trace(candidate, run_dir):
    errors = []
    app = rows(run_dir / "app_events.jsonl")
    observer = rows(run_dir / "observer_events.jsonl")
    actions = rows(run_dir / "actions.jsonl")
    run = json.loads((run_dir / "run.raw.json").read_text(encoding="utf-8"))
    if run.get("status") != "RUN_COMPLETE" or run.get("terminal_shift_down") is not False:
        errors.append("runner did not complete with neutral terminal state")
    if run.get("app_returncode") != 0 or run.get("observer_returncode") != 0:
        errors.append("fixture child did not exit cleanly")
    if candidate.get("app_rows") != app or candidate.get("observer_rows") != observer or candidate.get("driver_rows") != actions:
        errors.append("candidate summary differs from raw JSONL")
    app_events = [r for r in app if r.get("source") == "app"]
    obs_events = [r for r in observer if r.get("source") == "observer"]
    if [r.get("source_seq") for r in app_events] != list(range(1, len(app_events) + 1)):
        errors.append("app source-local event sequence is not contiguous")
    obs_sequences = [r.get("source_seq") for r in obs_events]
    if obs_sequences != sorted(set(obs_sequences)):
        errors.append("observer source-local sequence is not strictly increasing")
    expected = [("KeyPress", "shift-1"), ("KeyRelease", "shift-2")]
    if len(app_events) != 2 or len(obs_events) != 2:
        errors.append("unexpected number of observed keyboard events")
    for kind, suffix in expected:
        action_ids = {r.get("actuation_id") for r in actions if r.get("actuation_id", "").endswith(suffix)}
        if len(action_ids) != 1:
            errors.append(f"driver action id cardinality failure for {suffix}")
            continue
        actuation_id = next(iter(action_ids))
        phase = [r.get("phase") for r in actions if r.get("actuation_id") == actuation_id]
        if phase != ["arm_request", "both_armed", "dispatch_request", "dispatch_sync_complete"]:
            errors.append(f"driver phase protocol failure for {actuation_id}")
        acks_a = [i for i, r in enumerate(app) if r.get("kind") == "arm_ack" and r.get("actuation_id") == actuation_id]
        acks_o = [i for i, r in enumerate(observer) if r.get("kind") == "arm_ack" and r.get("actuation_id") == actuation_id]
        events_a = [i for i, r in enumerate(app) if r.get("source") == "app" and r.get("actuation_id") == actuation_id]
        events_o = [i for i, r in enumerate(observer) if r.get("source") == "observer" and r.get("actuation_id") == actuation_id]
        if len(acks_a) != 1 or len(acks_o) != 1 or len(events_a) != 1 or len(events_o) != 1:
            errors.append(f"missing or duplicate stream record for {actuation_id}")
            continue
        ia, io_ = events_a[0], events_o[0]
        a, o = app[ia], observer[io_]
        if acks_a[0] >= ia or acks_o[0] >= io_:
            errors.append(f"arm acknowledgement does not precede event in stream order for {actuation_id}")
        if a.get("kind") != kind or o.get("kind") != kind:
            errors.append(f"wrong event kind for {actuation_id}")
        if a.get("keycode") != o.get("keycode") or a.get("x_time") != o.get("x_time"):
            errors.append(f"independent streams disagree on X event identity for {actuation_id}")
        if a.get("causal_parent_ids") != [f"act:{actuation_id}"] or o.get("causal_parent_ids") != [f"act:{actuation_id}"]:
            errors.append(f"explicit parent link missing for {actuation_id}")
        if a.get("event_id") == o.get("event_id"):
            errors.append(f"source-local event identifiers are not distinct for {actuation_id}")
        dispatches = [r for r in actions if r.get("actuation_id") == actuation_id and r.get("phase") == "dispatch_request"]
        if len(dispatches) != 1 or dispatches[0].get("event_kind") != kind or dispatches[0].get("keycode") != a.get("keycode"):
            errors.append(f"raw event does not match dispatch record for {actuation_id}")
    # Timestamps are only checked for presence; they are never used to infer parentage or admission.
    if any("mono_ns" not in r for r in app + observer + actions):
        errors.append("diagnostic monotonic clock field missing")
    return errors, app, observer, actions, run


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    candidate_path = ROOT / "candidate.raw.json"
    run_dir = ROOT / "run" / "trace"
    errors = []
    parts_ok, archive_ok, inventory_ok, source_ok = reconstruct_inputs(freeze)
    if not parts_ok or not archive_ok or not inventory_ok or not all(source_ok.values()):
        errors.append("frozen upstream archive/source integrity failure")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    trace_errors, app, observer, actions, run = audit_trace(candidate, run_dir)
    errors.extend(trace_errors)
    expected = "PASS_PROSPECTIVE_CAUSAL_IDS" if not errors else "HOLD_OR_FAIL_AUDIT"
    if candidate.get("disposition") != "PASS_PROSPECTIVE_CAUSAL_IDS":
        errors.append("candidate did not reach preregistered PASS disposition")
        expected = "FAIL_CANDIDATE_DISPOSITION"
    result = {
        "schema": "blackstart-prospective-causal-trace-independent-audit-v1",
        "status": "PASS_AUDIT_PROSPECTIVE_CAUSAL_IDS" if not errors else expected,
        "errors": errors,
        "upstream_archive_parts_verified": parts_ok,
        "upstream_archive_verified": archive_ok,
        "upstream_inventory_verified": inventory_ok,
        "upstream_sources_verified": source_ok,
        "candidate_sha256": digest(candidate_path.read_bytes()),
        "candidate_disposition": candidate.get("disposition"),
        "app_tagged_events": len([r for r in app if r.get("source") == "app"]),
        "observer_tagged_events": len([r for r in observer if r.get("source") == "observer"]),
        "driver_rows": len(actions),
        "terminal_shift_down": run.get("terminal_shift_down"),
        "decision_used_monotonic_timestamps_for_causality": False,
    }
    (ROOT / "audit.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT_PROSPECTIVE_CAUSAL_IDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
