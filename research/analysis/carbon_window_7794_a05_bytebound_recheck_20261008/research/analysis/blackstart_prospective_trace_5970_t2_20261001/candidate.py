#!/usr/bin/env python3
"""One-shot runner and candidate adjudicator for Issue #5970 T2."""
import base64
import hashlib
import io
import json
import lzma
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "run"


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def repo_root():
    for path in ROOT.parents:
        if (path / ".git").exists():
            return path
    raise RuntimeError("repository root not found")


def read_pinned_archive(freeze):
    repo = repo_root()
    parts = []
    for rel, expected in sorted(freeze["archive_parts"].items()):
        path = repo / freeze["archive_path"] / rel
        raw = path.read_bytes()
        if sha256(raw) != expected:
            raise RuntimeError(f"archive part hash mismatch: {rel}")
        parts.append(raw)
    encoded = b"".join(parts)
    archive = base64.b64decode(encoded, validate=True)
    if len(archive) != freeze["archive_bytes"] or sha256(archive) != freeze["archive_sha256"]:
        raise RuntimeError("frozen archive hash/size mismatch")
    expanded = lzma.decompress(archive)
    with tarfile.open(fileobj=io.BytesIO(expanded), mode="r:") as tf:
        members = tf.getmembers()
        if len(members) != freeze["expanded_file_count"]:
            raise RuntimeError("frozen archive member count mismatch")
        out = {}
        for basename, expected in freeze["upstream_sources_sha256"].items():
            matches = [m for m in members if Path(m.name).name == basename and m.isfile()]
            if len(matches) != 1:
                raise RuntimeError(f"expected one archived {basename}, got {len(matches)}")
            data = tf.extractfile(matches[0]).read()
            if sha256(data) != expected:
                raise RuntimeError(f"upstream source hash mismatch: {basename}")
            out[basename] = data
    return out


def classify(actions, app_rows, observer_rows, terminal_shift_down):
    """Fail-closed paired-record predicate. Clocks are deliberately unused."""
    expected = [
        ("KeyPress", "shift-1"),
        ("KeyRelease", "shift-2"),
    ]
    app_events = [r for r in app_rows if r.get("source") == "app"]
    obs_events = [r for r in observer_rows if r.get("source") == "observer"]
    app_seq = [r.get("source_seq") for r in app_events]
    obs_seq = [r.get("source_seq") for r in obs_events]
    if (
        terminal_shift_down is not False
        or len(app_events) != 2
        or len(obs_events) != 2
        or app_seq != sorted(set(app_seq))
        or obs_seq != sorted(set(obs_seq))
    ):
        return "HOLD_INCOMPLETE_OR_NONNEUTRAL"
    for kind, suffix in expected:
        action_rows = [r for r in actions if r.get("actuation_id", "").endswith(suffix)]
        if len(action_rows) != 4:
            return "HOLD_DRIVER_PROTOCOL_INCOMPLETE"
        phases = [r["phase"] for r in action_rows]
        if phases != ["arm_request", "both_armed", "dispatch_request", "dispatch_sync_complete"]:
            return "HOLD_DRIVER_PROTOCOL_INCOMPLETE"
        actuation_id = action_rows[0].get("actuation_id")
        app_ack = [r for r in app_rows if r.get("kind") == "arm_ack" and r.get("actuation_id") == actuation_id]
        obs_ack = [r for r in observer_rows if r.get("kind") == "arm_ack" and r.get("actuation_id") == actuation_id]
        a = [r for r in app_events if r.get("actuation_id") == actuation_id]
        o = [r for r in obs_events if r.get("actuation_id") == actuation_id]
        if len(app_ack) != 1 or len(obs_ack) != 1 or len(a) != 1 or len(o) != 1:
            return "HOLD_INCOMPLETE_OR_DUPLICATE_PROVENANCE"
        if (
            a[0].get("kind") != kind
            or o[0].get("kind") != kind
            or action_rows[2].get("event_kind") != kind
            or a[0].get("keycode") != action_rows[2].get("keycode")
            or o[0].get("keycode") != action_rows[2].get("keycode")
            or a[0].get("keycode") != o[0].get("keycode")
            or a[0].get("x_time") != o[0].get("x_time")
            or a[0].get("causal_parent_ids") != [f"act:{actuation_id}"]
            or o[0].get("causal_parent_ids") != [f"act:{actuation_id}"]
            or a[0].get("event_id") == o[0].get("event_id")
            or o[0].get("epoch") != actuation_id.split(":shift-", 1)[0]
        ):
            return "HOLD_MISMATCHED_CAUSAL_RECORDS"
    return "PASS_PROSPECTIVE_CAUSAL_IDS"


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    for rel, expected in freeze["analysis_sources_sha256"].items():
        raw = (ROOT / rel).read_bytes()
        if sha256(raw) != expected:
            raise SystemExit(f"STOP: frozen analysis source changed: {rel}")
    if RUN_DIR.exists():
        raise SystemExit("STOP: one-shot run directory already exists; do not rerun candidate")
    upstream = read_pinned_archive(freeze)
    RUN_DIR.mkdir()
    instrumented = RUN_DIR / "instrumented"
    instrumented.mkdir()
    shutil.copyfile(ROOT / "instrumented_app.py", instrumented / "app.py")
    shutil.copyfile(ROOT / "instrumented_observer.py", instrumented / "observer.py")
    app_rows = observer_rows = actions = []
    stderr = ""
    try:
        proc = subprocess.run(
            [
                "xvfb-run",
                "-a",
                "-s",
                "-screen 0 1024x768x24",
                sys.executable,
                str(ROOT / "runner.py"),
                "--out",
                str(RUN_DIR / "trace"),
                "--app",
                str(instrumented / "app.py"),
                "--observer",
                str(instrumented / "observer.py"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        stderr = proc.stderr[-4000:]
        run_record = json.loads((RUN_DIR / "trace" / "run.raw.json").read_text(encoding="utf-8"))
        app_rows = [json.loads(line) for line in (RUN_DIR / "trace" / "app_events.jsonl").read_text(encoding="utf-8").splitlines() if line]
        observer_rows = [json.loads(line) for line in (RUN_DIR / "trace" / "observer_events.jsonl").read_text(encoding="utf-8").splitlines() if line]
        actions = [json.loads(line) for line in (RUN_DIR / "trace" / "actions.jsonl").read_text(encoding="utf-8").splitlines() if line]
        disposition = classify(actions, app_rows, observer_rows, run_record.get("terminal_shift_down"))
        if proc.returncode != 0 and disposition.startswith("PASS"):
            disposition = "STOP_RUNNER_NONZERO"
    except Exception as exc:
        run_record = {"status": "STOP", "error": type(exc).__name__, "message": str(exc)}
        disposition = "STOP_INFRASTRUCTURE_OR_RUNNER"
    result = {
        "schema": "blackstart-prospective-causal-trace-candidate-v1",
        "disposition": disposition,
        "runner": run_record,
        "candidate_process_returncode": proc.returncode if "proc" in locals() else None,
        "candidate_stderr_tail": stderr,
        "archive_sha256": freeze["archive_sha256"],
        "archive_verified": True,
        "upstream_source_hashes_verified": {k: sha256(v) for k, v in upstream.items()},
        "app_rows": app_rows,
        "observer_rows": observer_rows,
        "driver_rows": actions,
        "clock_fields_used_for_causal_decision": False,
    }
    (ROOT / "candidate.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "app_events": len([r for r in app_rows if r.get("source")]), "observer_events": len([r for r in observer_rows if r.get("source")]), "candidate_sha256": sha256((ROOT / "candidate.raw.json").read_bytes())}, sort_keys=True))
    return 0 if disposition == "PASS_PROSPECTIVE_CAUSAL_IDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
