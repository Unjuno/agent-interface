#!/usr/bin/env python3
"""Independent integrity checks for the C09 cleanup regression evidence."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
    baseline = HERE / "BASELINE-session_map01_v15.py"
    source = ROOT / "research/doom/session_map01_v15.py"
    assert sha256(baseline) == freeze["baseline_sha256"] == raw["baseline"]["sha256"]
    blob = subprocess.check_output(["git", "hash-object", str(baseline)], cwd=ROOT, text=True).strip()
    assert blob == freeze["baseline_blob"] == raw["baseline"]["git_blob"]
    assert sha256(source) == raw["candidate"]["sha256"]
    assert (HERE / raw["candidate"]["path"]).resolve() == source.resolve()
    assert (HERE / "red.exit.txt").read_text().strip() == str(raw["regression"]["red_exit"])
    assert (HERE / "green.exit.txt").read_text().strip() == str(raw["regression"]["green_exit"])
    assert "FAIL" in (HERE / "red.stdout.txt").read_text(encoding="utf-8")
    assert "OK" in (HERE / "green.stdout.txt").read_text(encoding="utf-8")
    sums = {}
    for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        assert name not in sums
        sums[name] = digest
        assert sha256(HERE / name) == digest, name
    expected = {p.name for p in HERE.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt" and p.name != "audit.json"}
    assert set(sums) == expected, (sorted(set(sums) - expected), sorted(expected - set(sums)))
    result = {
        "artifact_id": freeze["artifact_id"],
        "status": "PASS",
        "checks": ["frozen baseline sha256 and git blob", "candidate source sha256", "red and green outcomes", "all listed package hashes", "complete file coverage excluding audit output and checksum index"],
        "files_hashed": len(sums)
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
