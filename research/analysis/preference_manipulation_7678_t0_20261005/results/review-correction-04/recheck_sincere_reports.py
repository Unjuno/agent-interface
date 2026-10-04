#!/usr/bin/env python3
"""Additive, non-confirmatory check of sincere-report metadata and retained blobs."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))
from audit import (order_preference, pref_key, rank_vector_orders, report_domain,
                   candidate_domain_matches, summarize_manipulation)


def index_blob(path: str) -> bytes:
    return subprocess.run(["git", "show", f":{path}"], cwd=REPO,
                          check=True, capture_output=True).stdout


def reconstructed_sincere_id(indices, reporter, orders, reports):
    full_ids = {pref_key(row["preference"]): row["report_id"]
                for row in reports if row["label"] == "full"}
    return full_ids.get(pref_key(order_preference(orders[indices[reporter]][0])))


def sincere_metadata_mismatches(document, orders, reports):
    mismatches = []
    for row in document.get("deviations", []):
        indices = row["order_indices"]
        reporter = row["reporter"]
        expected_id = reconstructed_sincere_id(indices, reporter, orders, reports)
        expected_is_sincere = row["report_id"] == expected_id
        if row.get("sincere_report_id") != expected_id or row.get("is_sincere") is not expected_is_sincere:
            mismatches.append({"order_indices": indices, "reporter": reporter,
                               "report_id": row.get("report_id"),
                               "candidate_sincere_report_id": row.get("sincere_report_id"),
                               "reconstructed_sincere_report_id": expected_id,
                               "candidate_is_sincere": row.get("is_sincere"),
                               "reconstructed_is_sincere": expected_is_sincere})
    return mismatches


def main() -> int:
    fixture_path = ROOT / "fixture.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "results/formal-01/candidate-output.json").read_text(encoding="utf-8"))
    orders = rank_vector_orders(sorted(fixture["routes"]))
    reports = report_domain(orders, fixture["report_masks"])
    expected_full_ids = {
        pref_key(row["preference"]): row["report_id"]
        for row in reports if row["label"] == "full"
    }
    errors: list[str] = []
    if not candidate_domain_matches(raw, fixture, orders, reports):
        errors.append("independent order/report/world domain mismatch")
    seen = set()
    mismatches = sincere_metadata_mismatches(raw, orders, reports)
    for row in raw.get("deviations", []):
        indices = row.get("order_indices")
        reporter = row.get("reporter")
        report_id = row.get("report_id")
        if (not isinstance(indices, list) or len(indices) != len(fixture["principals"])
                or any(type(i) is not int or i < 0 or i >= len(orders) for i in indices)
                or type(reporter) is not int or reporter < 0 or reporter >= len(indices)):
            errors.append("malformed deviation identity")
            continue
        key = (tuple(indices), reporter, report_id)
        if key in seen:
            errors.append("duplicate deviation identity")
        seen.add(key)
    expected_keys = {
        (indices, reporter, report["report_id"])
        for indices in __import__("itertools").product(range(len(orders)), repeat=len(fixture["principals"]))
        for reporter in range(len(fixture["principals"])) for report in reports
    }
    if seen != expected_keys:
        errors.append("deviation domain incomplete or has unexpected rows")
    if mismatches:
        errors.append("candidate sincere-report metadata differs from independent reconstruction")

    corrected_summary = None
    if not errors:
        summary = summarize_manipulation(raw, fixture, orders, reports)
        corrected_summary = {
            "frontier_changed_deviations": summary["frontier_changed_deviations"],
            "true_top_removed_deviations": summary["true_top_removed_deviations"],
            "safe_beneficial_full_information": len(summary["safe_beneficial_full_information"]),
            "safe_beneficial_partial_information": len(summary["safe_beneficial_partial_information"]),
            "conclusion": ("MANIPULATION_WITNESS" if summary["safe_beneficial_full_information"]
                           or summary["safe_beneficial_partial_information"]
                           else "EXHAUSTIVE_NULL_FOR_DECLARED_SET_UTILITY"),
        }

    manifest_path = ROOT / "results/review-correction-03/REVIEW_SHA256SUMS.txt"
    manifest_checks = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        payload = (ROOT / rel).read_bytes()
        work_hash = hashlib.sha256(payload).hexdigest()
        try:
            staged = index_blob((ROOT / rel).relative_to(REPO).as_posix())
            staged_hash = hashlib.sha256(staged).hexdigest()
        except (subprocess.CalledProcessError, ValueError) as exc:
            staged_hash = None
            errors.append(f"index blob unavailable: {rel}: {exc}")
        manifest_checks.append({"path": rel, "manifest_sha256": expected,
                                "worktree_sha256": work_hash, "index_sha256": staged_hash,
                                "matches_manifest": expected == work_hash == staged_hash})
        if expected != work_hash or expected != staged_hash:
            errors.append(f"review-correction-03 manifest does not seal worktree and index bytes: {rel}")

    result = {
        "schema": "preference-manipulation-7678-t0-sincere-report-recheck-v1",
        "allocation": fixture["allocation"],
        "candidate_or_formal_auditor_rerun": False,
        "formal_allocation_disposition": "HOLD",
        "historical_review_correction_03_claim_status": "NOT_RECONFIRMED_UNTIL_THIS_RECHECK_PASSES",
        "reconstructed_full_report_ids": len(expected_full_ids),
        "deviation_rows": len(raw.get("deviations", [])),
        "sincere_metadata_mismatch_count": len(mismatches),
        "sincere_metadata_mismatch_examples": mismatches[:10],
        "independently_recomputed_manipulation_summary_after_metadata_validation": corrected_summary,
        "review_correction_03_manifest_file_count": len(manifest_checks),
        "review_correction_03_manifest_mismatch_count": sum(not r["matches_manifest"] for r in manifest_checks),
        "errors": errors,
        "disposition": "PASS_ADDITIVE_SINCERE_METADATA_AND_BLOB_RECHECK" if not errors else "HOLD_RECHECK_ERRORS",
        "manifest_checks": manifest_checks,
    }
    out = ROOT / "results/review-correction-04/RECHECK.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
