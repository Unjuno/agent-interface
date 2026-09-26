"""Independent verifier for the retained Issue #3688 matrix outputs."""
import hashlib
import json
import sys
from pathlib import Path


EXPECTED_CASES = {
    "exact_original": ("PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT", "structural_audit"),
    "whitespace_appended": ("FAIL_PROVENANCE", "raw_and_predecessor_binding"),
    "altered_event": ("FAIL_PROVENANCE", "raw_and_predecessor_binding"),
    "changed_expected_raw_digest": ("FAIL_PROVENANCE", "study_freeze_binding"),
    "malformed_expected_raw_digest": ("FAIL_PROVENANCE", "study_freeze_binding"),
    "changed_source_manifest_digest": ("FAIL_PROVENANCE", "study_freeze_binding"),
    "modified_original_freeze": ("FAIL_PROVENANCE", "raw_and_predecessor_binding"),
    "modified_source_bytes": ("FAIL_PROVENANCE", "source_manifest_binding"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(input_dir, output_dir):
    inp, out = Path(input_dir), Path(output_dir)
    experiment_freeze = json.loads((inp / "FREEZE.json").read_bytes())
    predecessor = experiment_freeze["predecessor"]
    original_raw = (inp / "predecessor_raw.json").read_bytes()
    original_freeze = (inp / "predecessor_FREEZE.json").read_bytes()
    original_study = (inp / "predecessor_study_FREEZE.json").read_bytes()
    expected_inputs = {
        "raw_sha256": hashlib.sha256(original_raw).hexdigest(),
        "freeze_sha256": hashlib.sha256(original_freeze).hexdigest(),
        "study_freeze_sha256": hashlib.sha256(original_study).hexdigest(),
    }
    if expected_inputs != {
        "raw_sha256": predecessor["raw_sha256"],
        "freeze_sha256": predecessor["freeze_sha256"],
        "study_freeze_sha256": predecessor["study_freeze_sha256"],
    }:
        raise AssertionError("original input hashes do not match frozen values")
    study = json.loads(original_study)
    for name, expected in study["source_sha256"].items():
        if sha(inp / "upstream_sources" / name) != expected:
            raise AssertionError(f"upstream source hash mismatch: {name}")
    candidate_sources = experiment_freeze["candidate_source_sha256"]
    for name, expected in candidate_sources.items():
        if sha(Path("/work") / name) != expected:
            raise AssertionError(f"candidate source hash mismatch: {name}")

    result_path = out / "formal_result.json"
    result = json.loads(result_path.read_bytes())
    if result.get("status") != "PASS_RAW_BYTE_BINDING":
        raise AssertionError("formal matrix did not pass")
    if result.get("raw_input_sha256") != expected_inputs["raw_sha256"]:
        raise AssertionError("formal result raw hash mismatch")
    if len(result.get("cases", [])) != len(EXPECTED_CASES) or set(row["case"] for row in result.get("cases", [])) != EXPECTED_CASES:
        raise AssertionError("formal result case set mismatch")
    if result.get("candidate_source_sha256") != candidate_sources:
        raise AssertionError("formal candidate source hashes differ from the freeze")

    checks = []
    for row in result["cases"]:
        name = row["case"]
        case_dir = out / "cases" / name
        expected_status, expected_stage = EXPECTED_CASES[name]
        direct = json.loads((case_dir / "direct.json").read_bytes())
        cli = json.loads((case_dir / "cli.json").read_bytes())
        if direct != cli or row.get("direct_cli_equal") is not True:
            raise AssertionError(f"direct/CLI mismatch: {name}")
        if direct.get("status") != expected_status:
            raise AssertionError(f"unexpected disposition: {name}")
        if expected_stage is not None and direct.get("stage") != expected_stage:
            raise AssertionError(f"unexpected rejection stage: {name}: {direct.get('stage')}")
        if name != "exact_original" and direct.get("status") == "PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT":
            raise AssertionError(f"tampered input got PASS: {name}")
        raw_bytes = (case_dir / "raw.json").read_bytes()
        if hashlib.sha256(raw_bytes).hexdigest() != row.get("input_raw_sha256"):
            raise AssertionError(f"raw copy hash mismatch: {name}")
        if hashlib.sha256((case_dir / "predecessor_FREEZE.json").read_bytes()).hexdigest() != row.get("input_predecessor_freeze_sha256"):
            raise AssertionError(f"predecessor freeze copy hash mismatch: {name}")
        study_bytes = (case_dir / "study_FREEZE.json").read_bytes()
        if hashlib.sha256(study_bytes).hexdigest() != row.get("input_study_freeze_sha256"):
            raise AssertionError(f"study freeze copy hash mismatch: {name}")
        checks.append({"case": name, "status": "VERIFIED", "observed": direct["status"],
                       "stage": direct.get("stage"), "direct_cli_equal": True})

    if (out / "cases/whitespace_appended/raw.json").read_bytes() != original_raw + b" \n":
        raise AssertionError("whitespace control is not the exact parsed-equivalent byte mutation")
    altered_event = json.loads((out / "cases/altered_event/raw.json").read_bytes())
    if altered_event == json.loads(original_raw):
        raise AssertionError("altered-event control did not change parsed content")
    changed_digest = json.loads((out / "cases/changed_expected_raw_digest/study_FREEZE.json").read_bytes())
    malformed_digest = json.loads((out / "cases/malformed_expected_raw_digest/study_FREEZE.json").read_bytes())
    if changed_digest.get("predecessor_raw_sha256") != "0" * 64:
        raise AssertionError("changed expected digest control was not applied")
    if malformed_digest.get("predecessor_raw_sha256") != "sha256:not-a-hex-digest":
        raise AssertionError("malformed expected digest control was not applied")
    changed_manifest = json.loads((out / "cases/changed_source_manifest_digest/study_FREEZE.json").read_bytes())
    if changed_manifest["source_sha256"].get("audit.py") != "0" * 64:
        raise AssertionError("changed source manifest control was not applied")
    if ((out / "cases/modified_original_freeze/predecessor_FREEZE.json").read_bytes()
            != original_freeze + b" \n"):
        raise AssertionError("original-freeze mutation control was not applied")
    mutated_audit = (out / "cases/modified_source_bytes/sources/audit.py").read_bytes()
    if not mutated_audit.endswith(b"\n# mutation copy only\n"):
        raise AssertionError("source-byte mutation was not applied")

    return {"status": "PASS_INDEPENDENT_RAW_BYTE_AUDIT", "verified_cases": checks,
            "raw_sha256": expected_inputs["raw_sha256"], "freeze_sha256": expected_inputs["freeze_sha256"],
            "study_freeze_sha256": expected_inputs["study_freeze_sha256"],
            "allocation_result_sha256": sha(result_path), "errors": []}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: independent_audit.py INPUT_DIR OUTPUT_DIR")
    report = verify(sys.argv[1], sys.argv[2])
    rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
    (Path(sys.argv[2]) / "independent_audit.json").write_text(rendered)
    print(rendered, end="")
