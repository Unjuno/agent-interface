"""Freeze P09 source, conditions and runtime commit before provider use."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONDITIONS = json.loads((ROOT / "CONDITIONS.json").read_text(encoding="utf-8"))
FROZEN = ("CONDITIONS.json", "PREREGISTRATION.md", "fake_factory.py",
          "run_arm.py", "audit_p09.py", "privacy_redact.py",
          "test_fake_factory.py", "test_standard_caller.py", "freeze_p09.py")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def freeze():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True, check=True).stdout.strip()
    parent = subprocess.run(["git", "rev-parse", "HEAD^"], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout
    if status:
        raise RuntimeError("P09 prelaunch freeze requires a clean committed tree")
    if parent != CONDITIONS["runtime_source_commit"]:
        raise RuntimeError("P09 runtime source is not the preregistered parent")
    if (ROOT / "run").exists():
        raise FileExistsError("immutable P09 run directory already exists")
    rows = {name: sha((ROOT / name).read_bytes()) for name in FROZEN}
    record = {
        "schema": "agent-interface/appserver-visual-grounding-p09-prelaunch-v1",
        "classification": "FROZEN_BEFORE_PROVIDER_CALL",
        "runtime_source_commit": parent,
        "runner_commit": head,
        "model": CONDITIONS["model"],
        "effort": CONDITIONS["effort"],
        "trial_count": CONDITIONS["trial_count"],
        "retry_count": CONDITIONS["retry_count"],
        "source_sha256": rows,
    }
    (ROOT / "PRELAUNCH.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    return record


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2, sort_keys=True))
