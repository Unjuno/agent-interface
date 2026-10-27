"""Freeze P10 source hashes after its packet is committed and before calls."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FILES = (
    "README.md", "PREREGISTRATION.md", "CONDITIONS.json", "RUN-ORDER.txt",
    "audit_p10.py", "export_p10.py", "fake_factory.py", "privacy_redact.py",
    "run_arm.py", "test_fake_factory.py", "test_packet_tools.py",
    "test_privacy_redact.py", "test_standard_caller.py", "freeze_p10.py",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def freeze():
    target = ROOT / "PRELAUNCH.json"
    if target.exists():
        raise FileExistsError("P10 prelaunch record already exists; preserve it")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          check=True, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                            check=True, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("commit the complete packet and ensure a clean worktree before freeze")
    conditions = json.loads((ROOT / "CONDITIONS.json").read_text(encoding="utf-8"))
    hashes = {name: sha((ROOT / name).read_bytes()) for name in FILES}
    record = {
        "schema": "agent-interface/appserver-visual-grounding-p10-prelaunch-v1",
        "classification": "FROZEN_BEFORE_PROVIDER_CALL",
        "freeze_input_commit": head,
        "runtime_source_commit": conditions["runtime_source_commit"],
        "runner_source_sha256": hashes,
        "conditions_sha256": sha((ROOT / "CONDITIONS.json").read_bytes()),
        "trial_count": conditions["trial_count"],
        "provider_turn_limit": conditions["provider_turn_limit"],
        "model": conditions["model"],
        "effort": conditions["effort"],
        "retry_count": conditions["retry_count"],
        "scope": "synthetic Fake X only; no WSLc, Docker, physical input, live GUI, or MAP01",
    }
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return record


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2, sort_keys=True))
