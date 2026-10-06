#!/usr/bin/env python3
"""Independent reviewer for the frozen, read-only Issue #7709 T1 audit."""
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text())
R = json.loads((ROOT / "RESULT_V2.json").read_text())
OUT = ROOT / "AUDIT_V2.json"


def pinned(path):
    data = subprocess.check_output(["git", "cat-file", "blob", F["sources"][path]["git_blob"]])
    assert hashlib.sha256(data).hexdigest() == F["sources"][path]["sha256"], path
    return data


def main():
    assert not OUT.exists(), "STOP_AUDIT_OUTPUT_EXISTS"
    assert hashlib.sha256((ROOT / "candidate.py").read_bytes()).hexdigest() == F["candidate_sha256"]
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == F["auditor_sha256"]
    assert R["base_commit"] == F["base_commit"]
    manifest = json.loads(pinned("runtime/results/public-six-task-comparison-04/manifest.json"))
    archive = pinned("runtime/results/public-six-task-comparison-04/raw.tar.gz")
    assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"]
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
        files = {m.name: m for m in tf.getmembers() if m.isfile()}
        expected = {f["path"]: f for f in manifest["files"]}
        assert set(files) == set(expected) and len(files) == 1051
        for name, meta in expected.items():
            data = tf.extractfile(files[name]).read()
            assert len(data) == meta["bytes"] and hashlib.sha256(data).hexdigest() == meta["sha256"], name
        metrics = json.loads(tf.extractfile(files["current/metrics.json"]).read())
        direct = json.loads(tf.extractfile(files["current/direct/goal.json"]).read())
        guarded = json.loads(tf.extractfile(files["current/guarded/goal.json"]).read())
        rows = metrics["tasks"]
        assert len(rows) == 12
        assert all(sum(r["route"] == route for r in rows) == 6 for route in ("direct", "guarded"))
        assert all(sorted(r["task"] for r in rows if r["route"] == route) == list(range(1, 7)) for route in ("direct", "guarded"))
        assert all(r["exact_once"] for r in rows)
        assert [r["route"] for r in rows] == ["direct"] * 6 + ["guarded"] * 6
        assert direct["seed"] == guarded["seed"] == 992004
        assert len([r for r in rows if not r.get("visual_completion_cue_in_save_image", False)]) == 1
        assert all(isinstance(r.get("sdk_selected_calls_ms"), (int, float)) and isinstance(r.get("sdk_input_to_independent_submission_ms"), (int, float)) for r in rows)
        host_checks = {}
        for route in ("direct", "guarded"):
            events = [json.loads(x) for x in tf.extractfile(files[f"current/{route}/host/host-events.jsonl"]).read().splitlines() if x]
            host_checks[route] = {"rows": len(events), "strict_sequence": all(a["sequence"] < b["sequence"] for a, b in zip(events, events[1:])),
                                  "monotonic": all(a["host_monotonic_ms"] <= b["host_monotonic_ms"] for a, b in zip(events, events[1:]))}
            assert host_checks[route]["strict_sequence"] and host_checks[route]["monotonic"]
    assert R["public_pair"]["run_identity_present"] is False
    assert R["public_pair"]["eligible_independent_pairs"] == 1
    transport_checks = []
    for comparison, manifest_path in F["transport_comparisons"]:
        rows = json.loads(pinned(comparison))
        m = json.loads(pinned(manifest_path))
        assert len(rows) == 3 and all(r["attempt_count"] == 1 for r in rows)
        assert m["model_calls"] == 0 and m["input_actions"] == 0
        transport_checks.append({"comparison": comparison, "routes": 3, "attempts_per_route": 1, "model_calls": 0, "input_actions": 0, "eligible_for_task_route_pool": False})
    stop = json.loads(pinned(F["route_stop_result"]))
    assert stop["decision"].startswith("STOP") and R["route_preflight_stop"]["route_calls"] == 0
    assert R["route_preflight_stop"]["status"] == stop["decision"]
    audit = {"format": "issue7709-t1-independent-audit-v1", "base_commit": F["base_commit"],
             "all_1051_archive_member_hashes_pass": True, "public_task_rows": 12,
             "tasks_per_route": 6, "exact_once_rows": 12, "route_order": "direct_then_guarded_fixed",
             "independent_prepared_pairs": 1, "missing_visual_completion_cues": 1,
             "run_identity_fields_present": False, "host_event_checks": host_checks,
             "transport_experiments": transport_checks, "route_stop_status": stop["decision"],
             "disposition": "HOLD_TOO_FEW_INDEPENDENT_RUNS", "auditor_pass": True}
    OUT.write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"auditor_pass": True, "independent_pairs": 1, "disposition": audit["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
