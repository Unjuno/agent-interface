"""Compose V39 measurement dispatch, V15 provenance, release publisher, and adapter."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
VENDORED = HERE / "candidate_inputs"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(alias: str, relpath: str):
    path = VENDORED / relpath
    spec = importlib.util.spec_from_file_location(alias, path)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


def verify_sources(output_dir: Path) -> tuple[dict[str, str], Path]:
    result = {}
    snapshot = output_dir / "source_snapshot"
    for relpath, expected in FREEZE["production_source_blobs"].items():
        blob = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", f"{FREEZE['local_main_source_check_ref']}:{relpath}"],
            text=True,
        ).strip()
        raw = subprocess.check_output(
            ["git", "-C", str(REPO), "show", f"{FREEZE['local_main_source_check_ref']}:{relpath}"]
        )
        raw_blob = subprocess.check_output(
            ["git", "-C", str(REPO), "hash-object", "--stdin"], input=raw, text=False
        ).decode().strip()
        if blob != expected or raw_blob != expected:
            raise ValueError(f"production source drift: {relpath}")
        target = snapshot / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        result[relpath] = blob
    for relpath, expected in FREEZE["candidate_inputs"].items():
        actual = sha256(VENDORED / relpath)
        if actual != expected:
            raise ValueError(f"candidate input drift: {relpath}")
        result[relpath] = actual
    return result, snapshot


def selected_v15_command(dispatch) -> dict:
    local, parser, report_expr = dispatch.controller_contract()
    args = parser.parse_args(["--measurement-session"])
    args.seed = 990605
    args.load_fixture_manifest = REPO / "fixture-manifest.json"
    runtime = HERE / "synthetic-measurement-session"
    command = local["session_command"](args, runtime)
    label = eval(compile(ast.Expression(report_expr), "frozen-v39-report-label", "eval"), {"args": args})
    if Path(command[1]).name != "session_map01_v15.py":
        raise AssertionError("measurement flag did not select V15")
    if label != "v15_scorer_only_per_key_release":
        raise AssertionError("V15 report label does not match selected command")
    return {
        "mode": "measurement",
        "session_path": str(Path(command[1]).resolve()),
        "report_label": label,
        "seed": command[command.index("--seed") + 1],
        "output": command[command.index("--out") + 1],
        "command_arguments": command,
    }


def merge_v15_manifest(output_dir: Path, snapshot: Path) -> tuple[dict, str]:
    session_path = snapshot / "research/doom/session_map01_v15.py"
    module_ast = ast.parse(session_path.read_text(encoding="utf-8"))
    merge = next(
        node for node in module_ast.body
        if isinstance(node, ast.FunctionDef) and node.name == "_merge_sources"
    )
    manifest_path = output_dir / "sources.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    scope = {
        "Path": Path,
        "json": json,
        "hashlib": hashlib,
        "_sha": lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "HERE": snapshot / "research/doom",
        "RESEARCH": snapshot / "research",
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[merge], type_ignores=[])), str(session_path), "exec"), scope)
    if scope["_merge_sources"](output_dir) is not True:
        raise AssertionError("V15 did not merge the source manifest")
    host_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = {key.replace("\\", "/"): value for key, value in host_manifest.items()}
    expected = set(FREEZE["per_key_source_manifest_keys"])
    if not expected.issubset(manifest):
        raise AssertionError("V15 manifest omitted a required per-key release source")
    expected_sha = {
        "doom/doom_owner_thread_release_batch_backend_v1.py": FREEZE["production_source_blobs"]["research/doom/doom_owner_thread_release_batch_backend_v1.py"],
        "doom/doom_typed_release_backend_v2.py": FREEZE["production_source_blobs"]["research/doom/doom_typed_release_backend_v2.py"],
        "live_control/input_transition_owner_v4.py": FREEZE["production_source_blobs"]["research/live_control/input_transition_owner_v4.py"],
        "live_control/input_owner_v12.py": FREEZE["production_source_blobs"]["research/live_control/input_owner_v12.py"],
    }
    for path, blob in expected_sha.items():
        file_path = snapshot / "research" / path
        if manifest[path] != sha256(file_path):
            raise AssertionError(f"V15 source manifest hash mismatch: {path}")
    return manifest, sha256(manifest_path)


def compose_release_feedback(t6, t7) -> dict:
    complete_rows = t6.exact_published_rows()
    complete = t6.adapt(complete_rows)
    if (complete["trace_integrity"] != "SOURCE_ROWS_JOINED"
            or complete["attributions"][0]["status"] != "TEMPORALLY_UNIQUE"
            or complete["attributions"][0]["causal_attribution"] != "NOT_ESTABLISHED"):
        raise AssertionError("complete V15 publisher rows failed adapter join")

    missing_rows, missing_ledger = t7.publication_attempt(False)
    missing = t6.adapt(missing_rows)
    if (len(missing_rows) != 1
            or [row["state"] for row in missing_ledger["positions"]] != ["confirmed", "unknown"]
            or missing["trace_integrity"] != "HOLD_INCOMPLETE_RELEASE_BATCH"
            or missing["attributions"][0]["status"] != "UNRESOLVED"):
        raise AssertionError("pre-acceptance missing row did not fail closed")

    accepted_rows, accepted_ledger = t7.publication_attempt(True)
    ambiguous = t6.adapt(accepted_rows)
    if (len(accepted_rows) != 2
            or [row["state"] for row in accepted_ledger["positions"]] != ["confirmed", "unknown"]
            or [row["release_batch_delivery_position"] for row in accepted_rows] != [0, 1]
            or ambiguous["trace_integrity"] != "SOURCE_ROWS_JOINED"
            or ambiguous["attributions"][0]["status"] != "TEMPORALLY_UNIQUE"
            or ambiguous["attributions"][0]["causal_attribution"] != "NOT_ESTABLISHED"):
        raise AssertionError("post-acceptance ambiguous acknowledgment escaped row-scoped attribution")

    return {
        "complete_batch": {
            "release_rows": len(complete_rows),
            "delivery_positions": [row["release_batch_delivery_position"] for row in complete_rows],
            "trace_integrity": complete["trace_integrity"],
            "attribution": complete["attributions"][0]["status"],
            "causal_attribution": complete["attributions"][0]["causal_attribution"],
        },
        "before_accept_failure": {
            "visible_rows": len(missing_rows),
            "producer_ledger": [row["state"] for row in missing_ledger["positions"]],
            "trace_integrity": missing["trace_integrity"],
            "attribution": missing["attributions"][0]["status"],
        },
        "after_accept_failure": {
            "visible_rows": len(accepted_rows),
            "producer_ledger": [row["state"] for row in accepted_ledger["positions"]],
            "delivery_positions": [row["release_batch_delivery_position"] for row in accepted_rows],
            "trace_integrity": ambiguous["trace_integrity"],
            "attribution": ambiguous["attributions"][0]["status"],
            "causal_attribution": ambiguous["attributions"][0]["causal_attribution"],
        },
    }


def run_case(output_dir: Path) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse output: {output_dir}")
    output_dir.mkdir(parents=True)
    sources, snapshot = verify_sources(output_dir)
    dispatch = module("frozen_dispatch", "research/doom/v39_measurement_dispatch_a01_20261008/run.py")
    t6 = module("frozen_release_t6", "research/doom/v15_release_batch_t6_20261008/run.py")
    t7 = module("frozen_release_t7", "research/doom/v15_release_batch_t7_20261008/run.py")
    # The component runners are vendored under a synthetic repository-shaped
    # tree. Point their production readers at the verified source snapshot.
    dispatch.REPO = REPO
    dispatch.MAIN = FREEZE["source_commit_used_by_existing_candidates"]
    t6.REPO = REPO
    t6.BACKEND = snapshot / "research/doom/doom_owner_thread_release_batch_backend_v1.py"
    t7.REPO = REPO
    t7.BACKEND_PATH = t6.BACKEND
    command = selected_v15_command(dispatch)
    manifest, manifest_hash = merge_v15_manifest(output_dir, snapshot)
    chain = dispatch.evidence_chain()
    if chain["session_path"] != "research/doom/session_map01_v15.py":
        raise AssertionError("static V15 chain does not match selected session")
    release_feedback = compose_release_feedback(t6, t7)
    result = {
        "schema": "v39-dispatch-release-adapter-composition-result-v1",
        "disposition": "PASS_SOURCE_BOUND_SYNTHETIC_COMPOSITION_ONLY",
        "latest_main_at_freeze": FREEZE["latest_main_at_freeze"],
        "source_commit_used_by_component_harnesses": FREEZE["source_commit_used_by_existing_candidates"],
        "source_identities": sources,
        "source_snapshot_sha256": {
            path: sha256(snapshot / path)
            for path in FREEZE["v15_manifest_source_keys"]
        },
        "selected_command": command,
        "measurement_mode": chain,
        "v15_manifest": {
            "sha256": manifest_hash,
            "entry_count": len(manifest),
            "per_key_source_keys": {
                path: manifest[path] for path in FREEZE["per_key_source_manifest_keys"]
            },
        },
        "release_to_feedback_adapter": release_feedback,
        "scope": "exact V39 command helper and V15 manifest merger composed with pinned current-main release publication methods and T5 adapter; synthetic owner/scorer/sink; no session or OS input",
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_case(args.out_dir.resolve()), sort_keys=True))
