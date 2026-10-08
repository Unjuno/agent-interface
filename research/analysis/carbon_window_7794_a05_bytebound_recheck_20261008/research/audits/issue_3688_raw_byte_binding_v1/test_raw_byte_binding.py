"""One-shot adversarial test matrix; writes only under the supplied output dir."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from raw_byte_audit import audit_bytes


PASS_STATUS = "PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT"


def invoke_cli(raw_path, pred_freeze, study_freeze, source_dir, expected_study_sha, out_path):
    command = [
        sys.executable, "/work/raw_byte_audit.py",
        "--raw", str(raw_path),
        "--predecessor-freeze", str(pred_freeze),
        "--study-freeze", str(study_freeze),
        "--source-dir", str(source_dir),
        "--expected-study-freeze-sha256", expected_study_sha,
        "--output", str(out_path),
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"CLI did not emit JSON: rc={proc.returncode}, stderr={proc.stderr!r}") from exc
    if not out_path.is_file() or json.loads(out_path.read_text()) != result:
        raise AssertionError("CLI stdout and retained output file disagree")
    return proc.returncode, result, command


def main(input_dir, output_dir):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in output_dir.iterdir():
        raise AssertionError(f"output directory must be unique and initially empty: {existing}")

    raw0 = (input_dir / "predecessor_raw.json").read_bytes()
    pred_freeze0 = (input_dir / "predecessor_FREEZE.json").read_bytes()
    study_freeze0 = (input_dir / "predecessor_study_FREEZE.json").read_bytes()
    experiment_freeze = json.loads((input_dir / "FREEZE.json").read_bytes())
    expected_inputs = experiment_freeze["predecessor"]
    actual_inputs = {
        "raw_sha256": hashlib.sha256(raw0).hexdigest(),
        "freeze_sha256": hashlib.sha256(pred_freeze0).hexdigest(),
        "study_freeze_sha256": hashlib.sha256(study_freeze0).hexdigest(),
    }
    if actual_inputs != {
        "raw_sha256": expected_inputs["raw_sha256"],
        "freeze_sha256": expected_inputs["freeze_sha256"],
        "study_freeze_sha256": expected_inputs["study_freeze_sha256"],
    }:
        raise AssertionError(f"predecessor input hash mismatch: {actual_inputs}")
    candidate_sources = experiment_freeze["candidate_source_sha256"]
    for name, expected in candidate_sources.items():
        candidate_path = Path("/work") / name
        actual = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f"candidate source hash mismatch: {name}")
    expected_study_sha = experiment_freeze["predecessor"]["study_freeze_sha256"]
    source0 = input_dir / "upstream_sources"
    source0.mkdir(exist_ok=True)
    for name in ("audit.py", "test_audit.py"):
        src = input_dir / f"predecessor_{name}"
        dst = source0 / name
        if not dst.exists():
            shutil.copyfile(src, dst)

    study_obj = json.loads(study_freeze0)
    raw_obj = json.loads(raw0)
    whitespace = raw0 + b" \n"
    altered_obj = copy.deepcopy(raw_obj)
    altered_obj["events"][0]["identity"]["pid"] += 100
    altered_event = (json.dumps(altered_obj, sort_keys=True, separators=(",", ":")) + "\n").encode()

    changed_digest_obj = copy.deepcopy(study_obj)
    changed_digest_obj["predecessor_raw_sha256"] = "0" * 64
    changed_digest = (json.dumps(changed_digest_obj, sort_keys=True, indent=2) + "\n").encode()
    malformed_digest_obj = copy.deepcopy(study_obj)
    malformed_digest_obj["predecessor_raw_sha256"] = "sha256:not-a-hex-digest"
    malformed_digest = (json.dumps(malformed_digest_obj, sort_keys=True, indent=2) + "\n").encode()
    changed_source_manifest_obj = copy.deepcopy(study_obj)
    changed_source_manifest_obj["source_sha256"]["audit.py"] = "0" * 64
    changed_source_manifest = (json.dumps(changed_source_manifest_obj, sort_keys=True, indent=2) + "\n").encode()
    changed_original_freeze = pred_freeze0 + b" \n"

    altered_source = output_dir / "cases" / "source_modified" / "sources"
    altered_source.mkdir(parents=True)
    shutil.copyfile(source0 / "audit.py", altered_source / "audit.py")
    shutil.copyfile(source0 / "test_audit.py", altered_source / "test_audit.py")
    with (altered_source / "audit.py").open("ab") as handle:
        handle.write(b"\n# mutation copy only\n")

    cases = [
        ("exact_original", raw0, pred_freeze0, study_freeze0, source0, PASS_STATUS),
        ("whitespace_appended", whitespace, pred_freeze0, study_freeze0, source0, "FAIL_PROVENANCE"),
        ("altered_event", altered_event, pred_freeze0, study_freeze0, source0, "FAIL_PROVENANCE"),
        ("changed_expected_raw_digest", raw0, pred_freeze0, changed_digest, source0, "FAIL_PROVENANCE"),
        ("malformed_expected_raw_digest", raw0, pred_freeze0, malformed_digest, source0, "FAIL_PROVENANCE"),
        ("changed_source_manifest_digest", raw0, pred_freeze0, changed_source_manifest, source0, "FAIL_PROVENANCE"),
        ("modified_original_freeze", raw0, changed_original_freeze, study_freeze0, source0, "FAIL_PROVENANCE"),
        ("modified_source_bytes", raw0, pred_freeze0, study_freeze0, altered_source, "FAIL_PROVENANCE"),
    ]
    rows = []
    for name, raw_bytes, predecessor_freeze_bytes, study_bytes, source_dir, expected_status in cases:
        case_dir = output_dir / "cases" / name
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_path = case_dir / "raw.json"
        study_path = case_dir / "study_FREEZE.json"
        raw_path.write_bytes(raw_bytes)
        study_path.write_bytes(study_bytes)
        (case_dir / "predecessor_FREEZE.json").write_bytes(predecessor_freeze_bytes)
        direct = audit_bytes(raw_path, case_dir / "predecessor_FREEZE.json", study_path,
                             source_dir, expected_study_sha)
        direct_path = case_dir / "direct.json"
        direct_path.write_text(json.dumps(direct, sort_keys=True, indent=2) + "\n")
        cli_rc, cli_result, command = invoke_cli(
            raw_path, case_dir / "predecessor_FREEZE.json", study_path,
            source_dir, expected_study_sha, case_dir / "cli.json")
        if direct != cli_result:
            raise AssertionError(f"direct/CLI mismatch for {name}")
        if direct["status"] != expected_status:
            raise AssertionError(f"unexpected {name} status: {direct}")
        if name != "exact_original" and direct["status"] == PASS_STATUS:
            raise AssertionError(f"tampered case received PASS: {name}")
        if (cli_rc == 0) != (direct["status"] == PASS_STATUS):
            raise AssertionError(f"CLI exit code does not match disposition for {name}")
        rows.append({
            "case": name,
            "input_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "input_study_freeze_sha256": hashlib.sha256(study_bytes).hexdigest(),
            "input_predecessor_freeze_sha256": hashlib.sha256(predecessor_freeze_bytes).hexdigest(),
            "direct_status": direct["status"],
            "failure_stage": direct.get("stage") if direct["status"] != PASS_STATUS else None,
            "direct_cli_equal": True,
            "cli_exit_code": cli_rc,
            "no_false_pass": name == "exact_original" or direct["status"] != PASS_STATUS,
        })

    result = {
        "allocation_id": experiment_freeze["allocation_id"],
        "status": "PASS_RAW_BYTE_BINDING" if all(r["direct_cli_equal"] and r["no_false_pass"] for r in rows) else "FAIL_RAW_BYTE_BINDING",
        "cases": rows,
        "raw_input_sha256": hashlib.sha256(raw0).hexdigest(),
        "predecessor_freeze_sha256": hashlib.sha256(pred_freeze0).hexdigest(),
        "predecessor_study_freeze_sha256": hashlib.sha256(study_freeze0).hexdigest(),
        "source_sha256": {name: hashlib.sha256((source0 / name).read_bytes()).hexdigest() for name in ("audit.py", "test_audit.py")},
        "candidate_audit_sha256": hashlib.sha256(Path("/work/raw_byte_audit.py").read_bytes()).hexdigest(),
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "allocation_freeze_sha256": hashlib.sha256((input_dir / "FREEZE.json").read_bytes()).hexdigest(),
        "candidate_source_sha256": candidate_sources,
        "scope": "one bounded offline byte-provenance audit; no GUI/X11/input/model",
    }
    output_path = output_dir / "formal_result.json"
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["status"] != "PASS_RAW_BYTE_BINDING":
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: test_raw_byte_binding.py INPUT_DIR OUTPUT_DIR")
    main(sys.argv[1], sys.argv[2])
