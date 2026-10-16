"""Post-hoc integrity check for the retained #7799 T0 result.

This check reads frozen source bytes and retained candidate/audit artifacts. It
does not invoke the candidate, original auditor, or a formal allocation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys


EXPECTED_FREEZE_SHA256 = "86dc57641783cc43763f316bee3b6a5824195e3c24dbf6db1c63441f829710d9"
EXPECTED_MANIFEST_SHA256 = "373b0e835872c24fadc54eea1064d209eaa5fdf48c5336890f78f2c383f4f414"
EXPECTED_SOURCE_COMMIT = "b5be19963454ce5edafc945b78b100012952dd15"
EXPECTED_CANDIDATE_SOURCE_SHA256 = "acda86fdfdfc14a1f64339e06dfd134b9c62825a461112839a90e793bddaee3e"
EXPECTED_AUDITOR_SOURCE_SHA256 = "2b5c45b0d0681c05843c627de3df052555c2a5f1029e70fb5fd153f28840f67b"
EXPECTED_CANDIDATE_RAW_SHA256 = "836fc1c302c8f1079c73c96c5f4cbf6400e3f8febeb30e54aedb6eb06de8db39"
EXPECTED_AUDIT_RAW_SHA256 = "1a98b5f74582923d62a3502ae8ef0bd9a50444557d6dff5b45adfd0eccb94b1a"
EXPECTED_DECISION = "HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR"

PACKAGE_FILES = {
    "candidate.py": EXPECTED_CANDIDATE_SOURCE_SHA256,
    "audit.py": EXPECTED_AUDITOR_SOURCE_SHA256,
    "results/formal-01/candidate.json": EXPECTED_CANDIDATE_RAW_SHA256,
    "results/formal-01/audit.json": EXPECTED_AUDIT_RAW_SHA256,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_manifest(data: bytes) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(data.decode("ascii").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        digest, separator, path = line.partition("  ")
        if not separator or len(digest) != 64 or path in entries:
            raise ValueError(f"invalid SHA256SUMS entry on line {line_number}")
        int(digest, 16)
        entries[path] = digest
    return entries


def evaluate(
    freeze: dict,
    freeze_sha256: str,
    source_sha256: dict[str, str],
    manifest_sha256: str,
    manifest: dict[str, str],
    package_sha256: dict[str, str],
    candidate: dict,
    candidate_raw_sha256: str,
    audit: dict,
    audit_raw_sha256: str,
) -> dict:
    frozen_sources = freeze.get("source_paths")
    checks = {
        "freeze_bytes_match_reviewed_package":
            freeze_sha256 == EXPECTED_FREEZE_SHA256,
        "freeze_commit_matches_reviewed_source":
            freeze.get("source_commit") == EXPECTED_SOURCE_COMMIT,
        "source_paths_are_complete":
            type(frozen_sources) is dict and len(frozen_sources) == 2,
        "checked_out_source_bytes_match_freeze":
            type(frozen_sources) is dict and source_sha256 == frozen_sources,
        "manifest_bytes_match_reviewed_package":
            manifest_sha256 == EXPECTED_MANIFEST_SHA256,
        "manifest_pins_candidate_and_auditor_code":
            all(manifest.get(path) == digest for path, digest in PACKAGE_FILES.items()),
        "candidate_code_matches_a01_manifest":
            package_sha256.get("candidate.py") == EXPECTED_CANDIDATE_SOURCE_SHA256,
        "original_auditor_code_matches_a01_manifest":
            package_sha256.get("audit.py") == EXPECTED_AUDITOR_SOURCE_SHA256,
        "candidate_raw_matches_a01_manifest":
            candidate_raw_sha256 == EXPECTED_CANDIDATE_RAW_SHA256,
        "original_audit_raw_matches_a01_manifest":
            audit_raw_sha256 == EXPECTED_AUDIT_RAW_SHA256,
        "candidate_commit_matches_freeze":
            candidate.get("source_commit") == freeze.get("source_commit"),
        "candidate_hashes_match_freeze":
            candidate.get("source_sha256") == frozen_sources,
        "candidate_decision_is_preserved_hold":
            candidate.get("eligibility") == EXPECTED_DECISION,
        "original_audit_binds_exact_candidate_raw":
            audit.get("raw_sha256") == candidate_raw_sha256,
        "original_audit_result_is_preserved":
            audit.get("decision") == "PASS_AUDIT"
            and audit.get("passed") == 11
            and audit.get("total") == 11
            and audit.get("rederived_design_matrix_rank") == 2,
    }
    return {
        "schema": "issue-7799-source-provenance-audit-v2",
        "scope": "post-hoc source, candidate-code, auditor-code, and retained-raw binding; no candidate, original auditor, or formal allocation invocation",
        "source_commit": freeze.get("source_commit"),
        "observed_sha256": {
            "freeze.json": freeze_sha256,
            "SHA256SUMS": manifest_sha256,
            "candidate.py": package_sha256.get("candidate.py"),
            "audit.py": package_sha256.get("audit.py"),
            "results/formal-01/candidate.json": candidate_raw_sha256,
            "results/formal-01/audit.json": audit_raw_sha256,
            **{f"source:{path}": digest for path, digest in source_sha256.items()},
        },
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "disposition": "PASS_SOURCE_BINDING_ONLY" if all(checks.values())
        else "FAIL_SOURCE_BINDING_ONLY",
    }


def mutation_checks(inputs: tuple) -> dict[str, bool]:
    (freeze, freeze_sha, sources, manifest_sha, manifest, package_sha,
     candidate, candidate_raw_sha, audit, audit_raw_sha) = inputs

    def fails(**changes) -> bool:
        values = {
            "freeze": freeze,
            "freeze_sha256": freeze_sha,
            "source_sha256": sources,
            "manifest_sha256": manifest_sha,
            "manifest": manifest,
            "package_sha256": package_sha,
            "candidate": candidate,
            "candidate_raw_sha256": candidate_raw_sha,
            "audit": audit,
            "audit_raw_sha256": audit_raw_sha,
        }
        values.update(changes)
        return evaluate(**values)["disposition"] == "FAIL_SOURCE_BINDING_ONLY"

    changed = copy.deepcopy(candidate)
    changed["source_sha256"][next(iter(changed["source_sha256"]))] = "0" * 64
    changed_package = dict(package_sha)
    changed_package["candidate.py"] = "0" * 64
    changed_auditor = dict(package_sha)
    changed_auditor["audit.py"] = "0" * 64
    changed_sources = dict(sources)
    changed_sources[next(iter(changed_sources))] = "0" * 64
    changed_manifest = dict(manifest)
    changed_manifest["candidate.py"] = "0" * 64
    changed_audit = copy.deepcopy(audit)
    changed_audit["raw_sha256"] = "0" * 64

    return {
        "candidate_source_hash_mutation_rejected": fails(candidate=changed),
        "candidate_code_byte_mutation_rejected": fails(package_sha256=changed_package),
        "original_auditor_code_byte_mutation_rejected": fails(package_sha256=changed_auditor),
        "source_file_mutation_rejected": fails(source_sha256=changed_sources),
        "manifest_entry_mutation_rejected": fails(manifest=changed_manifest),
        "audit_raw_binding_mutation_rejected": fails(audit=changed_audit),
        "original_audit_byte_mutation_rejected": fails(audit_raw_sha256="0" * 64),
    }


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: audit_provenance_v2.py PACKAGE_ROOT SOURCE_ROOT OUTPUT_JSON")
    package, source_root, output = map(pathlib.Path, sys.argv[1:])
    freeze_bytes = (package / "FREEZE.json").read_bytes()
    manifest_bytes = (package / "SHA256SUMS").read_bytes()
    freeze = json.loads(freeze_bytes)
    manifest = parse_manifest(manifest_bytes)
    candidate_bytes = (package / "results/formal-01/candidate.json").read_bytes()
    audit_bytes = (package / "results/formal-01/audit.json").read_bytes()
    candidate = json.loads(candidate_bytes)
    audit = json.loads(audit_bytes)
    frozen_sources = freeze.get("source_paths", {})
    actual_sources = {
        path: sha256((source_root / pathlib.PurePosixPath(path)).read_bytes())
        for path in frozen_sources
    }
    package_sha256 = {
        path: sha256((package / pathlib.PurePosixPath(path)).read_bytes())
        for path in PACKAGE_FILES
    }

    inputs = (
        freeze,
        sha256(freeze_bytes),
        actual_sources,
        sha256(manifest_bytes),
        manifest,
        package_sha256,
        candidate,
        sha256(candidate_bytes),
        audit,
        sha256(audit_bytes),
    )
    report = evaluate(*inputs)
    mutations = mutation_checks(inputs)
    report["mutation_checks"] = mutations
    report["mutation_checks_pass"] = all(mutations.values())
    passed = (report["disposition"] == "PASS_SOURCE_BINDING_ONLY"
              and report["mutation_checks_pass"])
    report["exit_disposition"] = (
        "PASS_SOURCE_BINDING_ONLY" if passed else "FAIL_SOURCE_BINDING_ONLY")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
