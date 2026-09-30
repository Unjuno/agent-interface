"""Run deletion-only mutations against the frozen #4448 construction auditor."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CASES = {
    "baseline": None,
    "delete_ephemeral_ready": "scratch/pair-00/EPHEMERAL_XTERM/effects-0.ready.json",
    "delete_resident_done": "scratch/pair-00/RESIDENT_XTERM/effects.done.json",
    "delete_ephemeral_effect": "scratch/pair-00/EPHEMERAL_XTERM/effects-0.jsonl",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_manifest(root: Path) -> dict[str, dict[str, object]]:
    result = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        result[rel] = {"bytes": len(data), "sha256": sha256(data)}
    return result


def manifest_digest(manifest: dict[str, dict[str, object]]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve(strict=True)
    audit = args.audit.resolve(strict=True)
    raw_path = evidence / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    if raw.get("schedule_id") != "construction-20260927-r1":
        raise SystemExit("STOP_SCHEDULE_ID_MISMATCH")
    if (raw.get("formal_invocations") != 0 or len(raw.get("pairs", [])) != 3
            or raw.get("pairs_planned") != 3
            or raw.get("label") != "construction-excluded"):
        raise SystemExit("STOP_EVIDENCE_ALLOCATION_MISMATCH")

    original_manifest = file_manifest(evidence)
    original_digest = manifest_digest(original_manifest)
    audit_bytes = audit.read_bytes()
    output_root = args.out.parent / "case-outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    cases = []
    for case_name, missing_rel in CASES.items():
        with tempfile.TemporaryDirectory(prefix="issue4810-copy-") as temp:
            copied = Path(temp) / "evidence"
            shutil.copytree(evidence, copied)
            if missing_rel is not None:
                target = copied / Path(missing_rel)
                if not target.is_file():
                    raise SystemExit("STOP_MUTATION_TARGET_ABSENT:" + missing_rel)
                target.unlink()
            copied_manifest = file_manifest(copied)
            out_dir = output_root / case_name
            out_dir.mkdir(parents=True, exist_ok=True)
            result_path = out_dir / "audit-result.json"
            command = [
                sys.executable, str(audit), "--evidence", str(copied),
                "--pairs", "3", "--schedule-id", raw["schedule_id"],
                "--mode", "construction", "--output", str(result_path),
            ]
            proc = subprocess.run(command, capture_output=True, check=False)
            (out_dir / "stdout.bin").write_bytes(proc.stdout)
            (out_dir / "stderr.bin").write_bytes(proc.stderr)
            audit_result = json.loads(result_path.read_bytes()) if result_path.exists() else None
            cases.append({
                "case": case_name,
                "missing_path": missing_rel,
                "returncode": proc.returncode,
                "stdout_sha256": sha256(proc.stdout),
                "stderr_sha256": sha256(proc.stderr),
                "stdout_bytes": len(proc.stdout),
                "stderr_bytes": len(proc.stderr),
                "audit_result": audit_result,
                "copy_manifest": copied_manifest,
                "copy_manifest_sha256": manifest_digest(copied_manifest),
            })

    after_manifest = file_manifest(evidence)
    report = {
        "schema": "issue4810-xterm-receipt-deletion-probe-v1",
        "source_commit": "53060eb8c12efdf14a83d0f88969ec93126af0b9",
        "audit_sha256": sha256(audit_bytes),
        "raw_sha256": sha256(raw_bytes),
        "source_evidence_manifest": original_manifest,
        "source_evidence_manifest_sha256": original_digest,
        "source_evidence_unchanged": after_manifest == original_manifest,
        "after_manifest_sha256": manifest_digest(after_manifest),
        "cases": cases,
    }
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "audit_sha256": report["audit_sha256"],
        "raw_sha256": report["raw_sha256"],
        "source_evidence_unchanged": report["source_evidence_unchanged"],
        "cases": [{"case": c["case"], "returncode": c["returncode"],
                   "decision": (c["audit_result"] or {}).get("decision"),
                   "audit_errors": (c["audit_result"] or {}).get("audit_errors"),
                   "missing_path": c["missing_path"]} for c in cases],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
