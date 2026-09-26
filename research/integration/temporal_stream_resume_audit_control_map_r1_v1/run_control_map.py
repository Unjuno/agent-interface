from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


EVIDENCE_MANIFEST_SHA = "1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855"
ALLOCATION = "temporal-resume-control-map-20260927-01"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return hashlib.sha256(canonical(rows)).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode() + b"\n")


def load_batch(root: Path, number: int) -> dict:
    return json.loads((root / f"BATCH{number}.json").read_text(encoding="utf-8"))


def sync_case(row: dict) -> None:
    row["stdout"] = canonical(row["parsed"]).decode() + "\n"


def sync_child(child: dict) -> None:
    child["stdout"] = canonical(child["parsed"]).decode() + "\n"


def update_manifest(root: Path) -> None:
    path = root / "ARTIFACT_MANIFEST.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for item in manifest["artifacts"]:
        target = root / item["path"]
        item["bytes"] = target.stat().st_size
        item["sha256"] = sha256(target)
    write_json(path, manifest)


def row_for_case(doc: dict, case_id: int) -> dict:
    matches = [row for row in doc["rows"] if row.get("case_id") == case_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one case_id={case_id}; found {len(matches)}")
    return matches[0]


def mutate(name: str, root: Path) -> dict:
    batch = 5 if name == "control_accept_case48" else 0
    doc = load_batch(root, batch)
    row = row_for_case(doc, 48) if name == "control_accept_case48" else row_for_case(doc, 0 if name != "duplicate_case_id" else 1)
    if name == "batch_incomplete":
        doc["complete"] = False
    elif name == "duplicate_case_id":
        row["parsed"]["case_id"] = 0
        sync_case(row)
    elif name == "candidate_suffix":
        row["parsed"]["candidate"]["parsed"]["suffix"][0] = {"co_timestamp": "UNKNOWN", "strict_time": "UNKNOWN", "ordered": "UNKNOWN"}
        sync_child(row["parsed"]["candidate"])
        sync_case(row)
    elif name == "candidate_rc":
        row["parsed"]["candidate"]["returncode"] = 9
        sync_case(row)
    elif name == "checkpoint_digest":
        row["parsed"]["checkpoint"]["prefix_sha256"] = "0" * 64
        sync_case(row)
    elif name == "prefix_label":
        event = row["parsed"]["prefix"][0]
        event["label"] = "B" if event["label"] != "B" else "A"
        sync_case(row)
    elif name == "comparator_status":
        row["parsed"]["comparator"]["parsed"]["status"] = "REFUSE_CHECKPOINT"
        sync_child(row["parsed"]["comparator"])
        sync_case(row)
    elif name == "authority":
        row["parsed"]["authority"] = "input"
        sync_case(row)
    elif name == "prepare_rc":
        row["parsed"]["prepare"]["returncode"] = 7
        sync_case(row)
    elif name == "control_accept_case48":
        if row["parsed"]["mutation"] != "foreign_epoch" or row["parsed"]["candidate"]["parsed"]["status"] != "REFUSE_CHECKPOINT":
            raise ValueError("case_id=48 no longer matches frozen original control precondition")
        row["parsed"]["candidate"]["parsed"]["status"] = "OK"
        sync_child(row["parsed"]["candidate"])
        sync_case(row)
    elif name == "comparator_rc":
        row["parsed"]["comparator"]["returncode"] = 9
        sync_case(row)
    else:
        raise ValueError(f"unknown mutation {name}")
    write_json(root / f"BATCH{batch}.json", doc)
    update_manifest(root)
    return {"batch": batch, "case_id": row.get("case_id"), "identity_asserted": name == "control_accept_case48"}


ORIGINAL_MUTATIONS = [
    "batch_incomplete", "duplicate_case_id", "candidate_suffix", "candidate_rc",
    "checkpoint_digest", "prefix_label", "comparator_status", "authority",
    "prepare_rc", "control_accept_case48",
]


def invoke(verifier: Path, source: Path, evidence: Path, expected_pin: bool) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-I", "-S", "-B", str(verifier), "--source", str(source), "--evidence", str(evidence)]
    if expected_pin:
        cmd.extend(["--expected-manifest-sha256", EVIDENCE_MANIFEST_SHA])
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_before, evidence_before = tree_hash(args.source), tree_hash(args.evidence)
    baseline = invoke(args.verifier, args.source, args.evidence, expected_pin=True)
    baseline_doc = {"returncode": baseline.returncode, "stdout": baseline.stdout.decode(errors="replace"), "stderr": baseline.stderr.decode(errors="replace")}
    if baseline.returncode != 0:
        write_json(args.output / "BASE_AUDIT.json", baseline_doc)
        write_json(args.output / "CONTROL_RESULTS.json", {"allocation": ALLOCATION, "baseline": baseline_doc, "stopped_before_controls": True})
        return 2

    outcomes = []
    for name in ORIGINAL_MUTATIONS + ["comparator_rc"]:
        with tempfile.TemporaryDirectory(prefix="control-map-copy-") as temporary:
            copy = Path(temporary) / "evidence"
            shutil.copytree(args.evidence, copy)
            before = tree_hash(copy)
            batch = 5 if name == "control_accept_case48" else 0
            original_bytes = (copy / f"BATCH{batch}.json").read_bytes()
            identity = mutate(name, copy)
            changed = original_bytes != (copy / f"BATCH{batch}.json").read_bytes() and before != tree_hash(copy)
            result = invoke(args.verifier, args.source, copy, expected_pin=False)
            item = {
                "name": name, **identity, "bytes_changed": changed,
                "copy_tree_sha256": tree_hash(copy),
                "manifest_sha256": sha256(copy / "ARTIFACT_MANIFEST.json"),
                "rejected": result.returncode != 0, "returncode": result.returncode,
                "stdout": result.stdout.decode(errors="replace"), "stderr": result.stderr.decode(errors="replace"),
            }
        item["copy_removed"] = not copy.exists()
        outcomes.append(item)

    with tempfile.TemporaryDirectory(prefix="control-map-positive-") as temporary:
        copy = Path(temporary) / "evidence"
        shutil.copytree(args.evidence, copy)
        original_tree = tree_hash(copy)
        result = invoke(args.verifier, args.source, copy, expected_pin=False)
        positive = {
            "name": "positive_accept_unchanged", "bytes_changed": False,
            "tree_hash_unchanged": original_tree == tree_hash(copy),
            "rejected": result.returncode != 0, "returncode": result.returncode,
            "copy_removed": not copy.exists(),
            "stdout": result.stdout.decode(errors="replace"), "stderr": result.stderr.decode(errors="replace"),
        }

    originals_unchanged = source_before == tree_hash(args.source) and evidence_before == tree_hash(args.evidence)
    effective = sum(x["bytes_changed"] and x["rejected"] for x in outcomes)
    result = {
        "allocation": ALLOCATION, "baseline": baseline_doc, "mutations": outcomes,
        "positive_control": positive, "effective": effective,
        "original_source_unchanged": source_before == tree_hash(args.source),
        "original_evidence_unchanged": evidence_before == tree_hash(args.evidence),
        "original_tree_hashes_equal": originals_unchanged,
    }
    write_json(args.output / "BASE_AUDIT.json", baseline_doc)
    write_json(args.output / "CONTROL_RESULTS.json", result)
    passed = (
        len(outcomes) == 11 and effective == 11
        and all(x["bytes_changed"] and x["rejected"] and x["copy_removed"] for x in outcomes)
        and outcomes[9]["case_id"] == 48 and outcomes[9]["identity_asserted"]
        and positive["bytes_changed"] is False and positive["tree_hash_unchanged"]
        and positive["rejected"] is False and positive["returncode"] == 0 and positive["copy_removed"]
        and originals_unchanged
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
