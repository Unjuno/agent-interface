#!/usr/bin/env python3
"""Build the A10 freeze before the one-shot candidate run."""
import hashlib
import json
import subprocess
from pathlib import Path

PACKAGE = Path("research/analysis/chromium_temporal_focus_payload_1998_t0_a10_20261009")
FRAME_ROOT = Path("research/observation_gating/results/baseline-screen-02/chromium-1101-O0")
PACKAGE_FILES = [
    "PLAN.md", "README.md", "ENVIRONMENT.md", "PREFLIGHT.md", "manifest.json",
    "run_formal.sh", "freeze_sources.py", "check_frozen.py", "auditor.py",
    "construction/README.md", "construction/test_construction.py",
    "construction/attempt-01/exit", "construction/attempt-01/stdout.json", "construction/attempt-01/stderr.txt",
    "construction/attempt-02/exit", "construction/attempt-02/stdout.json", "construction/attempt-02/stderr.txt",
    "construction/attempt-03/exit", "construction/attempt-03/stdout.json", "construction/attempt-03/stderr.txt",
    "construction/attempt-04/exit", "construction/attempt-04/stdout.json", "construction/attempt-04/stderr.txt",
    "preflight/container_smoke.json", "src/candidate.js",
]
INPUT_FILES = [
    FRAME_ROOT / "actions.json", FRAME_ROOT / "observations.jsonl",
    FRAME_ROOT / "result.json", FRAME_ROOT / "submitted.txt",
    FRAME_ROOT / "frames/3ef7a4415c4fe589ede0304e00dae19edeefc887e6e3ee73abd24978cb140307.png",
    FRAME_ROOT / "frames/36563401256d29715e9ef9b1ceadd4f0764b78712dc9b62d5578283e35e40d06.png",
    FRAME_ROOT / "frames/8f9f1351d7c90cb9e6579e66ccc9db33bbe95cca6d89504972ce5d52d91d4d34.png",
    Path("research/analysis/chromium_postsubmit_task_cue_1998_t0_a09_20261009/POSTHOC_DIAGNOSTIC.md"),
    Path("research/analysis/chromium_postsubmit_task_cue_1998_t0_a09_20261009/RESULT.json"),
    Path("research/analysis/chromium_postsubmit_task_cue_1998_t0_a09_20261009/FREEZE.json"),
    Path("research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/REPORT.md"),
    Path("research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/design.json"),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (PACKAGE / "results").exists():
        raise SystemExit("formal results path exists; refusing to create/replace freeze")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    main_sha = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
    files = [PACKAGE / p for p in PACKAGE_FILES] + INPUT_FILES
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise SystemExit("missing frozen inputs: " + ", ".join(missing))
    frozen = {str(p): digest(p) for p in files}
    manifest = json.loads((PACKAGE / "manifest.json").read_text())
    freeze = {
        "allocation": "LABEL-CONTROL-AMBIGUITY-1998-T0-A10-20261009",
        "issue": "https://github.com/Unjuno/agent-interface/issues/1998",
        "status_at_freeze": "FORMAL_NOT_STARTED",
        "source_anchor_before_freeze": head,
        "current_main_sha_at_freeze": main_sha,
        "parent_work": "A09 branch head; A09 is consumed and unchanged",
        "roi": manifest["roi"],
        "frames": manifest["frames"],
        "candidate_runtime": {
            "engine": "OrbStack Docker Engine",
            "docker_client": "29.5.2",
            "docker_server": "29.4.0",
            "image": "node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80",
            "platform": "linux/arm64",
            "node": "v26.10.0",
            "pull_policy": "never",
            "network": "none",
            "rootfs": "read-only",
            "capabilities": "all dropped",
            "uid_gid": "1000:1000",
            "cpu_limit": 1,
            "memory_limit_bytes": 268435456,
            "pids_limit": 32,
            "tmpfs_bytes": 16777216,
        },
        "auditor_runtime": {
            "host": "macOS 27.0.1 arm64",
            "python": "3.14.5",
            "libraries": "Python standard library only",
            "network": "sandbox-exec denied",
        },
        "formal_invocations_at_freeze": {"candidate": 0, "auditor": 0, "retries": 0},
        "formal_results_directory_exists_at_freeze": False,
        "frozen_inputs_sha256": frozen,
    }
    (PACKAGE / "FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"freeze_sha256": digest(PACKAGE / "FREEZE.json"), "files": len(frozen),
                      "source_anchor": head, "main_sha": main_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
