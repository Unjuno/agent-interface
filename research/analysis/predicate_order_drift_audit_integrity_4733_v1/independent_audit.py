from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path


EXPECTED_SOURCE = "28b207348b6279395670b282edcdc719ac1a653ff0e2dc09c987cf95526cf4d5"
EXPECTED_TRANSPORT = "474b6381e8381ed8cae12141303e4638539d12cf6cf8b1c999c630efae80efe7"
EXPECTED_RAW = "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"
EXPECTED_GIT_SOURCE = "1a6cc0e46b32d4cd6989aed118d003cce4cfe399"
EXPECTED_GIT_TRANSPORT = "c38dd2002f201d49b6fc261caff019550a4bf4bc"
SOURCE = Path("research/analysis/predicate_order_drift_4258_v1/src/audit.py")
TRANSPORT = Path("research/analysis/predicate_order_drift_4258_v1/RAW_AND_AUDIT.zip.base64")
MODES = {"normal", "python_-O", "PYTHONOPTIMIZE=1"}
MUTATIONS = {"first_row_weight_json_nan", "development_alpha_0_5", "truth_state_count_99"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(repo_root: Path, result_path: Path) -> dict:
    errors = []
    source = (repo_root / "audit.py").read_bytes() if repo_root.name == "source" else (repo_root / SOURCE).read_bytes()
    transport = (repo_root / "RAW_AND_AUDIT.zip.base64").read_bytes() if repo_root.name == "input" else (repo_root / TRANSPORT).read_bytes()
    if digest(source) != EXPECTED_SOURCE:
        errors.append("source_sha256")
    if digest(transport) != EXPECTED_TRANSPORT:
        errors.append("transport_sha256")
    try:
        archive_bytes = base64.b64decode(b"".join(transport.split()), validate=True)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            if archive.namelist() != ["RAW.json", "AUDIT.json"]:
                errors.append("archive_members")
            raw = archive.read("RAW.json")
    except Exception as exc:
        errors.append(f"archive_read:{type(exc).__name__}")
        raw = b""
    if len(raw) != 186739 or digest(raw) != EXPECTED_RAW:
        errors.append("raw_identity")
    try:
        document = json.loads(raw)
        if len(document["distributions"]) != 21:
            errors.append("distribution_count")
        if sum(len(item["rows"]) for item in document["distributions"]) != 336:
            errors.append("row_count")
        if document.get("truth_state_count") != 16:
            errors.append("truth_state_count_original")
    except Exception as exc:
        errors.append(f"raw_schema:{type(exc).__name__}")
    try:
        result_bytes = result_path.read_bytes()
        result = json.loads(result_bytes)
    except Exception as exc:
        errors.append(f"result_read:{type(exc).__name__}")
        result = {}
        result_bytes = b""
    if result.get("schema") != "predicate-order-audit-integrity-4733-probe-v1":
        errors.append("result_schema")
    identities = result.get("identities", {})
    if identities.get("source_sha256") != EXPECTED_SOURCE or identities.get("source_git_blob_expected") != EXPECTED_GIT_SOURCE:
        errors.append("result_source_binding")
    if identities.get("transport_sha256") != EXPECTED_TRANSPORT or identities.get("transport_git_blob_expected") != EXPECTED_GIT_TRANSPORT:
        errors.append("result_transport_binding")
    if identities.get("raw_sha256") != EXPECTED_RAW or identities.get("raw_bytes") != 186739:
        errors.append("result_raw_binding")
    baseline = result.get("baseline", {})
    if set(baseline) != MODES:
        errors.append("baseline_mode_set")
    for mode, value in baseline.items():
        if value.get("status") != "PASS_DRIFT_BOUNDARY_MAPPED" or value.get("errors") != []:
            errors.append(f"baseline:{mode}")
        if (value.get("corruption_controls_rejected"), value.get("corruption_control_count")) != (5, 5):
            errors.append(f"baseline_controls:{mode}")
        if (value.get("distribution_count"), value.get("row_count")) != (21, 336):
            errors.append(f"baseline_rows:{mode}")
    mutations = result.get("mutations", {})
    if set(mutations) != MUTATIONS:
        errors.append("mutation_set")
    passed = []
    for name, by_mode in mutations.items():
        if set(by_mode) != MODES:
            errors.append(f"mutation_modes:{name}")
        for mode, value in by_mode.items():
            if value.get("status") == "PASS_DRIFT_BOUNDARY_MAPPED" and value.get("errors") == []:
                passed.append((name, mode))
    expected = "PASS_AUDIT_GAP_REPRODUCED" if passed else "FAIL_GAP_NOT_REPRODUCED"
    if result.get("disposition") != expected:
        errors.append("disposition")
    if result.get("original_raw_sha256_before_after_equal") is not True:
        errors.append("raw_immutability_receipt")
    if result.get("source_sha256_before_after_equal") is not True:
        errors.append("source_immutability_receipt")
    return {"schema": "predicate-order-audit-integrity-independent-v1",
            "disposition": "INDEPENDENT_AUDIT_PASS" if not errors else "INDEPENDENT_AUDIT_FAIL",
            "errors": errors, "mutation_pass_witnesses": passed,
            "result_bytes": len(result_bytes), "result_sha256": digest(result_bytes),
            "raw_sha256_recomputed": digest(raw), "raw_bytes_recomputed": len(raw)}


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: independent_audit.py SOURCE_DIR INPUT_DIR RESULT_JSON AUDIT_JSON", file=sys.stderr)
        return 64
    report = audit(Path(sys.argv[1]), Path(sys.argv[3]))
    # Independently bind the separately mounted transport path as well.
    if digest((Path(sys.argv[2]) / "RAW_AND_AUDIT.zip.base64").read_bytes()) != EXPECTED_TRANSPORT:
        report["errors"].append("transport_mount_binding")
        report["disposition"] = "INDEPENDENT_AUDIT_FAIL"
    output = Path(sys.argv[4])
    if output.exists():
        print("STOP_AUDIT_OUTPUT_ALREADY_EXISTS", file=sys.stderr)
        return 2
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["disposition"] == "INDEPENDENT_AUDIT_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
