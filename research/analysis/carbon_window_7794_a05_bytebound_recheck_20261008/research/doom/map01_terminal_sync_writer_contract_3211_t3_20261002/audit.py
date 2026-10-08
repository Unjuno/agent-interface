from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_EVENTS = [
    {"event": "probe", "index": 1, "text": "embedded\nvalue"},
    {"event": "terminal", "id": "synthetic-terminal"},
]


def audit(out_dir: Path, bundle_root: Path | None = None) -> dict:
    out = out_dir.resolve()
    root = (bundle_root or out.parents[1]).resolve()
    freeze_raw = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    if freeze.get("main_sha") != "73235730af05375fddf3a9d102d30632e7d43af5":
        raise ValueError("main freeze identity mismatch")
    for filename, expected_sha256 in freeze.get("files", {}).items():
        actual = hashlib.sha256((root / filename).read_bytes()).hexdigest().upper()
        if actual != expected_sha256:
            raise ValueError(f"frozen source hash mismatch: {filename}")
    receipt = json.loads((out / "candidate.json").read_text(encoding="utf-8"))
    if receipt.get("freeze_sha256") != hashlib.sha256(freeze_raw).hexdigest():
        raise ValueError("candidate freeze manifest identity mismatch")
    if receipt.get("child_exit_code") != 0 or receipt.get("events") != EXPECTED_EVENTS:
        raise ValueError("child completion or exact event sequence mismatch")
    checked = {}
    for name, filename in (("fixed", "session-events.jsonl"), ("legacy_control", "legacy-control.txt")):
        raw = (out / filename).read_bytes()
        recorded = receipt.get("artifacts", {}).get(name, {})
        if recorded.get("byte_count") != len(raw):
            raise ValueError(f"{name}: byte count mismatch")
        digest = hashlib.sha256(raw).hexdigest()
        if recorded.get("sha256") != digest:
            raise ValueError(f"{name}: SHA-256 mismatch")
        lines = raw.splitlines()
        if recorded.get("physical_line_count") != len(lines):
            raise ValueError(f"{name}: physical line count mismatch")
        checked[name] = {"byte_count": len(raw), "sha256": digest, "physical_line_count": len(lines)}

    fixed_lines = (out / "session-events.jsonl").read_bytes().splitlines()
    fixed_rows = [json.loads(line.decode("utf-8")) for line in fixed_lines]
    if fixed_rows != EXPECTED_EVENTS or len(fixed_lines) != len(EXPECTED_EVENTS):
        raise ValueError("fixed stream is not exact conventional JSONL")
    control_raw = (out / "legacy-control.txt").read_bytes()
    try:
        control_rows = [json.loads(line.decode("utf-8")) for line in control_raw.splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError):
        control_rows = None
    if control_rows is not None:
        raise ValueError("legacy control unexpectedly parsed as ordinary JSONL")
    if len(control_raw.splitlines()) != 1:
        raise ValueError("legacy control should be one physical line")
    return {
        "schema": "map01-terminal-sync-jsonl-writer-contract-audit-v1",
        "decision": "PASS_WRITER_CONTRACT_SCOPED",
        "main_sha": freeze["main_sha"],
        "freeze_sha256": hashlib.sha256(freeze_raw).hexdigest(),
        "event_count": len(fixed_rows),
        "fixed_jsonl_rows": fixed_rows,
        "legacy_control_jsonl_rejected": True,
        "artifacts": checked,
        "scope_limit": "Synthetic JSONL writer contract only; no MAP01 session lifecycle, recovery terminal, timeout cause, or efficacy inference.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    result = audit(parser.parse_args().out)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
