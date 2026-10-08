"""Independent reconstruction of the V39 release-trace source attribution."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


_V15 = (
    "doom/session_map01_v15.py",
    "doom/doom_typed_release_backend_v2.py",
    "live_control/input_transition_owner_v4.py",
    "live_control/input_owner_v12.py",
)
_TIMING_FIELDS = ("key_release_attempts", "key_release_intervals_ns")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _imports(raw: bytes, wanted: str) -> bool:
    tree = ast.parse(raw.decode("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == wanted:
            return True
        if isinstance(node, ast.Import) and wanted in {alias.name for alias in node.names}:
            return True
    return False


def _independent_result(inputs: Path, freeze: dict) -> dict:
    manifest_raw = (inputs / "sources.json").read_bytes()
    rows_raw = (inputs / "owner-events.json").read_bytes()
    frozen_raw = (inputs / "frozen_tree_sha256.json").read_bytes()
    history_raw = (inputs / "historical_source_refs.json").read_bytes()
    manifest = json.loads(manifest_raw)
    frozen = json.loads(frozen_raw)
    historical = json.loads(history_raw)
    if _digest(manifest_raw) != freeze["run_manifest_sha256"]:
        raise ValueError("source manifest integrity failure")
    if _digest(rows_raw) != freeze["owner_events_sha256"]:
        raise ValueError("owner events integrity failure")
    if _digest(frozen_raw) != freeze["frozen_hash_map_sha256"]:
        raise ValueError("frozen source map integrity failure")
    if _digest(history_raw) != freeze["historical_ref_map_sha256"]:
        raise ValueError("historical ref map integrity failure")
    if len(manifest) != freeze["executed_source_count"] or set(manifest) != set(frozen):
        raise ValueError("source inventory mismatch")

    corpus = inputs / "executed_sources"
    inventory = sorted(str(p.relative_to(corpus)).replace("\\", "/") for p in corpus.rglob("*") if p.is_file())
    if inventory != sorted(manifest):
        raise ValueError("source corpus inventory mismatch")
    for rel, pinned in manifest.items():
        if _digest((corpus / rel).read_bytes()) != pinned:
            raise ValueError(f"source corpus hash mismatch: {rel}")

    same_tree = [rel for rel in manifest if manifest[rel] == frozen[rel]]
    old_tree = []
    for rel, attribution in historical.items():
        if manifest.get(rel) != attribution.get("sha256") or manifest.get(rel) == frozen.get(rel):
            raise ValueError(f"historical source attribution mismatch: {rel}")
        old_tree.append(rel)
    if set(same_tree) | set(old_tree) != set(manifest):
        raise ValueError("unattributed source hash")
    if len(old_tree) != freeze["historical_source_count"]:
        raise ValueError("historical source count mismatch")

    session_raw = (corpus / "doom/session_map01_v12.py").read_bytes()
    backend_raw = (corpus / "doom/doom_typed_release_backend_v1.py").read_bytes()
    owner_raw = (corpus / "live_control/input_owner_v10.py").read_bytes()
    if not _imports(session_raw, "doom_typed_release_backend_v1"):
        raise ValueError("V12 to backend V1 import link missing")
    if not _imports(backend_raw, "input_owner_v10"):
        raise ValueError("backend V1 to owner V10 import link missing")

    event_rows = json.loads(rows_raw)
    releases = [event for event in event_rows if event.get("event") == "owner_release"]
    with_timing = [event for event in releases if any(field in event for field in _TIMING_FIELDS)]
    return {
        "schema": "v39-release-source-attribution-v1",
        "evidence_commit": freeze["evidence_commit"],
        "run_manifest_sha256": freeze["run_manifest_sha256"],
        "owner_events_sha256": freeze["owner_events_sha256"],
        "observed_source_count": len(manifest),
        "frozen_tree_hash_matches": len(same_tree),
        "historical_tree_hash_matches": len(old_tree),
        "historical_source_paths": sorted(old_tree),
        "v15_measurement_sources_present": [path for path in _V15 if path in manifest],
        "v12_backend_owner_chain": [
            "doom/session_map01_v12.py",
            "doom/doom_typed_release_backend_v1.py",
            "live_control/input_owner_v10.py",
        ],
        "v12_imports_v1_backend": True,
        "v1_imports_owner_v10": True,
        "owner_v10_contains_per_key_timing_fields": any(name.encode("ascii") in owner_raw for name in _TIMING_FIELDS),
        "owner_release_rows": len(releases),
        "owner_release_rows_with_per_key_timing": len(with_timing),
        "source_disposition": "V12_BASE_WITHOUT_V15_OVERLAY_IN_RETAINED_MANIFEST",
        "launch_selection_proven": False,
        "limits": [
            "The retained manifest identifies its source bundle but does not include the top-level launcher source or invocation arguments.",
            "No live threat response, physical key state, useful feedback, recovery, or task outcome is tested by this posthoc attribution.",
        ],
    }


def audit_result(inputs: Path, result: dict) -> dict:
    failures = []
    try:
        freeze = _read_json(inputs.parent / "FREEZE.json")
        if freeze.get("schema") != "v39-release-source-attribution-freeze-v1":
            failures.append("freeze_schema")
        try:
            expected = _independent_result(inputs, freeze)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, SyntaxError):
            expected = None
            failures.append("frozen_inputs_reconstruct")
        if expected is not None and result != expected:
            failures.append("result_matches_independent_reconstruction")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        failures.append("freeze_readable")
    checks_total = 3
    checks_passed = checks_total - len(failures)
    return {
        "schema": "v39-release-source-attribution-audit-v1",
        "status": "PASS_SOURCE_ATTRIBUTION" if not failures else "FAIL_SOURCE_ATTRIBUTION",
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "failed_checks": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, default=Path(__file__).parent / "inputs")
    parser.add_argument("--result", type=Path, default=Path(__file__).parent / "RESULT.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "AUDIT.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")
    audit = audit_result(args.inputs, _read_json(args.result))
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
