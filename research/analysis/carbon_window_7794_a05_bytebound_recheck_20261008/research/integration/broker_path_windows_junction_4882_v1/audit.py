"""Independent raw and live-fixture auditor; does not import the candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


EXPECTED = {
    "repo_root": ("/repo", "accept", None),
    "workspace_root": ("/workspace", "accept", None),
    "regular_file": ("/repo/input.txt", "accept", None),
    "in_root_junction": ("/workspace/in-junction/data.txt", "accept", None),
    "external_junction": ("/repo/external-junction/secret.txt", "reject", "ValueError"),
    "lexical_traversal": ("/repo/../outside/secret.txt", "reject", "ValueError"),
    "encoded_traversal": ("/repo/%2e%2e/outside/secret.txt", "reject", "ValueError"),
    "absolute_host_path": ("ABSOLUTE_OUTSIDE_SECRET", "reject", "ValueError"),
    "missing_path": ("/repo/missing.txt", "reject", "FileNotFoundError"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(raw_path: Path, fixture_dir: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    freeze = json.loads(Path(__file__).with_name("FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "broker_path_windows_junction_4882_raw_v1":
        errors.append("schema")
    if raw.get("allocation") != "broker-path-windows-junction-4882-20260928-02":
        errors.append("allocation")
    if raw.get("source_main") != freeze.get("source_main"):
        errors.append("source_main")
    if raw.get("candidate_git_blob") != freeze.get("upstream_candidate", {}).get("git_blob"):
        errors.append("candidate_git_blob")
    source = Path(__file__).with_name("path_policy.py")
    if raw.get("candidate_sha256") != digest(source):
        errors.append("candidate_digest")
    if raw.get("candidate_sha256") != freeze["files"]["path_policy.py"]:
        errors.append("candidate_freeze")
    runner = Path(__file__).with_name("runner.py")
    if raw.get("runner_sha256") != digest(runner) or raw.get("runner_sha256") != freeze["files"]["runner.py"]:
        errors.append("runner_digest")
    if digest(Path(__file__).resolve()) != freeze["files"]["audit.py"]:
        errors.append("auditor_digest")
    if raw.get("environment", {}).get("platform") != "win32":
        errors.append("platform")
    fixture = raw.get("fixture", {})
    root = fixture_dir / "repo"
    outside = fixture_dir / "outside"
    internal = root / "internal"
    in_junction = root / "in-junction"
    external_junction = root / "external-junction"
    if not (root.is_dir() and outside.is_dir() and (root / "input.txt").is_file()):
        errors.append("fixture_roots")
    setup = fixture.get("setup", [])
    if len(setup) != 2 or not all(item.get("returncode") == 0 and item.get("setup_ok") is True
                                   for item in setup):
        errors.append("junction_setup_receipts")
    try:
        if (not in_junction.is_junction() or
                in_junction.resolve(strict=True) != internal.resolve(strict=True)):
            errors.append("in_root_junction_identity")
        if (not external_junction.is_junction() or
                external_junction.resolve(strict=True) != outside.resolve(strict=True)):
            errors.append("external_junction_identity")
    except (OSError, AttributeError) as exc:
        errors.append("junction_inspection:" + type(exc).__name__)
    if fixture.get("broker_subprocess_invocations") != 0:
        errors.append("broker_subprocess_invocations")
    if raw.get("status") != "RUN_COMPLETE":
        errors.append("runner_status")
    rows = raw.get("rows", [])
    observed = {row.get("case_id"): row for row in rows}
    if len(rows) != len(EXPECTED) or set(observed) != set(EXPECTED):
        errors.append("case_inventory")
    for case_id, (expected_input, disposition, exception) in EXPECTED.items():
        row = observed.get(case_id)
        if not row:
            continue
        value = str(outside / "secret.txt") if expected_input == "ABSOLUTE_OUTSIDE_SECRET" else expected_input
        recorded_input = "<absolute-outside-secret>" if expected_input == "ABSOLUTE_OUTSIDE_SECRET" else value
        if row.get("input") != recorded_input:
            errors.append(case_id + ":input")
        if (expected_input == "ABSOLUTE_OUTSIDE_SECRET" and
                row.get("input_sha256") != hashlib.sha256(value.encode("utf-8")).hexdigest()):
            errors.append(case_id + ":absolute_input_hash")
        if disposition == "accept":
            target = root if case_id in ("repo_root", "workspace_root") else (
                root / "input.txt" if case_id == "regular_file" else internal / "data.txt")
            expected_relative = target.resolve(strict=True).relative_to(fixture_dir.resolve(strict=True)).as_posix()
            if (row.get("outcome") != "accepted" or
                    row.get("actual_relative_to_fixture") != expected_relative):
                errors.append(case_id + ":canonical_target")
            try:
                (fixture_dir / row.get("actual_relative_to_fixture", "")).resolve(strict=True).relative_to(
                    root.resolve(strict=True))
            except (OSError, ValueError):
                errors.append(case_id + ":outside_root")
        elif (row.get("outcome") != "rejected" or row.get("exception") != exception or
              row.get("actual_relative_to_fixture") is not None):
            errors.append(case_id + ":rejection")
    report = {
        "schema": "broker_path_windows_junction_4882_audit_v1",
        "status": "PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED" if not errors else "FAIL_OR_HOLD",
        "rows": len(rows),
        "errors": errors,
        "fixture_inspected_before_cleanup": True,
        "scope": "candidate path policy under one native Windows/NTFS junction fixture; no production broker or model",
    }
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json FIXTURE_DIR")
    raw_path, output, fixture_dir = map(Path, sys.argv[1:])
    result = audit(raw_path, fixture_dir)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED" else 1)
