from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
IMAGE = "python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = HERE / "SOURCE" / "bridge_a04.py"
    scenario = HERE / "scenario.json"
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    freeze = {
        "schema": "map01-v39-perkey-bridge-a05-freeze-v1",
        "run_id": "MAP01-V39-PERKEY-BRIDGE-A05-OUT-OF-ORDER-20261005",
        "base_commit": git_head,
        "prior_main_commit": "dccf55e264f434ca27f2948fe53be09919047819",
        "image": IMAGE,
        "hypothesis": "A04 preserves each actuation's original program/step context when two distinct key cleanup records arrive in reverse admission order; a last-context bridge misattributes the earlier admission.",
        "test": "One candidate process; two distinct key acts and contexts; owner cleanup order act-b then act-a; compare frozen A04 output with explicit last-context baseline.",
        "candidate_command": "python3 run_candidate.py --out /results/a05",
        "container_mounts": {"source": "/src:ro", "output": "/results:rw"},
        "decision": "PASS only if baseline misattributes at least one release and A04 emits exactly two correctly bound confirmed release rows in cleanup order, with empty held/active/context state and authority false; otherwise FAIL.",
        "scope": "In-memory deterministic source-composition construction only; no owner thread, display, OS input, GUI, game, model, application effect, latency, or live allocation.",
        "input_sha256": sha(scenario),
        "source_sha256": {
            "SOURCE/bridge_a04.py": sha(source),
            "run_candidate.py": sha(HERE / "run_candidate.py"),
            "scenario.json": sha(scenario),
            "audit.py": sha(HERE / "audit.py"),
        },
        "source_git_blob": subprocess.check_output(
            ["git", "hash-object", str(source)], cwd=REPO, text=True
        ).strip(),
    }
    path = HERE / "FREEZE.json"
    path.write_text(json.dumps(freeze, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"freeze_sha256": sha(path), "run_id": freeze["run_id"], "image": IMAGE}, sort_keys=True))


if __name__ == "__main__":
    main()
