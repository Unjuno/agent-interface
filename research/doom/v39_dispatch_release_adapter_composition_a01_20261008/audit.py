"""Independent audit of the dispatch-to-release-feedback composition result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_result(result: dict, manifest: dict, freeze: dict, snapshot_root: Path | None = None) -> dict:
    if result.get("schema") != "v39-dispatch-release-adapter-composition-result-v1":
        raise ValueError("result schema mismatch")
    if result.get("disposition") != "PASS_SOURCE_BOUND_SYNTHETIC_COMPOSITION_ONLY":
        raise ValueError("composition disposition mismatch")
    if (result.get("latest_main_at_freeze") != freeze.get("latest_main_at_freeze")
            or result.get("source_commit_used_by_component_harnesses") != freeze.get("source_commit_used_by_existing_candidates")):
        raise ValueError("main/source freeze identity mismatch")
    selected = result.get("selected_command", {})
    if (Path(selected.get("session_path", "")).name != "session_map01_v15.py"
            or selected.get("report_label") != "v15_scorer_only_per_key_release"
            or selected.get("seed") != "990605"):
        raise ValueError("measurement dispatch did not select the expected V15 route")
    chain = result.get("measurement_mode", {})
    if (chain.get("session_path") != "research/doom/session_map01_v15.py"
            or chain.get("per_key_fields") != ["key_release_attempts", "key_release_intervals_ns"]):
        raise ValueError("selected V15 route is missing its per-key source chain")

    normalized = {key.replace("\\", "/"): value for key, value in manifest.items()}
    expected_keys = set(freeze["per_key_source_manifest_keys"])
    if not expected_keys.issubset(normalized):
        raise ValueError("source manifest omits per-key release sources")
    for source_key in freeze["v15_manifest_source_keys"]:
        expected_hash = result.get("source_snapshot_sha256", {}).get(source_key)
        if not expected_hash:
            raise ValueError(f"source snapshot hash missing: {source_key}")
        manifest_key = source_key.removeprefix("research/")
        if normalized.get(manifest_key) != expected_hash:
            raise ValueError(f"source manifest hash mismatch: {source_key}")
        if snapshot_root is not None and sha(snapshot_root / source_key) != expected_hash:
            raise ValueError(f"source snapshot bytes mismatch: {source_key}")
    for candidate_path, expected_hash in freeze["candidate_inputs"].items():
        if result.get("source_identities", {}).get(candidate_path) != expected_hash:
            raise ValueError(f"candidate input identity mismatch: {candidate_path}")
    if result.get("v15_manifest", {}).get("entry_count") != len(freeze["v15_manifest_source_keys"]):
        raise ValueError("V15 manifest entry count mismatch")
    for source_key in freeze["per_key_source_manifest_keys"]:
        if normalized[source_key] != result["v15_manifest"]["per_key_source_keys"][source_key]:
            raise ValueError("normalized manifest value changed")

    feedback = result.get("release_to_feedback_adapter", {})
    complete = feedback.get("complete_batch", {})
    before = feedback.get("before_accept_failure", {})
    after = feedback.get("after_accept_failure", {})
    if not (
        complete.get("trace_integrity") == "SOURCE_ROWS_JOINED"
        and complete.get("attribution") == "TEMPORALLY_UNIQUE"
        and complete.get("causal_attribution") == "NOT_ESTABLISHED"
    ):
        raise ValueError("complete batch attribution scope mismatch")
    if not (
        before.get("producer_ledger") == ["confirmed", "unknown"]
        and before.get("visible_rows") == 1
        and before.get("trace_integrity") == "HOLD_INCOMPLETE_RELEASE_BATCH"
        and before.get("attribution") == "UNRESOLVED"
    ):
        raise ValueError("pre-accept publication failure did not fail closed")
    if not (
        after.get("producer_ledger") == ["confirmed", "unknown"]
        and after.get("visible_rows") == 2
        and after.get("delivery_positions") == [0, 1]
        and after.get("trace_integrity") == "SOURCE_ROWS_JOINED"
        and after.get("attribution") == "TEMPORALLY_UNIQUE"
        and after.get("causal_attribution") == "NOT_ESTABLISHED"
    ):
        raise ValueError("post-accept acknowledgment was overclaimed")
    if "no session or OS input" not in result.get("scope", ""):
        raise ValueError("scope boundary missing")
    return {"status": "PASS_SOURCE_BOUND_COMPOSITION", "checks_passed": 10, "checks_total": 10}


def audit(out_dir: Path) -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    result_path = out_dir / "result.json"
    manifest_path = out_dir / "sources.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha(manifest_path) != result["v15_manifest"]["sha256"]:
        raise ValueError("source manifest byte hash mismatch")
    for relpath, expected in freeze["candidate_inputs"].items():
        if sha(HERE / "candidate_inputs" / relpath) != expected:
            raise ValueError(f"candidate input changed: {relpath}")
    for relpath, expected in freeze["production_source_blobs"].items():
        if result["source_identities"].get(relpath) != expected:
            raise ValueError(f"production source identity mismatch: {relpath}")
    verified = validate_result(result, manifest, freeze, out_dir / "source_snapshot")
    return {
        "schema": "v39-dispatch-release-adapter-composition-audit-v1",
        **verified,
        "result_sha256": sha(result_path),
        "manifest_sha256": sha(manifest_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit(args.out_dir)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite audit receipt: {args.output}")
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
