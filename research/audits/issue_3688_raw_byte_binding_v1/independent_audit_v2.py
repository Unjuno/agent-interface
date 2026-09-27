"""Fresh independent reconstruction of the immutable Issue #3688 result."""
import hashlib
import json
import sys
from pathlib import Path


EXPECTED = {
    "exact_original": ("PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT", "structural_audit"),
    "whitespace_appended": ("FAIL_PROVENANCE", "raw_and_predecessor_binding"),
    "altered_event": ("FAIL_PROVENANCE", "raw_and_predecessor_binding"),
    "changed_expected_raw_digest": ("FAIL_PROVENANCE", "study_freeze_binding"),
    "malformed_expected_raw_digest": ("FAIL_PROVENANCE", "study_freeze_binding"),
    "changed_source_manifest_digest": ("FAIL_PROVENANCE", "study_freeze_binding"),
    "modified_original_freeze": ("FAIL_PROVENANCE", "raw_and_predecessor_binding"),
    "modified_source_bytes": ("FAIL_PROVENANCE", "source_manifest_binding"),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(input_dir, results_dir):
    inp, out = Path(input_dir), Path(results_dir)
    allocation = json.loads((inp / "FREEZE.json").read_bytes())
    pred = allocation["predecessor"]
    raw0 = (inp / "predecessor_raw.json").read_bytes()
    freeze0 = (inp / "predecessor_FREEZE.json").read_bytes()
    study0 = (inp / "predecessor_study_FREEZE.json").read_bytes()
    if digest(raw0) != pred["raw_sha256"] or digest(freeze0) != pred["freeze_sha256"] or digest(study0) != pred["study_freeze_sha256"]:
        raise AssertionError("frozen predecessor input bytes changed")
    study = json.loads(study0)
    for name, expected in study["source_sha256"].items():
        if digest((inp / "upstream_sources" / name).read_bytes()) != expected:
            raise AssertionError(f"source-manifest mismatch: {name}")

    candidate_hashes = allocation["candidate_source_sha256"]
    for name, expected in candidate_hashes.items():
        if digest((Path("/work") / name).read_bytes()) != expected:
            raise AssertionError(f"candidate source mismatch: {name}")

    result = json.loads((out / "formal_result.json").read_bytes())
    rows = result.get("cases")
    if result.get("status") != "PASS_RAW_BYTE_BINDING" or not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise AssertionError("formal result disposition or row count mismatch")
    if {r.get("case") for r in rows} != set(EXPECTED):
        raise AssertionError("formal result case names mismatch")
    verified = []
    for row in rows:
        name = row["case"]
        status, stage = EXPECTED[name]
        case_dir = out / "cases" / name
        direct = json.loads((case_dir / "direct.json").read_bytes())
        cli = json.loads((case_dir / "cli.json").read_bytes())
        raw_bytes = (case_dir / "raw.json").read_bytes()
        freeze_bytes = (case_dir / "predecessor_FREEZE.json").read_bytes()
        study_bytes = (case_dir / "study_FREEZE.json").read_bytes()
        if direct != cli or direct.get("status") != status or direct.get("stage") != stage:
            raise AssertionError(f"direct/CLI disposition mismatch: {name}")
        if digest(raw_bytes) != row["input_raw_sha256"] or digest(freeze_bytes) != row["input_predecessor_freeze_sha256"] or digest(study_bytes) != row["input_study_freeze_sha256"]:
            raise AssertionError(f"retained mutation hash mismatch: {name}")
        if name != "exact_original" and status.startswith("PASS"):
            raise AssertionError(f"tampered case unexpectedly passed: {name}")
        verified.append({"case": name, "status": status, "stage": stage, "routes_equal": True,
                         "raw_sha256": digest(raw_bytes), "study_freeze_sha256": digest(study_bytes),
                         "predecessor_freeze_sha256": digest(freeze_bytes)})

    if (out / "cases/whitespace_appended/raw.json").read_bytes() != raw0 + b" \n":
        raise AssertionError("whitespace variant differs from preregistered mutation")
    changed_event = json.loads((out / "cases/altered_event/raw.json").read_bytes())
    if changed_event == json.loads(raw0):
        raise AssertionError("altered-event variant is unchanged")
    if json.loads((out / "cases/changed_expected_raw_digest/study_FREEZE.json").read_bytes())["predecessor_raw_sha256"] != "0" * 64:
        raise AssertionError("changed-digest variant is wrong")
    if json.loads((out / "cases/malformed_expected_raw_digest/study_FREEZE.json").read_bytes())["predecessor_raw_sha256"] != "sha256:not-a-hex-digest":
        raise AssertionError("malformed-digest variant is wrong")
    if json.loads((out / "cases/changed_source_manifest_digest/study_FREEZE.json").read_bytes())["source_sha256"]["audit.py"] != "0" * 64:
        raise AssertionError("source-manifest mutation is wrong")
    if (out / "cases/modified_original_freeze/predecessor_FREEZE.json").read_bytes() != freeze0 + b" \n":
        raise AssertionError("original-freeze byte mutation is wrong")
    if not (out / "cases/source_modified/sources/audit.py").read_bytes().endswith(b"\n# mutation copy only\n"):
        raise AssertionError("source-byte mutation is absent")

    return {"status": "PASS_INDEPENDENT_RAW_BYTE_AUDIT", "allocation_id": allocation["allocation_id"],
            "verified_cases": verified, "raw_sha256": digest(raw0), "predecessor_freeze_sha256": digest(freeze0),
            "predecessor_study_freeze_sha256": digest(study0), "formal_result_sha256": digest((out / "formal_result.json").read_bytes()),
            "errors": []}


if __name__ == "__main__":
    report = verify(sys.argv[1], sys.argv[2])
    print(json.dumps(report, sort_keys=True, indent=2))
