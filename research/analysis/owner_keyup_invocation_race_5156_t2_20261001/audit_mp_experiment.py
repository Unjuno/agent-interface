from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SHA = re.compile(r"[0-9a-f]{64}\Z")


def audit(raw: dict, package: Path) -> list[str]:
    errors: list[str] = []
    if raw.get("schema") != "issue5156_multiprocess_exclusive_claim_t2_v1":
        errors.append("schema mismatch")
    if raw.get("docker_invocations") != 0 or raw.get("x11_input_invocations") != 0 or raw.get("model_calls") != 0:
        errors.append("scope violation")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != 40:
        errors.append("expected 40 trial rows")
        rows = rows if isinstance(rows, list) else []
    by_arm = {arm: [] for arm in ("baseline", "exclusive")}
    for row in rows:
        arm = row.get("mode")
        if arm not in by_arm:
            errors.append("unknown arm")
            continue
        by_arm[arm].append(row)
        expected_statuses = [0, 0] if arm == "baseline" else [0, 2]
        expected_candidates = 2 if arm == "baseline" else 1
        if row.get("statuses") != expected_statuses:
            errors.append(f"{arm} trial status mismatch")
        if row.get("candidate_count") != expected_candidates:
            errors.append(f"{arm} trial receipt count mismatch")
        if len(row.get("candidate_receipts", [])) != expected_candidates:
            errors.append(f"{arm} trial receipt inventory mismatch")
        if row.get("worker_exitcodes") != [0, 0]:
            errors.append(f"{arm} worker exit mismatch")
        if row.get("claim_exists") != (arm == "exclusive"):
            errors.append(f"{arm} claim presence mismatch")
        trial_path = package / "results" / "trials" / f"{arm}-{row.get('trial', -1):02d}"
        actual = sorted(p.name for p in trial_path.glob("candidate-*"))
        if actual != row.get("candidate_receipts"):
            errors.append(f"{arm} retained receipts disagree with raw")
        if (trial_path / "CLAIM").is_file() != (arm == "exclusive"):
            errors.append(f"{arm} retained claim disagrees with raw")
    for arm, arm_rows in by_arm.items():
        if len(arm_rows) != 20 or sorted(r.get("trial") for r in arm_rows) != list(range(20)):
            errors.append(f"{arm} trial index/count mismatch")
    expected = raw.get("source_sha256", {})
    required = ("PLAN.md", "test_mp_race.py", "run_mp_experiment.py", "audit_mp_experiment.py")
    for name in required:
        digest = expected.get(name)
        if not isinstance(digest, str) or not SHA.fullmatch(digest):
            errors.append(f"invalid/missing source hash: {name}")
        elif hashlib.sha256((package / name).read_bytes()).hexdigest() != digest:
            errors.append(f"source hash mismatch: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    errors = audit(raw, args.raw.parent.parent)
    result = {
        "decision": "PASS_MULTIPROCESS_CLAIM_BOUNDARY_SCOPED" if not errors else "FAIL_CLOSED",
        "raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest(),
        "trials": len(raw.get("rows", [])),
        "errors": errors,
    }
    if args.output.exists():
        raise SystemExit("refusing to overwrite audit; no retry")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
