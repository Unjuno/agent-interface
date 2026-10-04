"""Generate the A04 source/input identity record; never touches A03 outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
A03 = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005"
ROOT = HERE.parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "rev-parse", "HEAD:" + relative],
                                  cwd=ROOT, text=True).strip()


def main() -> None:
    input_path = A03 / "INPUT_EVENTS.jsonl"
    a03_files = ("INPUT_EVENTS.jsonl", "FREEZE.json", "candidate.py", "audit.py")
    own_files = ("README.md", "PLAN.md", "candidate.py", "audit.py", "test_consumer.py",
                 "reproduce_a03.py", "generate_freeze.py", "audit_report.py")
    record = {
        "schema": "map01_v39_perkey_measurement_consumer_a04_freeze_v1",
        "run_id": "MAP01-V39-PERKEY-MEASUREMENT-CONSUMER-A04-20261005",
        "kind": "offline_boundary_regression",
        "formal_allocation": False,
        "a03": {
            "path": "../map01_v39_perkey_measurement_consumer_a03_20261005",
            "files": {name: {"sha256": sha256(A03 / name),
                             "git_blob": git_blob(A03 / name)}
                      for name in a03_files},
        },
        "input": {"path": "../map01_v39_perkey_measurement_consumer_a03_20261005/INPUT_EVENTS.jsonl",
                  "sha256": sha256(input_path),
                  "git_blob": git_blob(input_path)},
        "source_sha256": {name: sha256(HERE / name) for name in own_files},
        "commands": [
            "py -3 generate_freeze.py",
            "py -3 reproduce_a03.py",
            "py -3 -m unittest -v test_consumer.py",
            "py -3 -O -m unittest -v test_consumer.py",
            "py -3 audit_report.py",
            "py -3 -m py_compile candidate.py audit.py test_consumer.py reproduce_a03.py generate_freeze.py audit_report.py",
        ],
        "scope": "exact typing of down/up owner-bracket intervals in a retained fake-display pair; no live input or task-effect claim",
    }
    (HERE / "FREEZE.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
