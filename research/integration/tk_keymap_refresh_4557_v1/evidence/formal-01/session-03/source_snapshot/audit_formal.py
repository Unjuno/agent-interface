#!/usr/bin/env python3
"""Independent raw-record auditor for the six-session Tk/XKB allocation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCHEDULE = [f"tk-xkb-refresh-4664-formal-session-{index:02d}" for index in range(1, 7)]
PHASES = ("us_baseline", "existing_after_de", "fresh_after_de")
IMAGE_ID = "sha256:4c62a3d908f6bffdbff88b28eeff305bed40f5d6fcee029b7c0a3fa2ea5a86d6"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def session_errors(root: Path, index: int, expected_id: str,
                   expected_source_hashes: dict[str, str]) -> tuple[list[str], dict | None]:
    directory = root / f"session-{index:02d}"
    path = directory / "summary.json"
    errors: list[str] = []
    if not path.is_file():
        return [f"session-{index:02d}: summary missing"], None
    summary = read_object(path)
    if summary.get("formal") is not True:
        errors.append(f"session-{index:02d}: not marked formal")
    if summary.get("allocation_id") != expected_id:
        errors.append(f"session-{index:02d}: allocation id mismatch")
    if summary.get("disposition") != "FORMAL_SESSION_COMPLETE":
        errors.append(f"session-{index:02d}: session is incomplete")
    if summary.get("source_sha256") != expected_source_hashes:
        errors.append(f"session-{index:02d}: source hashes differ from frozen bundle")
    for name, expected_hash in expected_source_hashes.items():
        source = directory / "source_snapshot" / name
        if not source.is_file() or digest(source) != expected_hash:
            errors.append(f"session-{index:02d}: source snapshot mismatch: {name}")
    steps = summary.get("steps")
    if not isinstance(steps, list) or [step.get("phase") for step in steps] != list(PHASES):
        errors.append(f"session-{index:02d}: phase sequence incomplete or reordered")
        return errors, summary
    for step in steps:
        phase = step["phase"]
        events = step.get("events")
        if not isinstance(events, list) or len(events) != 2:
            errors.append(f"session-{index:02d}/{phase}: expected two events")
            continue
        if [event.get("kind") for event in events] != ["press", "release"]:
            errors.append(f"session-{index:02d}/{phase}: press/release order invalid")
        for event in events:
            if event.get("phase") != phase or event.get("keycode") != 29:
                errors.append(f"session-{index:02d}/{phase}: phase/keycode mismatch")
        keysyms = step.get("server_map", {}).get("keysyms", [])
        required_server_symbol = "y" if phase == "us_baseline" else "z"
        if step.get("server_map", {}).get("keycode") != 29 or required_server_symbol not in keysyms:
            errors.append(f"session-{index:02d}/{phase}: server map mismatch")
        if phase in ("us_baseline", "fresh_after_de"):
            expected = "y" if phase == "us_baseline" else "z"
            if any(event.get("keysym") != expected for event in events):
                errors.append(f"session-{index:02d}/{phase}: expected Tk keysym {expected}")
        send = step.get("send", {})
        if send.get("phase") != phase or send.get("target_window_id") != step.get("window_id"):
            errors.append(f"session-{index:02d}/{phase}: input target/phase mismatch")
        if send.get("request_sequence") != [{"type": "KeyPress", "detail": 29},
                                             {"type": "KeyRelease", "detail": 29}]:
            errors.append(f"session-{index:02d}/{phase}: XTEST request sequence mismatch")
        if send.get("observer_states") != {"after_press": True, "after_release": False}:
            errors.append(f"session-{index:02d}/{phase}: independent server key states mismatch")
        if send.get("terminal_key_down") is not False:
            errors.append(f"session-{index:02d}/{phase}: terminal key state not neutral")

        raw_file = directory / ("fresh.events.jsonl" if phase == "fresh_after_de" else "old.events.jsonl")
        if not raw_file.is_file():
            errors.append(f"session-{index:02d}/{phase}: raw event log missing")
        else:
            raw = [json.loads(line) for line in raw_file.read_text(encoding="utf-8").splitlines() if line]
            actual = [row for row in raw if row.get("phase") == phase]
            if actual != events:
                errors.append(f"session-{index:02d}/{phase}: raw log differs from summary")

    child_codes = summary.get("child_exit_codes")
    if not isinstance(child_codes, dict) or not child_codes or any(code is None for code in child_codes.values()):
        errors.append(f"session-{index:02d}: child exits missing")
    if summary.get("xvfb_exit_code") != 0:
        errors.append(f"session-{index:02d}: Xvfb did not exit cleanly")
    for name in ("old.ready.jsonl", "fresh.ready.jsonl", "old.stdout.txt", "old.stderr.txt",
                 "fresh.stdout.txt", "fresh.stderr.txt", "xvfb.stderr.txt"):
        if not (directory / name).is_file():
            errors.append(f"session-{index:02d}: artifact missing: {name}")
    return errors, summary


def audit(root: Path, expected_manifest_sha256: str) -> dict:
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    freeze_path = root / "freeze.sha256"
    if not manifest_path.is_file() or not freeze_path.is_file():
        return {"disposition": "HOLD_INCONSISTENT_OR_INCOMPLETE", "errors": ["freeze files missing"],
                "sessions": []}
    actual_manifest_sha = digest(manifest_path)
    recorded_freeze = freeze_path.read_text(encoding="ascii").strip()
    if actual_manifest_sha != expected_manifest_sha256 or recorded_freeze != expected_manifest_sha256:
        errors.append("frozen manifest hash mismatch")
    manifest = read_object(manifest_path)
    if manifest.get("formal") is not True or manifest.get("invocation_count") != 1:
        errors.append("formal invocation contract mismatch")
    if manifest.get("retry_count") != 0 or manifest.get("replacement_count") != 0:
        errors.append("retry/replacement contract mismatch")
    if manifest.get("image_id") != IMAGE_ID or manifest.get("expected_image_id") != IMAGE_ID:
        errors.append("container image identity mismatch")
    if manifest.get("scheduled_sessions") != SCHEDULE:
        errors.append("frozen schedule mismatch")

    source_snapshot = root / "source_snapshot"
    source_hashes = manifest.get("source_sha256", {})
    if not isinstance(source_hashes, dict) or not source_hashes:
        errors.append("source hashes missing")
    else:
        for name, expected_hash in source_hashes.items():
            path = source_snapshot / name
            if not path.is_file() or digest(path) != expected_hash:
                errors.append(f"source snapshot mismatch: {name}")

    orchestration_path = root / "orchestration.json"
    outcomes: dict[str, dict] = {}
    if not orchestration_path.is_file():
        errors.append("orchestration record missing")
    else:
        orchestration = read_object(orchestration_path)
        if orchestration.get("scheduled_sessions") != SCHEDULE:
            errors.append("orchestration schedule mismatch")
        if orchestration.get("retry_count") != 0 or orchestration.get("replacement_count") != 0:
            errors.append("orchestration includes retry/replacement")
        outcomes = {item.get("allocation_id"): item for item in orchestration.get("outcomes", [])}
        if list(outcomes) != SCHEDULE:
            errors.append("orchestration denominator/order mismatch")
        if any(item.get("returncode") != 0 for item in outcomes.values()):
            errors.append("one or more session runners exited nonzero or timed out")

    environment_path = root / "environment.json"
    if not environment_path.is_file():
        errors.append("runtime environment record missing")
    else:
        environment = read_object(environment_path)
        if environment.get("tk_runtime", {}).get("returncode") != 0:
            errors.append("Tk/Xlib runtime identity check failed")
        if environment.get("dpkg_packages", {}).get("returncode") != 0:
            errors.append("package version inventory failed")

    rows: list[dict] = []
    for index, allocation_id in enumerate(SCHEDULE, start=1):
        row_errors, summary = session_errors(root, index, allocation_id, source_hashes)
        errors.extend(row_errors)
        rows.append({"allocation_id": allocation_id, "errors": row_errors, "summary": summary})

    evidence_hash_path = root / "evidence_sha256.json"
    if not evidence_hash_path.is_file():
        errors.append("evidence hash manifest missing")
    else:
        expected_files = read_object(evidence_hash_path)
        for relative, expected_hash in expected_files.items():
            path = root / relative
            if not path.is_file() or digest(path) != expected_hash:
                errors.append(f"evidence hash mismatch: {relative}")

    stale = False
    for row in rows:
        summary = row["summary"]
        if not summary or len(summary.get("steps", [])) != 3:
            continue
        by_phase = {step.get("phase"): step for step in summary["steps"]}
        de_server = "z" in by_phase.get("existing_after_de", {}).get("server_map", {}).get("keysyms", [])
        fresh_z = all(event.get("keysym") == "z" for event in
                      by_phase.get("fresh_after_de", {}).get("events", []))
        old_events = by_phase.get("existing_after_de", {}).get("events", [])
        old_not_z = any(event.get("keysym") != "z" for event in old_events)
        if de_server and fresh_z and old_not_z and not row["errors"]:
            stale = True

    if stale:
        disposition = "FAIL_TK_STALE_MAPPING_EXPOSED"
    elif not errors and len(rows) == 6 and all(
        all(event.get("keysym") == "z" for event in
            {step["phase"]: step for step in row["summary"]["steps"]}["existing_after_de"]["events"])
        for row in rows
    ):
        disposition = "PASS_TK_XKB_REFRESH_SCOPED"
    else:
        disposition = "HOLD_INCONSISTENT_OR_INCOMPLETE"
    return {"disposition": disposition, "errors": errors,
            "sessions": [{"allocation_id": row["allocation_id"], "errors": row["errors"]} for row in rows],
            "stale_mapping_observed": stale}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.root, args.expected_manifest_sha256)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["disposition"] in ("PASS_TK_XKB_REFRESH_SCOPED", "FAIL_TK_STALE_MAPPING_EXPOSED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
