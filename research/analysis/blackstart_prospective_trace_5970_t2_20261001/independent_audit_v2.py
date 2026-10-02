#!/usr/bin/env python3
"""Independent T2b audit, separately reconstructing source inventory and raw trace."""
import base64
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def source_inventory(freeze):
    repo = next(p for p in ROOT.parents if (p / ".git").exists())
    stream = bytearray()
    pieces_match = True
    for name, expected in freeze["archive_parts"].items():
        data = (repo / freeze["archive_path"] / name).read_bytes()
        pieces_match &= sha(data) == expected
        stream.extend(data)
    archive = base64.b64decode(bytes(stream), validate=True)
    archive_match = len(archive) == freeze["archive_bytes"] and sha(archive) == freeze["archive_sha256"]
    expanded = lzma.decompress(archive)
    with tarfile.open(fileobj=io.BytesIO(expanded), mode="r:") as tf:
        members = tf.getmembers()
        files = [m for m in members if m.isfile()]
        counts_match = len(members) == freeze["tar_member_count"] and len(files) == freeze["expanded_file_count"]
        upstream = {}
        for name, expected in freeze["upstream_sources_sha256"].items():
            hits = [m for m in files if Path(m.name).name == name]
            upstream[name] = len(hits) == 1 and sha(tf.extractfile(hits[0]).read()) == expected
    return {
        "parts_match": bool(pieces_match),
        "archive_match": archive_match,
        "tar_member_count": len(members),
        "regular_file_count": len(files),
        "counts_match": counts_match,
        "upstream_source_matches": upstream,
        "archive_sha256": sha(archive),
    }


def verify_v1_stop(record, inventory):
    return (
        record.get("status") == "STOP_CANDIDATE_PREFLIGHT_INVENTORY_PREDICATE"
        and record.get("exception") == "RuntimeError: frozen archive member count mismatch"
        and record.get("archive_sha256_reconstructed_diagnostically_after_stop") == inventory["archive_sha256"]
        and record.get("tar_members_total") == inventory["tar_member_count"]
        and record.get("regular_files") == inventory["regular_file_count"]
        and record.get("run_directory_created") is False
        and record.get("x_test_events_dispatched") == 0
    )


def validate_trace(candidate, trace):
    errors = []
    app = jsonl(trace / "app_events.jsonl")
    obs = jsonl(trace / "observer_events.jsonl")
    driver = jsonl(trace / "actions.jsonl")
    run = json.loads((trace / "run.raw.json").read_text(encoding="utf-8"))
    if candidate.get("app_rows") != app or candidate.get("observer_rows") != obs or candidate.get("driver_rows") != driver:
        errors.append("candidate summary does not byte-semantically match raw JSONL")
    if run.get("status") != "RUN_COMPLETE" or run.get("terminal_shift_down") is not False:
        errors.append("live fixture did not finish in the preregistered neutral state")
    if run.get("app_returncode") != 0 or run.get("observer_returncode") != 0:
        errors.append("instrumented process shutdown was not clean")
    ae = [r for r in app if r.get("source") == "app"]
    oe = [r for r in obs if r.get("source") == "observer"]
    if [r.get("source_seq") for r in ae] != list(range(1, len(ae) + 1)):
        errors.append("app source-local sequence invalid")
    if [r.get("source_seq") for r in oe] != sorted(set(r.get("source_seq") for r in oe)):
        errors.append("observer source-local sequence is not increasing and unique")
    if len(ae) != 2 or len(oe) != 2:
        errors.append("expected exactly two key events in each source stream")
    specs = (("KeyPress", "shift-1"), ("KeyRelease", "shift-2"))
    for kind, suffix in specs:
        ids = {r.get("actuation_id") for r in driver if r.get("actuation_id", "").endswith(suffix)}
        if len(ids) != 1:
            errors.append(f"driver event ID ambiguity: {suffix}")
            continue
        event_id = next(iter(ids))
        rows = [r for r in driver if r.get("actuation_id") == event_id]
        if [r.get("phase") for r in rows] != ["arm_request", "both_armed", "dispatch_request", "dispatch_sync_complete"]:
            errors.append(f"controller protocol order invalid: {event_id}")
        app_acks = [i for i, row in enumerate(app) if row.get("kind") == "arm_ack" and row.get("actuation_id") == event_id]
        obs_acks = [i for i, row in enumerate(obs) if row.get("kind") == "arm_ack" and row.get("actuation_id") == event_id]
        app_hits = [i for i, row in enumerate(app) if row.get("source") == "app" and row.get("actuation_id") == event_id]
        obs_hits = [i for i, row in enumerate(obs) if row.get("source") == "observer" and row.get("actuation_id") == event_id]
        if any(len(items) != 1 for items in (app_acks, obs_acks, app_hits, obs_hits)):
            errors.append(f"required arm/event row missing or duplicated: {event_id}")
            continue
        ar, orow = app[app_hits[0]], obs[obs_hits[0]]
        if app_acks[0] >= app_hits[0] or obs_acks[0] >= obs_hits[0]:
            errors.append(f"arm acknowledgement follows observed event: {event_id}")
        if ar.get("kind") != kind or orow.get("kind") != kind:
            errors.append(f"event kind mismatch: {event_id}")
        dispatch = [r for r in rows if r.get("phase") == "dispatch_request"]
        if len(dispatch) != 1 or dispatch[0].get("event_kind") != kind:
            errors.append(f"dispatch intent mismatch: {event_id}")
        if ar.get("keycode") != orow.get("keycode") or ar.get("x_time") != orow.get("x_time"):
            errors.append(f"observer and app disagree on X event identity: {event_id}")
        expected_parent = [f"act:{event_id}"]
        if ar.get("causal_parent_ids") != expected_parent or orow.get("causal_parent_ids") != expected_parent:
            errors.append(f"explicit causal parent absent/mismatched: {event_id}")
        if ar.get("event_id") == orow.get("event_id"):
            errors.append(f"event IDs are not source-local/distinct: {event_id}")
        if orow.get("epoch") != run.get("epoch") or not event_id.startswith(run.get("epoch", "") + ":"):
            errors.append(f"observer event epoch mismatch: {event_id}")
        if dispatch and dispatch[0].get("keycode") != ar.get("keycode"):
            errors.append(f"observed keycode differs from controller dispatch: {event_id}")
    return errors, app, obs, driver, run


def main():
    freeze = json.loads((ROOT / "FREEZE_V2.json").read_text(encoding="utf-8"))
    inventory = source_inventory(freeze)
    stop1 = json.loads((ROOT / "candidate.preflight_stop.raw.json").read_text(encoding="utf-8"))
    stop1_ok = verify_v1_stop(stop1, inventory)
    errors = []
    if not all(inventory["upstream_source_matches"].values()) or not all(
        inventory[k] for k in ("parts_match", "archive_match", "counts_match")
    ):
        errors.append("frozen archive/source integrity or file inventory failure")
    if not stop1_ok:
        errors.append("T2 preflight STOP was not independently reproduced")
    candidate_path = ROOT / "candidate.v2.raw.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    trace_errors, app, obs, driver, run = validate_trace(candidate, ROOT / "run_v2" / "trace")
    errors.extend(trace_errors)
    if candidate.get("disposition") != "PASS_PROSPECTIVE_CAUSAL_IDS":
        errors.append("candidate-v2 did not reach preregistered PASS")
    result = {
        "schema": "blackstart-prospective-causal-trace-independent-audit-v2",
        "status": "PASS_AUDIT_PROSPECTIVE_CAUSAL_IDS" if not errors else "FAIL_OR_STOP_AUDIT",
        "errors": errors,
        "t2_preflight_stop_independently_verified": stop1_ok,
        "t2b_archive_inventory": inventory,
        "candidate_v2_sha256": sha(candidate_path.read_bytes()),
        "candidate_v2_disposition": candidate.get("disposition"),
        "app_event_count": len([r for r in app if r.get("source") == "app"]),
        "observer_event_count": len([r for r in obs if r.get("source") == "observer"]),
        "driver_record_count": len(driver),
        "neutral_terminal_keymap": run.get("terminal_shift_down") is False,
        "timestamps_used_to_infer_causality": False,
    }
    (ROOT / "audit.v2.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT_PROSPECTIVE_CAUSAL_IDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
