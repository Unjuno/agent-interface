"""One-shot host gate and candidate/auditor dispatcher for Allocation 06."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import launch_contract


ALLOCATION = "MAP01-OWNER-KEYUP-BRACKET-5156-20261001-06"
FROZEN_MAIN = "9fc98feb617c26fe1baa7ecc4decd43b69df8601"
WINDOW_START = datetime(2026, 9, 30, 17, 40, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 9, 30, 17, 55, tzinfo=timezone.utc)
CONTEXT = "desktop-linux"
IMAGE_ID = "sha256:f41b02e63fc3964f9bb831167ae42bce6d6ffa50fbda122d22deaa39736637bb"
PLATFORM = "linux/amd64"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results" / "formal-01"


def gate_errors(snapshot, now, results_dir=RESULTS):
    errors = []
    if now.tzinfo is None or now.utcoffset() is None:
        errors.append("clock must be timezone-aware UTC")
    elif not WINDOW_START <= now.astimezone(timezone.utc) < WINDOW_END:
        errors.append("outside exact assigned UTC window")
    elif (WINDOW_END - now.astimezone(timezone.utc)).total_seconds() < 480:
        errors.append("insufficient window remains for bounded runner and audit")
    if snapshot.get("main_sha") != FROZEN_MAIN:
        errors.append("current main differs from frozen main")
    if snapshot.get("docker_context") != CONTEXT:
        errors.append("Docker context mismatch")
    if snapshot.get("running_containers"):
        errors.append("unrelated/running Docker container present")
    if snapshot.get("image_id") != IMAGE_ID:
        errors.append("cached image digest mismatch or unavailable")
    if snapshot.get("image_platform") != PLATFORM:
        errors.append("cached image platform mismatch")
    if snapshot.get("queue_reconciled") is not True:
        errors.append("current shared queue was not reconciled")
    if snapshot.get("queue_conflict") is not False:
        errors.append("shared queue conflict or unknown status")
    if any((results_dir / name).exists() for name in ("START.json", "STOP.json", "EXECUTION.json")):
        errors.append("allocation already has a terminal/start marker; retry forbidden")
    return errors


def run_one_shot(snapshot, now, run_candidate, run_auditor, results_dir=RESULTS):
    """Gate once, invoke candidate once, and audit only a zero-exit candidate."""
    errors = gate_errors(snapshot, now, results_dir)
    if errors:
        if any((results_dir / name).exists()
               for name in ("START.json", "STOP.json", "EXECUTION.json")):
            return 2
        stop = {
            "allocation": ALLOCATION,
            "status": "STOP_BEFORE_RUNNER",
            "checked_at_utc": now.astimezone(timezone.utc).isoformat(),
            "snapshot": snapshot,
            "errors": errors,
            "candidate_invocations": 0,
            "audit_invocations": 0,
            "retry": False,
        }
        (results_dir / "STOP.json").write_text(json.dumps(stop, indent=2, sort_keys=True) + "\n",
                                                encoding="utf-8")
        return 2

    start = {
        "allocation": ALLOCATION,
        "started_at_utc": now.astimezone(timezone.utc).isoformat(),
        "frozen_main": FROZEN_MAIN,
        "image_id": IMAGE_ID,
        "platform": PLATFORM,
        "window_start_utc": WINDOW_START.isoformat(),
        "window_end_utc": WINDOW_END.isoformat(),
        "retry": False,
    }
    (results_dir / "START.json").write_text(json.dumps(start, indent=2, sort_keys=True) + "\n",
                                             encoding="utf-8")
    try:
        candidate = run_candidate()
    except Exception as exc:
        candidate = {"returncode": None, "stdout": "",
                     "stderr": f"{type(exc).__name__}: {exc}"}
    (results_dir / "runner.stdout.txt").write_text(candidate.get("stdout", ""), encoding="utf-8")
    (results_dir / "runner.stderr.txt").write_text(candidate.get("stderr", ""), encoding="utf-8")
    candidate_code = candidate.get("returncode")
    audit = None
    if candidate_code == 0:
        try:
            audit = run_auditor()
        except Exception as exc:
            audit = {"returncode": None, "stdout": "",
                     "stderr": f"{type(exc).__name__}: {exc}"}
        (results_dir / "auditor.stdout.txt").write_text(audit.get("stdout", ""), encoding="utf-8")
        (results_dir / "auditor.stderr.txt").write_text(audit.get("stderr", ""), encoding="utf-8")

    raw_path = results_dir / "raw.jsonl"
    execution = {
        **start,
        "candidate_returncode": candidate_code,
        "candidate_invocations": 1,
        "audit_returncode": audit.get("returncode") if audit is not None else None,
        "audit_invocations": 1 if audit is not None else 0,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest() if raw_path.is_file() else None,
        "disposition": ("AUDIT_COMPLETE" if audit is not None and audit.get("returncode") == 0
                        else "AUDIT_FAILED" if audit is not None
                        else "RUNNER_FAILED_NO_AUDIT"),
        "retry": False,
    }
    (results_dir / "EXECUTION.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n",
                                                  encoding="utf-8")
    if candidate_code != 0:
        return 1
    return 0 if audit is not None and audit.get("returncode") == 0 else 1


def _checked(args, cwd=None, timeout=15):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"preflight command failed ({result.returncode}): {args[0]} {args[1:]}")
    return result.stdout.strip()


def collect_snapshot(queue_reconciled, queue_conflict):
    _checked(["git", "fetch", "origin", "main"], cwd=REPO, timeout=30)
    main_sha = _checked(["git", "rev-parse", "origin/main"], cwd=REPO)
    context = _checked(["docker", "context", "show"])
    containers = _checked(["docker", "--context", CONTEXT, "ps", "--no-trunc", "-q"])
    image_data = _checked([
        "docker", "--context", CONTEXT, "image", "inspect", launch_contract._IMAGE_REF,
        "--format", "{{.Id}}|{{.Os}}/{{.Architecture}}",
    ])
    image_id, image_platform = image_data.split("|", 1)
    return {
        "main_sha": main_sha,
        "docker_context": context,
        "running_containers": [item for item in containers.splitlines() if item.strip()],
        "image_id": image_id,
        "image_platform": image_platform,
        "queue_reconciled": queue_reconciled,
        "queue_conflict": queue_conflict,
    }


def _invoke(argv, timeout):
    result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=timeout, check=False)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-reconciled", action="store_true")
    parser.add_argument("--queue-conflict", action="store_true")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if not WINDOW_START <= now < WINDOW_END:
        snapshot = {"queue_reconciled": args.queue_reconciled, "queue_conflict": args.queue_conflict}
        return run_one_shot(snapshot, now, lambda: {}, lambda: {})
    try:
        snapshot = collect_snapshot(args.queue_reconciled, args.queue_conflict)
    except Exception as exc:
        snapshot = {"queue_reconciled": args.queue_reconciled, "queue_conflict": args.queue_conflict,
                    "preflight_error": f"{type(exc).__name__}: {exc}"}
        return run_one_shot(snapshot, datetime.now(timezone.utc), lambda: {}, lambda: {})

    now = datetime.now(timezone.utc)
    candidate_argv = launch_contract.build_command(HERE, RESULTS, launch_contract._IMAGE_REF, PLATFORM)
    auditor_argv = launch_contract.build_audit_command(HERE, RESULTS, launch_contract._IMAGE_REF, PLATFORM)
    return run_one_shot(
        snapshot, now,
        lambda: _invoke(candidate_argv, timeout=325),
        lambda: _invoke(auditor_argv, timeout=145),
    )


if __name__ == "__main__":
    raise SystemExit(main())
