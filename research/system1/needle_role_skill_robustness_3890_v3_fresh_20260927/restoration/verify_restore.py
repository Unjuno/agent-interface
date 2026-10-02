"""Restore the preserved #4580 raw bundles and replay its frozen audit."""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
SNAPSHOT = BASE / "restoration_snapshot"
FORMAL = BASE / "outputs" / "formal01"
BUNDLES = FORMAL / "bundles"
REPORT = FORMAL / "RESTORE_AUDIT.json"
EXPECTED_MEMBERS = [
    "builder/skill.json", "builder/expected.json", "load1/loader.json",
    "load2/loader.json", "builder.log", "load1.log", "load2.log",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    freeze = json.loads((SNAPSHOT / "FREEZE.json").read_bytes())
    manifest = json.loads((BUNDLES / "EVIDENCE_MANIFEST.json").read_bytes())
    expected_seeds = freeze["seeds"]
    if [row["seed"] for row in manifest] != expected_seeds:
        raise SystemExit("STOP:bundle_seed_schedule")

    archive_hashes = {}
    archive_bytes = 0
    with tempfile.TemporaryDirectory(prefix="needle4580-repository-restore-") as tmp:
        restored = Path(tmp)
        for row in manifest:
            name = row["path"]
            if name != f"seed-{row['seed']}.zip" or row["members"] != EXPECTED_MEMBERS:
                raise SystemExit(f"STOP:bundle_manifest:{name}")
            raw = (BUNDLES / name).read_bytes()
            if len(raw) != row["bytes"] or sha(raw) != row["sha256"]:
                raise SystemExit(f"STOP:bundle_hash:{name}")
            with zipfile.ZipFile(BUNDLES / name) as archive:
                if archive.testzip() is not None or archive.namelist() != EXPECTED_MEMBERS:
                    raise SystemExit(f"STOP:bundle_zip_integrity:{name}")
                archive.extractall(restored / f"seed-{row['seed']}")
            archive_hashes[name] = row["sha256"]
            archive_bytes += len(raw)

        shutil.copy2(FORMAL / "FORMAL_RUN.json", restored / "FORMAL_RUN.json")
        sys.path.insert(0, str(SNAPSHOT))
        import audit_saved_run  # exact retained post-run auditor; imports snapshot audit_v3

        audit = audit_saved_run.audit_saved(restored, SNAPSHOT / "source", freeze)

    audit_sha = sha((SNAPSHOT / "audit_v3.py").read_bytes())
    result = {
        "schema": "needle-role-skill-robustness-evidence-restoration-v1",
        "issue": 4580,
        "allocation": freeze["allocation"],
        "status": "PASS_EVIDENCE_RESTORATION_SCOPED" if not audit["errors"] else "FAIL_OR_STOP_AUDIT",
        "formal_candidate_invocations_added": 0,
        "formal_optimizer_updates_added": 0,
        "retries_added": 0,
        "archives_verified": len(archive_hashes),
        "archive_bytes": archive_bytes,
        "archive_sha256": archive_hashes,
        "auditor_sha256": audit_sha,
        "audit_error_count": audit["error_count"],
        "audit_errors": audit["errors"],
        "audited_seed_count": len(audit["seeds"]),
        "audit": audit,
        "restoration_runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "container": False,
            "purpose": "offline restore and independent raw-only audit; no candidate/training/timing workload",
        },
        "scope": "Exact retained synthetic #4580 evidence restoration only; no new scientific allocation or claim beyond PASS_ROLE_SKILL_ROBUSTNESS_SCOPED.",
    }
    REPORT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "archives_verified", "archive_bytes", "audited_seed_count",
        "audit_error_count", "auditor_sha256", "restoration_runtime")}, sort_keys=True))
    return 0 if result["status"] == "PASS_EVIDENCE_RESTORATION_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
