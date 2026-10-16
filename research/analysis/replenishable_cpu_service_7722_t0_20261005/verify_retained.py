#!/usr/bin/env python3
"""Read-only integrity check; never launches the candidate or formal auditor."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIRED_MANIFEST_FILES = {
    "candidate.py",
    "auditor.py",
    "cases.json",
    "freeze.json",
    "PROTOCOL.md",
    "output/candidate/candidate.raw.json",
    "output/auditor/audit.json",
    "output/candidate/run-meta.json",
    "output/auditor/run-meta.json",
    "output/review/review_audit.json",
    "review_audit.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT) -> None:
    sums_path = root / "SHA256SUMS"
    checksums = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64 or parts[1] in checksums:
            raise ValueError("invalid or duplicate SHA256SUMS entry")
        try:
            int(parts[0], 16)
        except ValueError as error:
            raise ValueError("invalid SHA-256 digest") from error
        relative = Path(parts[1])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe SHA256SUMS path")
        checksums[parts[1]] = parts[0]

    missing = REQUIRED_MANIFEST_FILES - checksums.keys()
    if missing:
        raise ValueError("required manifest entries missing: " + ", ".join(sorted(missing)))

    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS" and "__pycache__" not in path.parts
    }
    if actual_files != checksums.keys():
        raise ValueError(
            "manifest file set mismatch: "
            f"unlisted={sorted(actual_files - checksums.keys())}; "
            f"missing={sorted(checksums.keys() - actual_files)}"
        )

    for name, expected in checksums.items():
        path = root / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"checksum mismatch: {name}")

    freeze = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    source_files = (
        ("candidate_sha256", "candidate.py"),
        ("auditor_sha256", "auditor.py"),
        ("cases_sha256", "cases.json"),
        ("protocol_sha256", "PROTOCOL.md"),
        ("freeze_builder_sha256", "freeze_builder.py"),
    )
    for key, name in source_files:
        if sha(root / name) != freeze["source_hashes"][key]:
            raise ValueError(f"frozen source mismatch: {name}")

    raw = json.loads((root / "output/candidate/candidate.raw.json").read_text(encoding="utf-8"))
    audit = json.loads((root / "output/auditor/audit.json").read_text(encoding="utf-8"))
    review = json.loads((root / "output/review/review_audit.json").read_text(encoding="utf-8"))
    if len(raw.get("runs", [])) != 18:
        raise ValueError("retained raw run count mismatch")
    if audit.get("method") != "METHOD_PASS_SCOPED" or audit.get("hypothesis") != "FAIL_HYPOTHESIS":
        raise ValueError("retained audit disposition mismatch")
    if audit.get("errors") != [] or len(audit.get("mutation_rejections", {})) != 6:
        raise ValueError("retained audit error or mutation record mismatch")
    if not all(audit["mutation_rejections"].values()):
        raise ValueError("retained audit reports an un-rejected mutation")
    if review.get("status") != "PASS_SUPPLEMENTAL_RAW_RECONSTRUCTION":
        raise ValueError("supplemental raw reconstruction did not pass")
    if review.get("classification") != "SUPPLEMENTAL_READ_ONLY_AUDIT; does not replace or upgrade the frozen formal allocation":
        raise ValueError("supplemental audit claim boundary missing")
    if review.get("raw_reconstruction_errors") != [] or review.get("raw_run_count") != 18:
        raise ValueError("supplemental raw reconstruction evidence mismatch")
    mutation_controls = review.get("mutation_controls", {})
    if len(mutation_controls) != 8 or not all(item.get("rejected") for item in mutation_controls.values()):
        raise ValueError("supplemental mutation controls incomplete")
    if review.get("unchanged_trace_control", {}).get("accepted") is not True:
        raise ValueError("supplemental valid-trace control failed")
    if review.get("candidate_invocations") != 0 or review.get("frozen_auditor_invocations") != 0 or review.get("retries") != 0:
        raise ValueError("supplemental audit exceeded read-only invocation scope")
    hashes = review.get("sha256", {})
    for key, path in (
        ("raw", root / "output/candidate/candidate.raw.json"),
        ("cases", root / "cases.json"),
        ("frozen_candidate", root / "candidate.py"),
        ("frozen_auditor", root / "auditor.py"),
        ("supplemental_auditor", root / "review_audit.py"),
    ):
        if hashes.get(key) != sha(path):
            raise ValueError(f"supplemental evidence hash mismatch: {key}")

    for case, shared, reserved, misses in (
        ("sched_seed_7722", 584, 166, 3),
        ("sched_seed_7723", 586, 168, 2),
        ("sched_seed_7724", 561, 131, 1),
    ):
        metrics = audit["metrics"]
        if metrics[f"{case}/shared_priority"]["p99_response_ticks"] != shared:
            raise ValueError(f"shared p99 mismatch: {case}")
        if metrics[f"{case}/reserved_server"]["p99_response_ticks"] != reserved:
            raise ValueError(f"reserved p99 mismatch: {case}")
        if metrics[f"{case}/shared_priority"]["control_deadline_misses"] != 10:
            raise ValueError(f"shared misses mismatch: {case}")
        if metrics[f"{case}/reserved_server"]["control_deadline_misses"] != misses:
            raise ValueError(f"reserved misses mismatch: {case}")
        if metrics[f"{case}/shared_priority"]["best_effort_completed"] != 192:
            raise ValueError(f"shared best-effort count mismatch: {case}")
        if metrics[f"{case}/reserved_server"]["best_effort_completed"] != 190:
            raise ValueError(f"reserved best-effort count mismatch: {case}")

    warning = b"Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap."
    for lane in ("candidate", "auditor"):
        output = root / "output" / lane
        meta = json.loads((output / "run-meta.json").read_text(encoding="utf-8"))
        if meta.get("exit_code") != 0 or meta.get("retry_count") != 0:
            raise ValueError(f"run metadata mismatch: {lane}")
        if warning not in (output / "wslc.stderr.log").read_bytes():
            raise ValueError(f"expected WSLc warning not retained: {lane}")


def main() -> int:
    try:
        verify()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"FAIL_RETAINED_EVIDENCE_INTEGRITY: {error}", file=sys.stderr)
        return 1
    print("PASS_RETAINED_PACKAGE_INTEGRITY_WITH_SUPPLEMENTAL_AUDIT; candidate/auditor were not rerun")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
