"""Read-only integrity verification of the frozen 2026-10-04 evidence."""
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
ARCHIVED = {
    "README.md",
    "run_hold_bound_30.py",
    "audit_hold_bound_30.py",
    "audit_repo_sources.py",
    "freeze_hold_bound.py",
    "make_run_receipt.py",
}


def resolve_original(name):
    if name in ARCHIVED:
        return ROOT / "historical_originals" / f"{name}.txt"
    return ROOT / name


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    checks = {}
    manifest = ROOT / "SHA256SUMS.txt"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, name = line.split(maxsplit=1)
        name = name.strip()
        source = resolve_original(name)
        checks[f"manifest:{name}"] = source.is_file() and digest(source) == expected

    freeze = json.loads((ROOT / "PRE-RUN.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        source = resolve_original(name)
        checks[f"freeze:{name}"] = source.is_file() and digest(source) == expected

    raw = json.loads((ROOT / "RAW-30.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "AUDIT.json").read_text(encoding="utf-8"))
    run = json.loads((ROOT / "RUN.json").read_text(encoding="utf-8"))
    checks["run:raw_hash"] = run.get("raw_sha256") == digest(ROOT / "RAW-30.json")
    checks["run:audit_hash"] = run.get("audit_sha256") == digest(ROOT / "AUDIT.json")
    checks["run:identity"] = (
        run.get("run_id") == raw.get("run_id") == freeze.get("run_id")
        and run.get("base_commit") == raw.get("base_commit") == freeze.get("base_commit")
        and run.get("pr_head") == raw.get("pr_head") == freeze.get("pr_head")
    )
    checks["audit:stored_pass"] = audit.get("pass") is True
    checks["audit:30_rows"] = len(raw.get("rows", [])) == 30
    checks["archived_runner_exists"] = resolve_original("run_hold_bound_30.py").is_file()

    failures = [name for name, passed in checks.items() if not passed]
    report = {
        "read_only": True,
        "candidate_executed": False,
        "artifacts_written": False,
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failures": failures,
    }
    print(json.dumps(report, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(verify())
