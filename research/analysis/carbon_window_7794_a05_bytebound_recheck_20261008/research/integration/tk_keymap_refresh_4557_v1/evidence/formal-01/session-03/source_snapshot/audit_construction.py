#!/usr/bin/env python3
"""Independent raw-evidence audit for the excluded Tk/XKB construction probe."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("summary root must be an object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(summary_path: Path) -> list[str]:
    summary = load(summary_path)
    errors: list[str] = []
    if summary.get("formal") is not False:
        errors.append("construction must be explicitly excluded from formal")
    if summary.get("disposition") != "CONSTRUCTION_MECHANICS_ONLY":
        errors.append("unexpected construction disposition")
    expected = ["us_baseline", "existing_after_de", "fresh_after_de"]
    steps = summary.get("steps")
    if not isinstance(steps, list) or [step.get("phase") for step in steps] != expected:
        errors.append("phase sequence is missing, duplicated, or out of order")
        return errors
    for step in steps:
        phase = step["phase"]
        events = step.get("events")
        if not isinstance(events, list) or len(events) != 2:
            errors.append(f"{phase}: expected exactly press and release")
            continue
        if [event.get("kind") for event in events] != ["press", "release"]:
            errors.append(f"{phase}: event pair is not press then release")
        for event in events:
            if event.get("phase") != phase or event.get("keycode") != 29:
                errors.append(f"{phase}: wrong phase or keycode")
        server = step.get("server_map", {})
        keysyms = server.get("keysyms", [])
        if phase == "us_baseline" and "y" not in keysyms:
            errors.append("US baseline server map lacks keycode-29 y")
        if phase != "us_baseline" and "z" not in keysyms:
            errors.append(f"{phase}: DE server map lacks keycode-29 z")
        if phase in ("us_baseline", "fresh_after_de"):
            expected_symbol = "y" if phase == "us_baseline" else "z"
            if any(event.get("keysym") != expected_symbol for event in events):
                errors.append(f"{phase}: Tk keysym does not match independent expected symbol")
        send = step.get("send", {})
        if send.get("phase") != phase or send.get("target_window_id") != step.get("window_id"):
            errors.append(f"{phase}: input request lacks phase or target window")
        if send.get("request_sequence") != [{"type": "KeyPress", "detail": 29},
                                             {"type": "KeyRelease", "detail": 29}]:
            errors.append(f"{phase}: XTEST request sequence is missing or changed")
        if send.get("observer_states") != {"after_press": True, "after_release": False}:
            errors.append(f"{phase}: independent server key-state transitions disagree")
        if send.get("terminal_key_down") is not False:
            errors.append(f"{phase}: terminal key state is not independently neutral")
    hashes = summary.get("source_sha256")
    if not isinstance(hashes, dict) or not hashes:
        errors.append("source hashes are missing")
    else:
        for name, expected_hash in hashes.items():
            source = summary_path.parent / "source_snapshot" / name
            if not source.is_file() or digest(source) != expected_hash:
                errors.append(f"source hash mismatch: {name}")
    if not (summary_path.parent / "xvfb.stderr.txt").is_file():
        errors.append("Xvfb stderr log is missing")
    exits = summary.get("child_exit_codes")
    if not isinstance(exits, dict) or not exits or any(code is None for code in exits.values()):
        errors.append("child process exits are missing or unverified")
    if summary.get("xvfb_exit_code") is None:
        errors.append("Xvfb exit is missing or unverified")
    for name in ("old.events.jsonl", "fresh.events.jsonl", "old.stdout.txt", "old.stderr.txt",
                 "fresh.stdout.txt", "fresh.stderr.txt"):
        if not (summary_path.parent / name).is_file():
            errors.append(f"raw child artifact missing: {name}")
    for phase, filename in (("us_baseline", "old.events.jsonl"),
                            ("existing_after_de", "old.events.jsonl"),
                            ("fresh_after_de", "fresh.events.jsonl")):
        raw_rows = [row for row in (summary_path.parent / filename).read_text(encoding="utf-8").splitlines()
                    if row and json.loads(row).get("phase") == phase]
        expected_rows = next(step["events"] for step in steps if step["phase"] == phase)
        if [json.loads(row) for row in raw_rows] != expected_rows:
            errors.append(f"{phase}: raw JSONL and summary differ")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    errors = audit(args.summary)
    print(json.dumps({"errors": errors, "pass": not errors}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
