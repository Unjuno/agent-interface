"""Independent raw-only audit for the Issue #2922 setup-only result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def audit(root: Path, *, rows_override=None, manifest_override=None,
          runner_sources_override=None, package_override=None) -> list[str]:
    errors: list[str] = []
    package = package_override or root / "research/integration/golden_ipc_source_closure_2922_v1"
    evidence = root / "evidence/ready-gate-01"
    rows = rows_override if rows_override is not None else [
        json.loads(line) for line in (package / "events.jsonl").read_text().splitlines()]
    kinds = [row.get("event") for row in rows]
    if kinds != ["ready", "observation", "command", "independent_evaluation"]:
        errors.append("event sequence/cardinality mismatch")
    ready = rows[0] if rows else {}
    goal = ready.get("goal", {}) if isinstance(ready.get("goal"), dict) else {}
    if ready.get("app") != "chromium" or not str(goal.get("url", "")).startswith("http://127.0.0.1:"):
        errors.append("ready identity or private endpoint mismatch")
    if goal.get("setup_readiness_captures") != 0:
        errors.append("unexpected setup-readiness capture count")
    observation = rows[1] if len(rows) > 1 else {}
    if observation.get("exact") is not True or observation.get("semantic_completion") != "unknown":
        errors.append("initial observation not exact/unknown")
    windows = observation.get("context", [])
    if not any("about:blank" in str(item) for item in windows):
        errors.append("startup observation is not the frozen about:blank state")
    command = rows[2].get("command", {}) if len(rows) > 2 else {}
    if command != {"op": "finish"}:
        errors.append("non-finish command or task submission present")
    if any(str(row.get("event", "")).startswith("input_") or row.get("event") == "action_admission" for row in rows):
        errors.append("input/action event present")
    evaluation = rows[3] if len(rows) > 3 else {}
    if evaluation.get("success") is not False or "FileNotFoundError" not in str(evaluation.get("actual")):
        errors.append("zero-action evaluation disposition changed")

    manifest = manifest_override if manifest_override is not None else json.loads(
        (package / "SOURCE_MANIFEST.json").read_text())
    runner_sources = runner_sources_override if runner_sources_override is not None else json.loads(
        (package / "sources.json").read_text())
    normalized_manifest_paths = {path.removeprefix("research/") for path in manifest.get("files", {})}
    if normalized_manifest_paths != set(runner_sources):
        errors.append("source manifest denominator mismatch")
    for rel, expected in manifest.get("files", {}).items():
        source = package / "source_snapshot" / Path(rel)
        try:
            data = source.read_bytes()
        except OSError:
            errors.append(f"source missing: {rel}")
            continue
        if hashlib.sha256(data).hexdigest() != expected.get("sha256"):
            errors.append(f"source sha256 mismatch: {rel}")
        if git_blob_sha(data) != expected.get("git_blob"):
            errors.append(f"source git blob mismatch: {rel}")
        if runner_sources.get(rel.removeprefix("research/")) != expected.get("sha256"):
            errors.append(f"runner source receipt mismatch: {rel}")

    image = package / "001.png"
    if not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest() != (
            "0ad03d3f0636a714b6a75868d8a7d0e1d2aaff09c437e7552a46f2bf316c8bbe"):
        errors.append("initial screenshot missing or hash mismatch")
    return errors


if __name__ == "__main__":
    package = Path(__file__).resolve().parent
    problems = audit(package, package_override=package)
    source_count = len(json.loads((package / "SOURCE_MANIFEST.json").read_text())["files"])
    print(json.dumps({"event_rows": 4, "source_files": source_count, "errors": problems,
                      "disposition": "HOLD_XVFB_READY_SIGNAL_INTERVENTION" if not problems else "FAIL_AUDIT"},
                     sort_keys=True))
    raise SystemExit(bool(problems))
