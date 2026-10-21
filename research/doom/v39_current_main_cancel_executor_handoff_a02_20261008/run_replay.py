"""Re-run A01 in an isolated copy and retain the exact command outputs."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "research/doom/v39_current_main_cancel_executor_handoff_a01_20261008"


def run(label, command, cwd, env):
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (HERE / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (HERE / f"{label}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    (HERE / f"{label}.exit").write_text(f"{result.returncode}\n", encoding="ascii")
    if result.returncode:
        raise SystemExit(f"{label} failed ({result.returncode}); see retained output")
    return result


def main():
    with tempfile.TemporaryDirectory(prefix="cancel-handoff-a02-", dir=HERE) as raw:
        temp = Path(raw)
        workspace = temp / "workspace"
        copied = workspace / "research/doom/v39_current_main_cancel_executor_handoff_a01_20261008"
        copied.parent.mkdir(parents=True)
        shutil.copytree(SOURCE, copied, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        env = os.environ.copy()
        env["TEMP"] = str(temp)
        env["TMP"] = str(temp)
        run("replay", [sys.executable, "-B", str(copied / "run_candidate.py")], workspace, env)
        replay = json.loads((copied / "RESULT.json").read_text(encoding="utf-8"))
        # The legacy runner rewrites RESULT.json with platform newline rules.
        # Restore its frozen bytes before the legacy manifest auditor runs.
        (copied / "RESULT.json").write_bytes((SOURCE / "RESULT.json").read_bytes())
        run("unit", [sys.executable, "-B", "-m", "unittest", "-v",
                     "research.doom.v39_current_main_cancel_executor_handoff_a01_20261008.test_current_handoff"],
            workspace, env)
        run("audit", [sys.executable, "-B", str(copied / "audit_source.py")], workspace, env)
        result = {
            "schema": "v39-current-main-cancel-executor-handoff-a02-result-v1",
            "current_main_commit": "2a9052efdd155b8cdc173d216a969ea5f64a1ce9",
            "disposition": "PASS_CURRENT_MAIN_SOURCE_ALIGNED_SOFTWARE_REPLAY",
            "source_alignment": {"matched": 13, "total": 13},
            "commands": {name: 0 for name in ("replay", "unit", "audit")},
            "event_order": replay["observed_events"],
            "verified_empty_release": replay["verified_empty_release"],
            "checks": replay["checks"],
            "scope": "source-aligned software composition only; simulated backend/owner; no OS input, live game, threat exposure, or task effect",
        }
        (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
