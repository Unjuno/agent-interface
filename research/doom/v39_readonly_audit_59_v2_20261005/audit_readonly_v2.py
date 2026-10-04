"""Read-only independent audit of the archived V39 A01 projection result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
DEFAULT_ARCHIVE = PACKAGE.parent / "v39_application_consumption_conflict_59_a01_20261005"
EXPECTED_LAYERS = ("event", "measurement", "adapter_edge", "bracket")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_inventory(archive: Path):
    entries = {}
    for line in (archive / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64:
            raise ValueError(f"invalid SHA256SUMS row: {line!r}")
        path = (archive / relative).resolve()
        if archive.resolve() not in path.parents:
            raise ValueError(f"manifest path escapes archive: {relative}")
        if relative in entries:
            raise ValueError(f"duplicate manifest path: {relative}")
        entries[relative] = digest
    actual_files = {
        path.relative_to(archive).as_posix()
        for path in archive.rglob("*") if path.is_file() and
        "__pycache__" not in path.parts
    } - {"SHA256SUMS"}
    if actual_files != set(entries):
        raise ValueError("archive file inventory differs from SHA256SUMS")
    mismatches = [relative for relative, expected in entries.items()
                  if sha256(archive / relative) != expected]
    return entries, mismatches


def audit_archive(archive: Path) -> dict:
    errors = []
    try:
        entries, mismatches = archive_inventory(archive)
    except (OSError, ValueError) as error:
        return {"status": "FAIL_READ_ONLY_ARCHIVE_AUDIT",
                "errors": [f"archive manifest: {error}"],
                "archive_path": str(archive),
                "scope": "saved-output audit only; no files are written"}
    if mismatches:
        errors.append(f"archive SHA256SUMS mismatches: {mismatches}")

    try:
        freeze = json.loads((archive / "FREEZE.json").read_text(encoding="utf-8"))
        raw = json.loads((archive / "raw/A01.json").read_text(encoding="utf-8"))
        saved_audit = json.loads((archive / "raw/AUDIT.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"status": "FAIL_READ_ONLY_ARCHIVE_AUDIT",
                "errors": [*errors, f"invalid archived JSON: {error}"],
                "archive_path": str(archive),
                "manifest_members": len(entries),
                "scope": "saved-output audit only; no files are written"}

    for name, raw_name, relative in (
        ("baseline_source", "baseline", "BASELINE_SOURCE.py.txt"),
        ("candidate_source", "candidate", "CANDIDATE_SOURCE.py.txt"),
        ("input", "input", "INPUT.jsonl"),
    ):
        observed = sha256(archive / relative)
        if freeze.get("sha256", {}).get(name) != observed:
            errors.append(f"freeze SHA mismatch: {name}")
        if raw.get("sources", {}).get(f"{raw_name}_sha256") != observed:
            errors.append(f"raw source SHA mismatch: {name}")

    mutations = raw.get("application_flag_mutations", [])
    expected = [(row, layer) for row in range(2) for layer in EXPECTED_LAYERS]
    observed = [(row.get("row_index"), row.get("layer")) for row in mutations]
    if observed != expected:
        errors.append("application-flag mutation identities/order mismatch")
    candidate_false_accepts = 0
    baseline_false_accepts = 0
    for row in mutations:
        candidate = row.get("candidate", {})
        baseline = row.get("baseline", {})
        if candidate.get("status") == "adapter_edge_brackets_paired":
            candidate_false_accepts += 1
        if baseline.get("status") == "adapter_edge_brackets_paired":
            baseline_false_accepts += 1
        if candidate.get("status") != "adapter_edge_receipt_incomplete":
            errors.append("candidate did not reject a contradictory flag")
        if (candidate.get("down_edge_interval_ns") is not None or
                candidate.get("up_edge_interval_ns") is not None):
            errors.append("candidate exposed intervals for contradictory evidence")

    if baseline_false_accepts != raw.get("baseline_false_accept_count"):
        errors.append("baseline false-accept summary mismatch")
    if candidate_false_accepts != raw.get("candidate_false_accept_count"):
        errors.append("candidate false-accept summary mismatch")
    if candidate_false_accepts != 0 or baseline_false_accepts < 1:
        errors.append("baseline/candidate mutation gate mismatch")

    sweep_result = {}
    for name in ("baseline", "candidate"):
        cases = raw.get("interval_sweep", {}).get(name, {}).get("cases", [])
        paired = incomplete = 0
        if len(cases) != 100:
            errors.append(f"{name} interval sweep case count is not 100")
        for case in cases:
            ordered = case.get("expected_ordered") is True
            expected_status = ("adapter_edge_brackets_paired" if ordered else
                               "adapter_edge_receipt_incomplete")
            if case.get("status") != expected_status:
                errors.append(f"{name} interval classification mismatch")
            if ordered:
                paired += 1
                if (case.get("down_edge_interval_ns") != case.get("down") or
                        case.get("up_edge_interval_ns") != case.get("up")):
                    errors.append(f"{name} ordered interval output mismatch")
            else:
                incomplete += 1
                if (case.get("down_edge_interval_ns") is not None or
                        case.get("up_edge_interval_ns") is not None):
                    errors.append(f"{name} exposed intervals for unordered pair")
        if (paired, incomplete) != (15, 85):
            errors.append(f"{name} interval summary is not 15/85")
        sweep_result[name] = {"cases": len(cases), "ordered": paired,
                              "incomplete": incomplete}

    if raw.get("valid_control", {}).get("status") != "adapter_edge_brackets_paired":
        errors.append("valid control did not pair")
    saved_consistent = (
        saved_audit.get("status") == "PASS_SAVED_RESULT_AUDIT" and
        saved_audit.get("errors") == [] and
        saved_audit.get("baseline_false_accept_count") == baseline_false_accepts and
        saved_audit.get("candidate_false_accept_count") == candidate_false_accepts and
        saved_audit.get("interval_sweep", {}).get("baseline") ==
        {"cases": 100, "paired": 15, "incomplete": 85} and
        saved_audit.get("interval_sweep", {}).get("candidate") ==
        {"cases": 100, "paired": 15, "incomplete": 85})
    if not saved_consistent:
        errors.append("preserved first-audit output disagrees with raw recomputation")

    return {
        "status": "PASS_READ_ONLY_ARCHIVE_AUDIT" if not errors else
                  "FAIL_READ_ONLY_ARCHIVE_AUDIT",
        "errors": errors,
        "archive_path": str(archive),
        "manifest_members": len(entries),
        "baseline_false_accept_count": baseline_false_accepts,
        "candidate_false_accept_count": candidate_false_accepts,
        "interval_sweep": sweep_result,
        "preserved_first_audit_consistent": saved_consistent,
        "scope": "saved-result and archive-integrity audit only; no files are written; does not validate X-server behavior, application consumption, live input, or task effect",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args()
    result = audit_archive(args.archive.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS_READ_ONLY_ARCHIVE_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
