#!/usr/bin/env python3
"""Run the frozen A04 summary-field auditor corruption follow-up once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PKG = Path(__file__).resolve().parent
ROOT = next(p for p in PKG.parents if (p / ".git").exists())
SOURCE = ROOT / "research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
PYTHON = sys.executable


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(argv, stdout_path, exit_path):
    completed = subprocess.run(argv, cwd=PKG, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
    stdout_path.write_bytes(completed.stdout)
    stdout_path.with_suffix(".stderr.txt").write_bytes(completed.stderr)
    exit_path.write_text(f"{completed.returncode}\n", encoding="utf-8")
    return completed.returncode


def main():
    raw_dir = PKG / "raw"
    raw_dir.mkdir(exist_ok=True)
    raw = SOURCE.read_bytes()
    candidate_bytes = (PKG / "PARENT_ANALYZE.py").read_bytes()
    auditor_bytes = (PKG / "PARENT_AUDIT.py").read_bytes()
    if sha(raw) != FREEZE["input_sha256"]:
        raise SystemExit("STOP_INPUT_HASH_MISMATCH")
    if sha(candidate_bytes) != FREEZE["candidate_sha256"]:
        raise SystemExit("STOP_CANDIDATE_HASH_MISMATCH")
    if sha(auditor_bytes) != FREEZE["original_auditor_sha256"]:
        raise SystemExit("STOP_AUDITOR_HASH_MISMATCH")

    candidate_exit = command(
        [PYTHON, str(PKG / "PARENT_ANALYZE.py")],
        raw_dir / "PARENT_CANDIDATE.stdout.txt",
        raw_dir / "PARENT_CANDIDATE.exit.txt")
    if candidate_exit != 0:
        raise SystemExit("STOP_PARENT_CANDIDATE_FAILED")
    pristine_audit_exit = command(
        [PYTHON, str(PKG / "PARENT_AUDIT.py")],
        raw_dir / "PARENT_AUDITOR_PRISTINE.stdout.txt",
        raw_dir / "PARENT_AUDITOR_PRISTINE.exit.txt")
    if pristine_audit_exit != 0:
        raise SystemExit("STOP_PARENT_AUDITOR_PRISTINE_FAILED")
    pristine_v2_exit = command(
        [PYTHON, str(PKG / "audit_v2.py")],
        raw_dir / "AUDIT_V2_PRISTINE.stdout.txt",
        raw_dir / "AUDIT_V2_PRISTINE.exit.txt")

    pristine = json.loads((PKG / "RESULT.json").read_text(encoding="utf-8"))
    mutations = []
    for field, replacement in (("unique", 0), ("ambiguous", 0), ("unmatched", 39)):
        case_dir = PKG / "corruptions" / field
        case_dir.mkdir(parents=True, exist_ok=True)
        corrupt = json.loads(json.dumps(pristine))
        original = corrupt[field]
        corrupt[field] = replacement
        result_path = case_dir / "RESULT.json"
        result_path.write_text(json.dumps(corrupt, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
        shutil.copyfile(PKG / "PARENT_AUDIT.py", case_dir / "PARENT_AUDIT.py")
        original_exit = command(
            [PYTHON, str(case_dir / "PARENT_AUDIT.py")],
            raw_dir / f"ORIGINAL_AUDITOR_{field}.stdout.txt",
            raw_dir / f"ORIGINAL_AUDITOR_{field}.exit.txt")
        v2_exit = command(
            [PYTHON, str(PKG / "audit_v2.py"), "--result", str(result_path),
             "--output", str(case_dir / "AUDIT_V2.json")],
            raw_dir / f"AUDIT_V2_{field}.stdout.txt",
            raw_dir / f"AUDIT_V2_{field}.exit.txt")
        mutations.append({
            "field": field, "original": original, "mutated": replacement,
            "original_auditor_exit": original_exit,
            "v2_auditor_exit": v2_exit,
            "original_auditor_false_accept": original_exit == 0,
            "v2_rejected": v2_exit != 0,
        })

    gap = all(row["original_auditor_false_accept"] for row in mutations)
    repair = pristine_v2_exit == 0 and all(row["v2_rejected"] for row in mutations)
    run = {
        "schema": "map01-a04-summary-audit-followup-run-v1",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": sha(raw),
        "candidate_exit": candidate_exit,
        "pristine_original_auditor_exit": pristine_audit_exit,
        "pristine_v2_auditor_exit": pristine_v2_exit,
        "summary_mutations": mutations,
        "gap_reproduced": gap,
        "v2_rejects_all_mutations": repair,
        "decision": ("PASS_AUDIT_GAP_REPRODUCED_AND_REPAIR_TESTED"
                     if gap and repair else "FAIL_OR_HOLD"),
        "scope": "deterministic posthoc raw/result audit only; no live control or physical timing claim",
    }
    (PKG / "RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
    print(json.dumps(run, indent=2, sort_keys=True))
    return 0 if run["decision"] == "PASS_AUDIT_GAP_REPRODUCED_AND_REPAIR_TESTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
