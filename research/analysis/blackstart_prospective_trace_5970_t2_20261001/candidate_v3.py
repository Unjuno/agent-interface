#!/usr/bin/env python3
"""One-shot T2c candidate with corrected Tk event-log location."""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "run_v3"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main():
    freeze = json.loads((ROOT / "FREEZE_V3.json").read_text(encoding="utf-8"))
    for rel, expected in freeze["analysis_sources_sha256"].items():
        if digest((ROOT / rel).read_bytes()) != expected:
            raise SystemExit(f"STOP: T2c frozen source changed: {rel}")
    for rel, expected in freeze["prior_artifacts_sha256"].items():
        if digest((ROOT / rel).read_bytes()) != expected:
            raise SystemExit(f"STOP: preserved prior attempt changed: {rel}")
    if RUN_DIR.exists() or (ROOT / "candidate.v3.raw.json").exists():
        raise SystemExit("STOP: T2c one-shot output already exists; do not rerun")
    prior = json.loads((ROOT / "candidate.v2.raw.json").read_text(encoding="utf-8"))
    prior_actions = jsonl(ROOT / "run_v2" / "trace" / "actions.jsonl")
    prior_app_nested = jsonl(ROOT / "run_v2" / "trace" / "tk" / "app_events.jsonl")
    prior_obs = jsonl(ROOT / "run_v2" / "trace" / "observer_events.jsonl")
    prior_stop_verified = (
        prior.get("runner", {}).get("status") == "STOP"
        and not any(r.get("phase") == "dispatch_request" for r in prior_actions)
        and not any(r.get("source") == "app" for r in prior_app_nested)
        and not any(r.get("source") == "observer" for r in prior_obs)
        and any(r.get("kind") == "arm_ack" for r in prior_app_nested)
        and any(r.get("kind") == "arm_ack" for r in prior_obs)
    )
    if not prior_stop_verified:
        raise SystemExit("STOP: prior no-dispatch outcome is not confirmed")
    helper = load_module("t2b_candidate", "candidate_v2.py")
    gate = helper.load_original_gate()
    inventory = helper.verify_archive(freeze)
    RUN_DIR.mkdir()
    instruments = RUN_DIR / "instrumented"
    instruments.mkdir()
    shutil.copyfile(ROOT / "instrumented_app.py", instruments / "app.py")
    shutil.copyfile(ROOT / "instrumented_observer.py", instruments / "observer.py")
    disposition = "STOP_INFRASTRUCTURE_OR_RUNNER"
    stderr = ""
    proc = None
    run = {"status": "STOP"}
    app = observer = driver = []
    try:
        proc = subprocess.run(
            ["xvfb-run", "-a", "-s", "-screen 0 1024x768x24", sys.executable,
             str(ROOT / "runner_v3.py"), "--out", str(RUN_DIR / "trace"),
             "--app", str(instruments / "app.py"), "--observer", str(instruments / "observer.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        stderr = proc.stderr[-4000:]
        trace = RUN_DIR / "trace"
        run = json.loads((trace / "run.raw.json").read_text(encoding="utf-8"))
        app = jsonl(trace / "tk" / "app_events.jsonl")
        observer = jsonl(trace / "observer_events.jsonl")
        driver = jsonl(trace / "actions.jsonl")
        disposition = gate(driver, app, observer, run.get("terminal_shift_down"))
        if proc.returncode != 0 and disposition.startswith("PASS"):
            disposition = "STOP_RUNNER_NONZERO"
    except Exception as exc:
        run = {"status": "STOP", "error": type(exc).__name__, "message": str(exc)}
    result = {
        "schema": "blackstart-prospective-causal-trace-candidate-v3",
        "disposition": disposition,
        "prior_t2b_no_dispatch_stop_verified": prior_stop_verified,
        "archive_inventory": inventory,
        "runner": run,
        "runner_returncode": proc.returncode if proc else None,
        "runner_stderr_tail": stderr,
        "app_rows": app,
        "observer_rows": observer,
        "driver_rows": driver,
        "clock_fields_used_for_causal_decision": False,
    }
    output = ROOT / "candidate.v3.raw.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "prior_t2b_no_dispatch_stop_verified": prior_stop_verified, "app_events": len([r for r in app if r.get("source") == "app"]), "observer_events": len([r for r in observer if r.get("source") == "observer"]), "result_sha256": digest(output.read_bytes())}, sort_keys=True))
    return 0 if disposition == "PASS_PROSPECTIVE_CAUSAL_IDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
