"""Freeze the one-shot A02 runner, auditor, and owner source."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = HERE / "FREEZE-A03.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=HERE, text=True).strip()


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE-A03.json already exists")
    paths = {
        "input_owner_v13.py": HERE / "input_owner_v13.py",
        "run_a03.py": HERE / "run_a03.py",
        "audit_a03.py": HERE / "audit_a03.py",
        "v12/test_input_owner_v12.py": ROOT / "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/test_input_owner_v12.py",
        "v12/input_owner_v12.py": ROOT / "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py",
        "live_control/executor_v3.py": ROOT / "research/live_control/executor_v3.py",
        "bridge/test_bridge.py": ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py",
        "bridge/bridge.py": ROOT / "research/doom/map01_v39_perkey_bridge_a01/bridge.py",
    }
    sources = {}
    for name, path in paths.items():
        raw = path.read_bytes()
        sources[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": git("hash-object", str(path)),
            "path": path.relative_to(ROOT).as_posix(),
        }
    payload = {
        "run_id": "map01-v39-cancel-cleanup-bracket-a03-20261005",
        "base_commit": git("rev-parse", "HEAD"),
        "sources": sources,
        "python_version": __import__("sys").version.split()[0],
        "protocol_change": "A03 freezes runtime and all imported fake-owner harness/control sources",
        "method": "offline fake X display; one two-key cancellation cleanup",
        "retries": 0,
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
