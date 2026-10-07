#!/usr/bin/env python3
"""Read-only T1 feasibility reconstruction from frozen main Git blobs."""
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text())
OUT = ROOT / "RESULT_V2.json"


def blob(path):
    raw = subprocess.check_output(["git", "show", f"{F['base_commit']}:{path}"])
    pin = F["sources"][path]
    actual_blob = subprocess.check_output(["git", "rev-parse", f"{F['base_commit']}:{path}"]).decode().strip()
    if hashlib.sha256(raw).hexdigest() != pin["sha256"] or actual_blob != pin["git_blob"]:
        raise SystemExit("STOP_SOURCE_PIN:" + path)
    return raw


def keys_contain(value, wanted):
    if isinstance(value, dict):
        return any(key in wanted or keys_contain(child, wanted) for key, child in value.items())
    if isinstance(value, list):
        return any(keys_contain(child, wanted) for child in value)
    return False


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    readme = blob(F["public_readme"]).decode()
    outer = json.loads(blob(F["public_manifest"]))
    archive = blob(F["public_archive"])
    outer_files = {item["path"]: item for item in outer["files"]}
    if hashlib.sha256(archive).hexdigest() != outer["archive_sha256"]:
        raise SystemExit("STOP_ARCHIVE_SHA")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
        members = {member.name: member for member in tf.getmembers() if member.isfile()}
        if len(members) != len(outer_files) or set(members) != set(outer_files):
            raise SystemExit("STOP_ARCHIVE_MEMBER_SET")
        archived = {}
        for name, receipt in outer_files.items():
            raw = tf.extractfile(members[name]).read()
            if len(raw) != receipt["bytes"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
                raise SystemExit("STOP_ARCHIVE_MEMBER_HASH:" + name)
            archived[name] = raw
    metrics = json.loads(archived["current/metrics.json"])
    direct_goal = json.loads(archived["current/direct/goal.json"])
    guarded_goal = json.loads(archived["current/guarded/goal.json"])
    route_rows = metrics["tasks"]
    counts = {route: sum(row["route"] == route for row in route_rows) for route in ("direct", "guarded")}
    task_ids = {route: sorted(row["task"] for row in route_rows if row["route"] == route)
                for route in ("direct", "guarded")}
    missing_visual = [{"route": row["route"], "task": row["task"]}
                      for row in route_rows if not row.get("visual_completion_cue_in_save_image", False)]
    order = [row["route"] for row in route_rows]
    run_identity_fields = {"run_id", "session_id", "prepared_run_id", "block_id"}
    has_run_identity = keys_contain(metrics, run_identity_fields) or keys_contain(direct_goal, run_identity_fields) or keys_contain(guarded_goal, run_identity_fields)
    host_events = {}
    for route in ("direct", "guarded"):
        events = [json.loads(line) for line in archived[f"current/{route}/host/host-events.jsonl"].splitlines() if line]
        host_events[route] = {"rows": len(events),
                              "sequence_strict": all(a["sequence"] < b["sequence"] for a, b in zip(events, events[1:])),
                              "monotonic_non_decreasing": all(a["host_monotonic_ms"] <= b["host_monotonic_ms"] for a, b in zip(events, events[1:])),
                              "run_identity_present": keys_contain(events, run_identity_fields)}
    transport, transport_paths = [], F["transport_comparisons"]
    for comparison_path, manifest_path in transport_paths:
        rows = json.loads(blob(comparison_path))
        manifest = json.loads(blob(manifest_path))
        transport.append({"comparison": comparison_path, "experiment_commit": manifest.get("experiment_commit"),
                          "source_commit": manifest.get("source_commit"),
                          "image_id": manifest.get("image_id"), "model_calls": manifest.get("model_calls"),
                          "input_actions": manifest.get("input_actions"),
                          "routes": [{"route": row["route"], "attempt_count": row["attempt_count"],
                                      "elapsed_ns": row["elapsed_ns"], "start_ns": row["call_started_monotonic_ns"],
                                      "end_ns": row["call_ended_monotonic_ns"]} for row in rows]})
    stop_report = blob(F["route_stop_report"]).decode()
    stop_result = json.loads(blob(F["route_stop_result"]))
    public_pair = {"route_task_rows": len(route_rows), "counts": counts, "task_ids": task_ids,
                   "route_order": order, "seed_by_route": {"direct": direct_goal["seed"], "guarded": guarded_goal["seed"]},
                   "run_identity_present": has_run_identity, "host_events": host_events,
                   "task_rows_all_exact_once": all(row["exact_once"] for row in route_rows),
                   "task_rows_with_required_timing": all(isinstance(row.get("sdk_selected_calls_ms"), (float, int)) and
                                                          isinstance(row.get("sdk_input_to_independent_submission_ms"), (float, int))
                                                          for row in route_rows),
                   "missing_visual_completion_cues": missing_visual,
                   "single_serial_pair_explicit": "one exploratory serial pair" in readme,
                   "model_visible_protocol_in_readme": "gpt-6.1-sol" in readme,
                   "eligible_independent_pairs": 1}
    result = {"format": "issue7709-t1-feasibility-v2", "classification": "read-only retained-evidence audit",
              "base_commit": F["base_commit"], "public_pair": public_pair,
              "transport_only_experiments": transport,
              "route_preflight_stop": {"status": stop_result.get("decision"), "model_route_gate": stop_result.get("model_route_gate"), "route_calls": 0,
                                        "model_calls": 0, "stop_document_contains_no_call": "No nonce was generated and no model task or route observation was called." in stop_report},
              "qualifying_independent_pairs": 1 if public_pair["eligible_independent_pairs"] == 1 else 0,
              "disposition": "HOLD_TOO_FEW_INDEPENDENT_RUNS"}
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"public_pair": public_pair, "transport_only_count": len(transport),
                      "route_preflight_stop": result["route_preflight_stop"],
                      "disposition": result["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
