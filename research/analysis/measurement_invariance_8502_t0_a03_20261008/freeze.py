"""Create the one-shot A03 freeze from exact on-disk bytes before formal execution."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
from pathlib import Path


SOURCES = ["README.md", "PROTOCOL.md", "CONSTRUCTION.md", "config.json", "generate.py", "candidate.py",
           "integrity.py", "audit.py", "test_candidate.py", "test_audit.py", "freeze.py"]
INPUTS = ["fixtures.json", "truth.json"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-sha", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    payload = {
        "schema": "issue8502-t0-a03-freeze-v1", "issue": 8502, "allocation": "A03",
        "main_sha": args.main_sha,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "runtime": {"python": sys.version.split()[0], "platform": platform.platform(), "execution": "local CPU; standard library only"},
        "formal_counts": {"candidate": 1, "independent_auditor": 1, "candidate_retries": 0, "auditor_retries": 0},
        "construction": {"test_suite_invocations": 5, "candidate_full_fixture_construction_calls": 9,
                         "auditor_construction_suite_invocations": 4,
                         "result": "construction only; none counted as formal allocation"},
        "seeds": {"F01": 850301, "F02": 850302, "F03": 850303, "F04": 850304, "F05": 850305},
        "sources": {name: digest(root / name) for name in SOURCES},
        "inputs": {name: digest(root / name) for name in INPUTS},
    }
    encoded = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
    with (root / "FREEZE.json").open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"freeze_sha256": hashlib.sha256(encoded).hexdigest(), "sources": len(SOURCES), "inputs": len(INPUTS)}, sort_keys=True))


if __name__ == "__main__":
    main()
