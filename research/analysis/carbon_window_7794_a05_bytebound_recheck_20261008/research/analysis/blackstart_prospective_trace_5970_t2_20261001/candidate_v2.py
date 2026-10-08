#!/usr/bin/env python3
"""One-shot successor candidate; fixes only regular-file inventory counting."""
import base64
import hashlib
import importlib.util
import io
import json
import lzma
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "run_v2"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_original_gate():
    spec = importlib.util.spec_from_file_location("t2_candidate_v1", ROOT / "candidate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify


def root_path():
    return next(path for path in ROOT.parents if (path / ".git").exists())


def verify_archive(freeze):
    repo = root_path()
    encoded = bytearray()
    for rel, expected in sorted(freeze["archive_parts"].items()):
        raw = (repo / freeze["archive_path"] / rel).read_bytes()
        if digest(raw) != expected:
            raise RuntimeError(f"archive part hash mismatch: {rel}")
        encoded.extend(raw)
    archive = base64.b64decode(bytes(encoded), validate=True)
    if len(archive) != freeze["archive_bytes"] or digest(archive) != freeze["archive_sha256"]:
        raise RuntimeError("archive digest or byte count mismatch")
    expanded = lzma.decompress(archive)
    with tarfile.open(fileobj=io.BytesIO(expanded), mode="r:") as tf:
        members = tf.getmembers()
        regular = [m for m in members if m.isfile()]
        if len(members) != freeze["tar_member_count"] or len(regular) != freeze["expanded_file_count"]:
            raise RuntimeError(f"archive inventory mismatch: total={len(members)} files={len(regular)}")
        sources = {}
        for basename, expected in freeze["upstream_sources_sha256"].items():
            matches = [m for m in regular if Path(m.name).name == basename]
            if len(matches) != 1:
                raise RuntimeError(f"expected one upstream source {basename}")
            contents = tf.extractfile(matches[0]).read()
            if digest(contents) != expected:
                raise RuntimeError(f"upstream source hash mismatch: {basename}")
            sources[basename] = digest(contents)
    return {"archive_sha256": digest(archive), "tar_member_count": len(members), "regular_file_count": len(regular), "source_hashes": sources}


def records(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main():
    freeze = json.loads((ROOT / "FREEZE_V2.json").read_text(encoding="utf-8"))
    for rel, expected in freeze["analysis_sources_sha256"].items():
        if digest((ROOT / rel).read_bytes()) != expected:
            raise SystemExit(f"STOP: T2b frozen source changed: {rel}")
    stop1 = json.loads((ROOT / "candidate.preflight_stop.raw.json").read_text(encoding="utf-8"))
    if stop1.get("status") != "STOP_CANDIDATE_PREFLIGHT_INVENTORY_PREDICATE" or stop1.get("x_test_events_dispatched") != 0:
        raise SystemExit("STOP: T2 preflight failure record is missing or inconsistent")
    if RUN_DIR.exists():
        raise SystemExit("STOP: candidate-v2 run directory already exists; do not rerun")
    archive_info = verify_archive(freeze)
    classify = load_original_gate()
    RUN_DIR.mkdir()
    instruments = RUN_DIR / "instrumented"
    instruments.mkdir()
    shutil.copyfile(ROOT / "instrumented_app.py", instruments / "app.py")
    shutil.copyfile(ROOT / "instrumented_observer.py", instruments / "observer.py")
    disposition = "STOP_INFRASTRUCTURE_OR_RUNNER"
    stderr = ""
    run_record = {"status": "STOP"}
    app_rows = obs_rows = driver_rows = []
    proc = None
    try:
        proc = subprocess.run(
            [
                "xvfb-run", "-a", "-s", "-screen 0 1024x768x24", sys.executable,
                str(ROOT / "runner.py"), "--out", str(RUN_DIR / "trace"),
                "--app", str(instruments / "app.py"), "--observer", str(instruments / "observer.py"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        stderr = proc.stderr[-4000:]
        trace = RUN_DIR / "trace"
        run_record = json.loads((trace / "run.raw.json").read_text(encoding="utf-8"))
        app_rows = records(trace / "app_events.jsonl")
        obs_rows = records(trace / "observer_events.jsonl")
        driver_rows = records(trace / "actions.jsonl")
        disposition = classify(driver_rows, app_rows, obs_rows, run_record.get("terminal_shift_down"))
        if proc.returncode != 0 and disposition.startswith("PASS"):
            disposition = "STOP_RUNNER_NONZERO"
    except Exception as exc:
        run_record = {"status": "STOP", "error": type(exc).__name__, "message": str(exc)}
    result = {
        "schema": "blackstart-prospective-causal-trace-candidate-v2",
        "disposition": disposition,
        "preflight_stop_v1_preserved": True,
        "archive_inventory": archive_info,
        "runner": run_record,
        "runner_returncode": proc.returncode if proc else None,
        "runner_stderr_tail": stderr,
        "app_rows": app_rows,
        "observer_rows": obs_rows,
        "driver_rows": driver_rows,
        "clock_fields_used_for_causal_decision": False,
    }
    output = ROOT / "candidate.v2.raw.json"
    if output.exists():
        raise SystemExit("STOP: candidate-v2 raw result already exists")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "archive_inventory": archive_info, "app_events": len([r for r in app_rows if r.get("source")]), "observer_events": len([r for r in obs_rows if r.get("source")]), "result_sha256": digest(output.read_bytes())}, sort_keys=True))
    return 0 if disposition == "PASS_PROSPECTIVE_CAUSAL_IDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
