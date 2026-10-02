from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from trace_writer import write_jsonl, write_legacy_control


EXPECTED_EVENTS = [
    {"event": "probe", "index": 1, "text": "embedded\nvalue"},
    {"event": "terminal", "id": "synthetic-terminal"},
]


def verify_freeze(root: Path) -> dict:
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("main_sha") != "73235730af05375fddf3a9d102d30632e7d43af5":
        raise ValueError("main freeze identity mismatch")
    for filename, expected_sha256 in freeze.get("files", {}).items():
        actual = hashlib.sha256((root / filename).read_bytes()).hexdigest().upper()
        if actual != expected_sha256:
            raise ValueError(f"frozen source hash mismatch: {filename}")
    return freeze


def run(out_dir: Path) -> dict:
    root = Path(__file__).resolve().parent
    freeze = verify_freeze(root)
    expected = root / "results" / "t3-01"
    out_dir = out_dir.resolve()
    if out_dir != expected.resolve():
        raise ValueError(f"output path must be exactly {expected}")
    if out_dir.exists():
        raise FileExistsError(f"output path must not exist: {out_dir}")
    out_dir.mkdir(parents=True)

    child_code = (
        "import json,sys\n"
        "for row in json.loads(sys.argv[1]):\n"
        " print(json.dumps(row,sort_keys=True,separators=(',',':')))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", child_code, json.dumps(EXPECTED_EVENTS)],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"synthetic child failed: {completed.stderr}")
    events = [json.loads(line) for line in completed.stdout.splitlines()]
    if events != EXPECTED_EVENTS:
        raise ValueError("synthetic child event sequence mismatch")

    fixed_path = out_dir / "session-events.jsonl"
    control_path = out_dir / "legacy-control.txt"
    write_jsonl(fixed_path, events)
    write_legacy_control(control_path, events)
    artifacts = {}
    for name, path in (("fixed", fixed_path), ("legacy_control", control_path)):
        raw = path.read_bytes()
        artifacts[name] = {
            "path": path.name,
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "physical_line_count": len(raw.splitlines()),
        }
    receipt = {
        "schema": "map01-terminal-sync-jsonl-writer-contract-candidate-v1",
        "child_exit_code": completed.returncode,
        "events": events,
        "event_count": len(events),
        "freeze_sha256": hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest(),
        "artifacts": artifacts,
    }
    (out_dir / "candidate.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    run(parser.parse_args().out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
