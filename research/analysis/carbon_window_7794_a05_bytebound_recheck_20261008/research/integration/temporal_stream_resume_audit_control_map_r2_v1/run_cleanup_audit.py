from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode() + b"\n")


def load_helper(path: Path):
    spec = importlib.util.spec_from_file_location("frozen_control_map_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def invoke(verifier: Path, source: Path, evidence: Path, expected_pin: bool, manifest_sha: str) -> dict:
    command = [sys.executable, "-I", "-S", "-B", str(verifier), "--source", str(source), "--evidence", str(evidence)]
    if expected_pin:
        command.extend(["--expected-manifest-sha256", manifest_sha])
    import subprocess

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.decode(errors="replace"),
        "stderr": result.stderr.decode(errors="replace"),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--helper", type=Path, required=True)
    p.add_argument("--verifier", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--manifest-sha256", required=True)
    p.add_argument("--allocation", default="temporal-resume-control-map-cleanup-20260928-01")
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    args.output.mkdir(parents=True, exist_ok=True)

    helper = load_helper(args.helper)
    source_before, evidence_before = helper.tree_hash(args.source), helper.tree_hash(args.evidence)
    baseline = invoke(args.verifier, args.source, args.evidence, True, args.manifest_sha256)
    write_json(args.output / "BASE_AUDIT.json", baseline)
    if baseline["returncode"] != 0:
        write_json(args.output / "CONTROL_RESULTS.json", {"allocation": args.allocation, "baseline": baseline, "stopped_before_controls": True})
        return 2

    controls = []
    for name in helper.ORIGINAL_MUTATIONS + ["comparator_rc"]:
        with tempfile.TemporaryDirectory(prefix="cleanup-audit-copy-") as temporary:
            root = Path(temporary) / "evidence"
            import shutil

            shutil.copytree(args.evidence, root)
            tree_before = helper.tree_hash(root)
            batch = 5 if name == "control_accept_case48" else 0
            bytes_before = (root / f"BATCH{batch}.json").read_bytes()
            identity = helper.mutate(name, root)
            bytes_changed = bytes_before != (root / f"BATCH{batch}.json").read_bytes() and tree_before != helper.tree_hash(root)
            receipt = invoke(args.verifier, args.source, root, False, args.manifest_sha256)
            item = {
                "name": name,
                **identity,
                "bytes_changed": bytes_changed,
                "copy_tree_sha256": helper.tree_hash(root),
                "manifest_sha256": hashlib.sha256((root / "ARTIFACT_MANIFEST.json").read_bytes()).hexdigest(),
                "rejected": receipt["returncode"] != 0,
                "verifier": receipt,
                "copy_exists_inside_scope": root.exists(),
            }
        item["copy_exists_after_scope"] = root.exists()
        item["copy_removed_after_scope"] = not root.exists()
        controls.append(item)

    with tempfile.TemporaryDirectory(prefix="cleanup-audit-positive-") as temporary:
        root = Path(temporary) / "evidence"
        import shutil

        shutil.copytree(args.evidence, root)
        original_tree = helper.tree_hash(root)
        positive_receipt = invoke(args.verifier, args.source, root, False, args.manifest_sha256)
        positive = {
            "name": "positive_accept_unchanged",
            "tree_sha256_before": original_tree,
            "tree_sha256_after": helper.tree_hash(root),
            "bytes_changed": False,
            "tree_hash_unchanged_inside_scope": original_tree == helper.tree_hash(root),
            "rejected": positive_receipt["returncode"] != 0,
            "verifier": positive_receipt,
            "copy_exists_inside_scope": root.exists(),
        }
    positive["copy_exists_after_scope"] = root.exists()
    positive["copy_removed_after_scope"] = not root.exists()

    result = {
        "allocation": args.allocation,
        "baseline": baseline,
        "mutations": controls,
        "positive_control": positive,
        "original_source_tree_sha256_before": source_before,
        "original_source_tree_sha256_after": helper.tree_hash(args.source),
        "original_evidence_tree_sha256_before": evidence_before,
        "original_evidence_tree_sha256_after": helper.tree_hash(args.evidence),
    }
    write_json(args.output / "CONTROL_RESULTS.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
