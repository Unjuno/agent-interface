"""Read-only auditor for the nine-case native Windows junction allocation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPECTED = {
    "repo_root": ("/repo", "accept", None), "workspace_root": ("/workspace", "accept", None),
    "regular_file": ("/repo/input.txt", "accept", None),
    "in_root_junction": ("/workspace/in-junction/data.txt", "accept", None),
    "external_junction": ("/repo/external-junction/secret.txt", "reject", "ValueError"),
    "lexical_traversal": ("/repo/../outside/secret.txt", "reject", "ValueError"),
    "encoded_traversal": ("/repo/%2e%2e/outside/secret.txt", "reject", "ValueError"),
    "absolute_host_path": ("ABS", "reject", "ValueError"),
    "missing_path": ("/repo/missing.txt", "reject", "FileNotFoundError"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(raw_path: Path, fixture: Path, root: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("allocation") != freeze["allocation"] or raw.get("source_main") != freeze["source_main"]:
        errors.append("identity")
    for name, expected_hash in freeze["files"].items():
        if sha(root / name) != expected_hash:
            errors.append(name + "_hash")
    if raw.get("candidate_sha256") != freeze["files"]["path_policy.py"] or raw.get("runner_sha256") != freeze["files"]["runner.py"]:
        errors.append("raw_source_hashes")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("environment", {}).get("platform") != "win32":
        errors.append("run_status_or_platform")
    r = fixture / "repo"
    links = ((r / "in-junction", r / "internal"), (r / "external-junction", fixture / "outside"))
    try:
        for link, target in links:
            if not link.is_junction() or link.resolve(strict=True) != target.resolve(strict=True):
                errors.append("junction_identity")
    except (OSError, AttributeError):
        errors.append("junction_inspection")
    rows = raw.get("rows", [])
    observed = {row.get("case_id"): row for row in rows}
    if len(rows) != len(EXPECTED) or set(observed) != set(EXPECTED):
        errors.append("case_inventory")
    for case_id, (input_value, disposition, exception) in EXPECTED.items():
        row = observed.get(case_id)
        if not row:
            continue
        value = str(fixture / "outside" / "secret.txt") if input_value == "ABS" else input_value
        safe = "<absolute-outside-secret>" if input_value == "ABS" else input_value
        if row.get("input") != safe:
            errors.append(case_id + ":input")
        if input_value == "ABS" and row.get("input_sha256") != hashlib.sha256(value.encode()).hexdigest():
            errors.append(case_id + ":input_hash")
        if disposition == "accept":
            target = r if case_id in ("repo_root", "workspace_root") else (r / "input.txt" if case_id == "regular_file" else r / "internal" / "data.txt")
            rel = target.resolve(strict=True).relative_to(fixture.resolve(strict=True)).as_posix()
            if row.get("outcome") != "accepted" or row.get("actual_relative_to_fixture") != rel:
                errors.append(case_id + ":target")
            try:
                (fixture / row.get("actual_relative_to_fixture", "")).resolve(strict=True).relative_to(r.resolve(strict=True))
            except (OSError, ValueError):
                errors.append(case_id + ":containment")
        elif row.get("outcome") != "rejected" or row.get("exception") != exception or row.get("actual_relative_to_fixture") is not None:
            errors.append(case_id + ":rejection")
    setup = raw.get("fixture", {}).get("setup", [])
    if len(setup) != 2 or not all(receipt.get("ok") for receipt in setup):
        errors.append("setup_receipts")
    if raw.get("fixture", {}).get("broker_subprocess_invocations") != 0:
        errors.append("broker_subprocess_invocations")
    return {"schema": "broker_path_windows_junction_4882_v4_audit_v1",
            "status": "PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED" if not errors else "FAIL_OR_HOLD",
            "rows": len(rows), "errors": errors, "fixture_inspected_before_cleanup": True,
            "scope": "candidate resolver in one native Windows NTFS junction fixture"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit.py RAW.json FIXTURE_DIR AUDIT.json PACKAGE_DIR")
    raw_path, fixture, output, package = map(Path, sys.argv[1:])
    report = audit(raw_path, fixture, package)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED" else 1)
