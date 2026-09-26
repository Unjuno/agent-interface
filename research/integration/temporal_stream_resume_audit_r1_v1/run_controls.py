from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_receipts import canonical, sha256

FORMAL_MANIFEST_SHA = "1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855"


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode() + b"\n")


def tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})
    return hashlib.sha256(canonical(rows)).hexdigest()


def load_batch(root: Path, number: int) -> dict:
    return json.loads((root / f"BATCH{number}.json").read_text(encoding="utf-8"))


def save_batch(root: Path, number: int, doc: dict) -> None:
    write_json(root / f"BATCH{number}.json", doc)


def sync_case(row: dict) -> None:
    row["stdout"] = canonical(row["parsed"]).decode() + "\n"


def sync_child(process: dict) -> None:
    process["stdout"] = canonical(process["parsed"]).decode() + "\n"


def update_manifest(root: Path) -> None:
    path = root / "ARTIFACT_MANIFEST.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    for item in doc["artifacts"]:
        target = root / item["path"]
        item["bytes"] = target.stat().st_size
        item["sha256"] = sha256(target)
    write_json(path, doc)


def run_verifier(verifier: Path, source: Path, evidence: Path, pinned: bool = False) -> subprocess.CompletedProcess:
    command = [sys.executable, "-I", "-S", "-B", str(verifier), "--source", str(source), "--evidence", str(evidence)]
    if pinned:
        command.extend(["--expected-manifest-sha256", FORMAL_MANIFEST_SHA])
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def set_batch_value(root: Path, batch: int, row_index: int, change) -> None:
    doc = load_batch(root, batch)
    change(doc, doc["rows"][row_index])
    save_batch(root, batch, doc)


def mutations():
    def incomplete(doc, row):
        doc["complete"] = False

    def duplicate_id(doc, row):
        doc["rows"][1]["parsed"]["case_id"] = 0
        sync_case(doc["rows"][1])

    def candidate_suffix(doc, row):
        row["parsed"]["candidate"]["parsed"]["suffix"][0] = {
            "co_timestamp": "UNKNOWN", "strict_time": "UNKNOWN", "ordered": "UNKNOWN"
        }
        sync_child(row["parsed"]["candidate"])
        sync_case(row)

    def candidate_rc(doc, row):
        row["parsed"]["candidate"]["returncode"] = 9
        sync_case(row)

    def checkpoint_digest(doc, row):
        row["parsed"]["checkpoint"]["prefix_sha256"] = "0" * 64
        sync_case(row)

    def prefix_label(doc, row):
        event = row["parsed"]["prefix"][0]
        event["label"] = "B" if event["label"] != "B" else "A"
        sync_case(row)

    def comparator_status(doc, row):
        row["parsed"]["comparator"]["parsed"]["status"] = "REFUSE_CHECKPOINT"
        sync_child(row["parsed"]["comparator"])
        sync_case(row)

    def authority(doc, row):
        row["parsed"]["authority"] = "input"
        sync_case(row)

    def prepare_rc(doc, row):
        row["parsed"]["prepare"]["returncode"] = 7
        sync_case(row)

    def control_accept(doc, row):
        row["parsed"]["candidate"]["parsed"]["status"] = "OK"
        sync_child(row["parsed"]["candidate"])
        sync_case(row)

    def comparator_rc(doc, row):
        row["parsed"]["comparator"]["returncode"] = 9
        sync_case(row)

    return [
        ("batch_incomplete", 0, 0, incomplete),
        ("duplicate_case_id", 0, 1, duplicate_id),
        ("candidate_suffix", 0, 0, candidate_suffix),
        ("candidate_rc_zero_to_nine", 0, 0, candidate_rc),
        ("checkpoint_digest", 0, 0, checkpoint_digest),
        ("prefix_label", 0, 0, prefix_label),
        ("comparator_status", 0, 0, comparator_status),
        ("authority", 0, 0, authority),
        ("prepare_rc_zero_to_seven", 0, 0, prepare_rc),
        ("control_accept", 5, 0, control_accept),
        ("comparator_rc_zero_to_nine", 0, 0, comparator_rc),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verifier = Path(__file__).with_name("verify_receipts.py")
    source_before, evidence_before = tree_hash(args.source), tree_hash(args.evidence)
    baseline = run_verifier(verifier, args.source, args.evidence, pinned=True)
    baseline_record = {
        "returncode": baseline.returncode,
        "stdout": baseline.stdout.decode(errors="replace"),
        "stderr": baseline.stderr.decode(errors="replace"),
    }
    if baseline.returncode != 0:
        write_json(args.output / "BASE_AUDIT.json", baseline_record)
        return 2

    results = []
    for name, batch, row_index, mutate in mutations():
        with tempfile.TemporaryDirectory(prefix="receipt-audit-copy-") as temporary:
            copy = Path(temporary) / "evidence"
            shutil.copytree(args.evidence, copy)
            before_tree = tree_hash(copy)
            batch_doc = load_batch(copy, batch)
            old_bytes = (copy / f"BATCH{batch}.json").read_bytes()
            mutate(batch_doc, batch_doc["rows"][row_index])
            save_batch(copy, batch, batch_doc)
            update_manifest(copy)
            new_bytes = (copy / f"BATCH{batch}.json").read_bytes()
            after_tree = tree_hash(copy)
            result = run_verifier(verifier, args.source, copy)
            item = {
                "name": name,
                "bytes_changed": old_bytes != new_bytes and before_tree != after_tree,
                "batch_path": f"BATCH{batch}.json",
                "batch_sha256_before": hashlib.sha256(old_bytes).hexdigest(),
                "batch_sha256_after": hashlib.sha256(new_bytes).hexdigest(),
                "copy_tree_sha256": after_tree,
                "manifest_sha256": sha256(copy / "ARTIFACT_MANIFEST.json"),
                "rejected": result.returncode != 0,
                "returncode": result.returncode,
                "stdout": result.stdout.decode(errors="replace"),
                "stderr": result.stderr.decode(errors="replace"),
            }
        item["copy_removed"] = not copy.exists()
        results.append(item)

    original_unchanged = source_before == tree_hash(args.source) and evidence_before == tree_hash(args.evidence)
    effective = sum(item["bytes_changed"] and item["rejected"] for item in results)
    output = {
        "allocation": "temporal-resume-audit-returncode-20260927-01",
        "baseline": baseline_record,
        "mutations": results,
        "effective": effective,
        "original_source_unchanged": source_before == tree_hash(args.source),
        "original_evidence_unchanged": evidence_before == tree_hash(args.evidence),
        "original_tree_hashes_equal": original_unchanged,
    }
    write_json(args.output / "CONTROL_RESULTS.json", output)
    write_json(args.output / "BASE_AUDIT.json", baseline_record)
    passed = len(results) == 11 and effective == 11 and original_unchanged and all(item["copy_removed"] for item in results)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
