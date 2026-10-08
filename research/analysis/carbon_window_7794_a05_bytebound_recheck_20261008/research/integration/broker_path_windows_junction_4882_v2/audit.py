"""Independent check of frozen rows and the live NTFS junction fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

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


def audit(raw_path: Path, fixture: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    freeze = json.loads(Path(__file__).with_name("FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("allocation") != freeze["allocation"] or raw.get("source_main") != freeze["source_main"]:
        errors.append("identity")
    for name in ("path_policy.py", "runner.py", "audit.py", "make_junctions.ps1"):
        if sha(Path(__file__).with_name(name)) != freeze["files"][name]:
            errors.append(name + "_digest")
    if raw.get("candidate_sha256") != freeze["files"]["path_policy.py"] or raw.get("runner_sha256") != freeze["files"]["runner.py"]:
        errors.append("raw_digests")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("environment", {}).get("platform") != "win32":
        errors.append("run_or_platform")
    root, outside = fixture / "repo", fixture / "outside"
    inside_link, outside_link = root / "in-junction", root / "external-junction"
    try:
        if not inside_link.is_junction() or inside_link.resolve(strict=True) != (root / "internal").resolve(strict=True):
            errors.append("in_root_junction_identity")
        if not outside_link.is_junction() or outside_link.resolve(strict=True) != outside.resolve(strict=True):
            errors.append("external_junction_identity")
    except (OSError, AttributeError):
        errors.append("junction_inspection")
    if raw.get("fixture", {}).get("broker_subprocess_invocations") != 0:
        errors.append("broker_subprocess_invocations")
    rows = raw.get("rows", [])
    observed = {row.get("case_id"): row for row in rows}
    if len(rows) != len(EXPECTED) or set(observed) != set(EXPECTED):
        errors.append("case_inventory")
    for case_id, (expected_input, kind, exception) in EXPECTED.items():
        row = observed.get(case_id)
        if row is None:
            continue
        value = str(outside / "secret.txt") if expected_input == "ABS" else expected_input
        safe_input = "<absolute-outside-secret>" if expected_input == "ABS" else expected_input
        if row.get("input") != safe_input:
            errors.append(case_id + ":input")
        if expected_input == "ABS" and row.get("input_sha256") != hashlib.sha256(value.encode()).hexdigest():
            errors.append(case_id + ":input_hash")
        if kind == "accept":
            target = root if case_id in ("repo_root", "workspace_root") else (root / "input.txt" if case_id == "regular_file" else root / "internal" / "data.txt")
            expected_rel = target.resolve(strict=True).relative_to(fixture.resolve(strict=True)).as_posix()
            if row.get("outcome") != "accepted" or row.get("actual_relative_to_fixture") != expected_rel:
                errors.append(case_id + ":canonical_target")
            try:
                (fixture / row.get("actual_relative_to_fixture", "")).resolve(strict=True).relative_to(root.resolve(strict=True))
            except (OSError, ValueError):
                errors.append(case_id + ":outside_root")
        elif row.get("outcome") != "rejected" or row.get("exception") != exception or row.get("actual_relative_to_fixture") is not None:
            errors.append(case_id + ":rejection")
    return {"schema": "broker_path_windows_junction_4882_v2_audit_v1",
            "status": "PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED" if not errors else "FAIL_OR_HOLD",
            "rows": len(rows), "errors": errors, "fixture_inspected_before_cleanup": True,
            "scope": "candidate resolver under one native Windows NTFS junction fixture"}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json FIXTURE_DIR")
    raw, output, fixture = map(Path, sys.argv[1:])
    result = audit(raw, fixture)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_WINDOWS_JUNCTION_CONFINEMENT_SCOPED" else 1)
