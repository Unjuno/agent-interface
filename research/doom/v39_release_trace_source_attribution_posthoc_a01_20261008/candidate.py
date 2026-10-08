"""Candidate reduction for the retained V39 release-trace source manifest."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


V15_SOURCES = [
    "doom/session_map01_v15.py",
    "doom/doom_typed_release_backend_v2.py",
    "live_control/input_transition_owner_v4.py",
    "live_control/input_owner_v12.py",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _has_import(source: bytes, module: str) -> bool:
    tree = ast.parse(source.decode("utf-8"))
    return any(
        (isinstance(node, ast.ImportFrom) and node.module == module)
        or (isinstance(node, ast.Import) and any(alias.name == module for alias in node.names))
        for node in ast.walk(tree)
    )


def build_result(inputs: Path) -> dict:
    freeze = _json(inputs.parent / "FREEZE.json")
    sources_bytes = (inputs / "sources.json").read_bytes()
    owner_bytes = (inputs / "owner-events.json").read_bytes()
    frozen_bytes = (inputs / "frozen_tree_sha256.json").read_bytes()
    historic_bytes = (inputs / "historical_source_refs.json").read_bytes()
    if _sha(sources_bytes) != freeze["run_manifest_sha256"]:
        raise ValueError("run source manifest hash mismatch")
    if _sha(owner_bytes) != freeze["owner_events_sha256"]:
        raise ValueError("owner event hash mismatch")
    if _sha(frozen_bytes) != freeze["frozen_hash_map_sha256"]:
        raise ValueError("frozen source hash map mismatch")
    if _sha(historic_bytes) != freeze["historical_ref_map_sha256"]:
        raise ValueError("historical source ref map mismatch")

    observed = json.loads(sources_bytes)
    frozen = json.loads(frozen_bytes)
    historic = json.loads(historic_bytes)
    if set(observed) != set(frozen):
        raise ValueError("frozen hash map does not cover exactly the run source manifest")
    if freeze["executed_source_count"] != len(observed):
        raise ValueError("frozen source count mismatch")

    observed_bundle = inputs / "executed_sources"
    bundle_paths = sorted(
        str(path.relative_to(observed_bundle)).replace("\\", "/")
        for path in observed_bundle.rglob("*") if path.is_file()
    )
    if bundle_paths != sorted(observed):
        raise ValueError("executed source bundle paths do not match the run manifest")
    for rel, expected_sha in observed.items():
        actual_sha = _sha((observed_bundle / rel).read_bytes())
        if actual_sha != expected_sha:
            raise ValueError(f"executed source bundle hash mismatch: {rel}")

    frozen_matches = [rel for rel in observed if observed[rel] == frozen[rel]]
    historic_matches = [
        rel for rel, ref in historic.items()
        if observed.get(rel) == ref.get("sha256") and observed.get(rel) != frozen.get(rel)
    ]
    if set(frozen_matches) | set(historic_matches) != set(observed):
        raise ValueError("one or more executed sources lack a frozen or historical identity")
    if len(historic) != freeze["historical_source_count"]:
        raise ValueError("historical source count mismatch")

    missing_v15 = [name for name in V15_SOURCES if name not in observed]
    session = (observed_bundle / "doom/session_map01_v12.py").read_bytes()
    release_backend = (observed_bundle / "doom/doom_typed_release_backend_v1.py").read_bytes()
    owner_v10 = (observed_bundle / "live_control/input_owner_v10.py").read_bytes()
    if not _has_import(session, "doom_typed_release_backend_v1"):
        raise ValueError("V12 session does not import the V1 release backend")
    if not _has_import(release_backend, "input_owner_v10"):
        raise ValueError("V1 release backend does not import InputOwner V10")

    owner_events = json.loads(owner_bytes)
    release_rows = [row for row in owner_events if row.get("event") == "owner_release"]
    timing_names = {"key_release_attempts", "key_release_intervals_ns"}
    with_per_key = [row for row in release_rows if timing_names.intersection(row)]
    return {
        "schema": "v39-release-source-attribution-v1",
        "evidence_commit": freeze["evidence_commit"],
        "run_manifest_sha256": freeze["run_manifest_sha256"],
        "owner_events_sha256": freeze["owner_events_sha256"],
        "observed_source_count": len(observed),
        "frozen_tree_hash_matches": len(frozen_matches),
        "historical_tree_hash_matches": len(historic_matches),
        "historical_source_paths": sorted(historic_matches),
        "v15_measurement_sources_present": [name for name in V15_SOURCES if name in observed],
        "v12_backend_owner_chain": [
            "doom/session_map01_v12.py",
            "doom/doom_typed_release_backend_v1.py",
            "live_control/input_owner_v10.py",
        ],
        "v12_imports_v1_backend": True,
        "v1_imports_owner_v10": True,
        "owner_v10_contains_per_key_timing_fields": any(
            name.encode("ascii") in owner_v10 for name in timing_names
        ),
        "owner_release_rows": len(release_rows),
        "owner_release_rows_with_per_key_timing": len(with_per_key),
        "source_disposition": "V12_BASE_WITHOUT_V15_OVERLAY_IN_RETAINED_MANIFEST",
        "launch_selection_proven": False,
        "limits": [
            "The retained manifest identifies its source bundle but does not include the top-level launcher source or invocation arguments.",
            "No live threat response, physical key state, useful feedback, recovery, or task outcome is tested by this posthoc attribution.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, default=Path(__file__).parent / "inputs")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "RESULT.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")
    result = build_result(args.inputs)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
