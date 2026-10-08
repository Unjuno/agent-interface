"""Independent live-fixture auditor for the native Windows broker serve() allocation."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys

FIELDS = ("schema", "image", "working")
BAD_KINDS = ("traversal", "encoded_traversal", "absolute", "missing",
             "external_junction", "ambiguous_separator")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(base: Path) -> list[dict]:
    rows = []
    for current, dirs, files in os.walk(base, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(current) / name
            info = path.lstat()
            rel = path.relative_to(base).as_posix()
            if path.is_junction():
                target = path.resolve(strict=True).relative_to(base.resolve(strict=True)).as_posix()
                rows.append({"path": rel, "kind": "junction", "target_relative": target, "sha256": None})
            elif path.is_symlink():
                rows.append({"path": rel, "kind": "symlink", "target_relative": os.readlink(path), "sha256": None})
            elif path.is_dir():
                rows.append({"path": rel, "kind": "directory", "target_relative": None, "sha256": None})
            elif path.is_file():
                rows.append({"path": rel, "kind": "file", "target_relative": None, "sha256": sha(path)})
            else:
                rows.append({"path": rel, "kind": "other", "target_relative": None, "sha256": None})
    return sorted(rows, key=lambda row: row["path"])


def expected_schedule(outside: Path) -> list[dict]:
    cases = [
        {"case_id": "valid_repo", "field": None, "kind": "valid_repo", "paths":
         {"schema": "/repo/internal/schema.json", "image": "/repo/internal/image.png", "working": "/repo/internal/work"}},
        {"case_id": "valid_workspace", "field": None, "kind": "valid_workspace", "paths":
         {"schema": "/workspace/internal/schema.json", "image": "/workspace/internal/image.png", "working": "/workspace/internal/work"}},
    ]
    for field, filename in (("schema", "schema.json"), ("image", "image.png"), ("working", "work")):
        paths = {"schema": "/repo/internal/schema.json", "image": "/repo/internal/image.png", "working": "/repo/internal/work"}
        paths[field] = "/repo/in-junction/" + filename if field != "working" else "/repo/in-junction/work"
        cases.append({"case_id": field + "_inside_junction", "field": field, "kind": "inside_junction", "paths": paths})
    for field in FIELDS:
        for kind in BAD_KINDS:
            paths = {"schema": "/repo/internal/schema.json", "image": "/repo/internal/image.png", "working": "/repo/internal/work"}
            file_name = "work" if field == "working" else ("image.png" if field == "image" else "schema.json")
            if kind == "traversal":
                paths[field] = "/repo/../outside/" + file_name
            elif kind == "encoded_traversal":
                paths[field] = "/repo/%252e%252e/outside/" + file_name
            elif kind == "absolute":
                paths[field] = str(outside / file_name)
            elif kind == "missing":
                paths[field] = "/repo/not-present"
            elif kind == "external_junction":
                paths[field] = "/repo/external-junction/" + file_name
            else:
                paths[field] = "/repo/sub\\..\\outside"
            cases.append({"case_id": field + "_" + kind, "field": field, "kind": kind, "paths": paths})
    return cases


def expected_accept_argv(case: dict) -> dict:
    paths = case["paths"]
    values = {}
    for key, value in paths.items():
        if case["kind"] == "inside_junction" and key == case["field"]:
            suffix = {"schema": "internal/schema.json", "image": "internal/image.png",
                      "working": "internal/work"}[key]
        else:
            suffix = value.split("/", 2)[2]
        values[key] = "repo/" + suffix
    return values


def evaluate(raw: dict, manifest: dict, fixture: Path, package: Path) -> list[str]:
    errors = []
    freeze = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
    if raw.get("allocation") != freeze["allocation"] or raw.get("source_main") != freeze["source_main"]:
        errors.append("allocation_or_main")
    for name, digest in freeze["files"].items():
        if sha(package / name) != digest:
            errors.append(name + "_source_hash")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("case_count") != 23:
        errors.append("run_status_or_case_count")
    if raw.get("environment", {}).get("platform") != "win32" or raw.get("environment", {}).get("os_name") != "nt":
        errors.append("native_windows_environment")
    if raw.get("subprocess_mocked") is not True:
        errors.append("mock_boundary")
    if raw.get("fixture_unchanged") is not True:
        errors.append("fixture_changed_during_run")
    actual_inventory = inventory(fixture)
    if manifest.get("entries") != actual_inventory or raw.get("fixture_after_entries") != actual_inventory:
        errors.append("durable_fixture_inventory")
    root, outside = fixture / "repo", fixture / "outside"
    try:
        if not (root / "in-junction").is_junction() or (root / "in-junction").resolve(strict=True) != (root / "internal").resolve(strict=True):
            errors.append("in_root_junction_identity")
        if not (root / "external-junction").is_junction() or (root / "external-junction").resolve(strict=True) != outside.resolve(strict=True):
            errors.append("external_junction_identity")
    except (OSError, AttributeError):
        errors.append("junction_inspection")
    cases = expected_schedule(outside)
    rows = raw.get("rows", [])
    observed = {row.get("case_id"): row for row in rows}
    if len(rows) != 23 or set(observed) != {case["case_id"] for case in cases}:
        errors.append("case_inventory")
    for case in cases:
        row = observed.get(case["case_id"])
        if row is None:
            continue
        accepted = case["kind"] in ("valid_repo", "valid_workspace", "inside_junction")
        expected_paths = dict(case["paths"])
        absolute = {key: value for key, value in expected_paths.items()
                    if not value.startswith(("/repo", "/workspace"))}
        for key, value in absolute.items():
            expected_paths[key] = "<absolute-outside>"
        expected_hashes = {key: hashlib.sha256(value.encode("utf-8")).hexdigest()
                           for key, value in absolute.items()}
        if row.get("kind") != case["kind"] or row.get("field") != case["field"] or row.get("expected") != ("accept" if accepted else "reject"):
            errors.append(case["case_id"] + ":schedule")
        if row.get("request_paths") != expected_paths or row.get("absolute_input_sha256") != expected_hashes:
            errors.append(case["case_id"] + ":inputs")
        receipt = row.get("receipt", {})
        if (row.get("request_id_count") != 1 or row.get("broker_receipt_count") != 1 or
                receipt.get("request_id") != f"case-{cases.index(case):02d}"):
            errors.append(case["case_id"] + ":receipt_count")
        if receipt.get("authority_granted") is not False or receipt.get("boundary") != "host-local-codex-exe":
            errors.append(case["case_id"] + ":authority")
        if accepted:
            if (row.get("subprocess_calls") != 1 or row.get("exit_code") != 0 or
                    receipt.get("returncode") != 0 or row.get("response") != '{"mock":"ok"}'):
                errors.append(case["case_id"] + ":accept_receipt")
            if row.get("argv_paths_relative_to_fixture") != expected_accept_argv(case):
                errors.append(case["case_id"] + ":argv_containment")
        else:
            if (row.get("subprocess_calls") != 0 or row.get("exit_code") != 1 or
                    receipt.get("returncode") is not None or receipt.get("error_class") != "InvalidHostPath" or
                    receipt.get("stop_reason") != "HOST_MODEL_PATH_REJECTED" or row.get("response") != ""):
                errors.append(case["case_id"] + ":reject_receipt")
            if row.get("argv_paths_relative_to_fixture") is not None:
                errors.append(case["case_id"] + ":unexpected_argv")
    if raw.get("subprocess_call_count") != 5 or raw.get("broker_subprocess_invocations") != 5:
        errors.append("aggregate_mock_calls")
    return errors


def audit(raw_path: Path, manifest_path: Path, fixture: Path, package: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = evaluate(raw, manifest, fixture, package)
    controls = []
    accept = next((row for row in raw["rows"] if row["expected"] == "accept"), None)
    reject = next((row for row in raw["rows"] if row["expected"] == "reject"), None)
    if accept:
        mutated = copy.deepcopy(raw)
        mutated["rows"][0]["argv_paths_relative_to_fixture"] = {"schema": "../outside/secret", "image": "repo/internal/image.png", "working": "repo/internal/work"}
        controls.append({"control": "mutated accepted argv", "rejected": bool(evaluate(mutated, manifest, fixture, package))})
    if reject:
        mutated = copy.deepcopy(raw)
        bad_row = next(row for row in mutated["rows"] if row["expected"] == "reject")
        bad_row["subprocess_calls"] = 1
        controls.append({"control": "rejected request reaches mock", "rejected": bool(evaluate(mutated, manifest, fixture, package))})
        mutated = copy.deepcopy(raw)
        bad_row = next(row for row in mutated["rows"] if row["expected"] == "reject")
        bad_row["receipt"]["authority_granted"] = True
        controls.append({"control": "authority escalation", "rejected": bool(evaluate(mutated, manifest, fixture, package))})
    control_ok = len(controls) == 3 and all(item["rejected"] for item in controls)
    if not control_ok:
        errors.append("corruption_controls")
    return {"schema": "broker_path_serve_windows_4882_audit_v1",
            "status": "PASS_WINDOWS_SERVE_PATH_BOUNDARY_SCOPED" if not errors else "FAIL_OR_HOLD",
            "rows": len(raw.get("rows", [])), "errors": errors,
            "corruption_controls": controls, "corruption_controls_passed": sum(x["rejected"] for x in controls),
            "fixture_inspected_live": True,
            "scope": "candidate path resolver wired into copied current-main serve() on one native Windows/NTFS fixture; subprocess is mocked"}


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: audit.py RAW.json FIXTURE_MANIFEST.json FIXTURE_DIR AUDIT.json PACKAGE_DIR")
    raw, manifest, fixture, output, package = map(Path, sys.argv[1:])
    report = audit(raw, manifest, fixture, package)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_WINDOWS_SERVE_PATH_BOUNDARY_SCOPED" else 1)
