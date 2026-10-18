"""Raw/provenance and mutation audit for the retained reader-transfer result."""
import copy
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(result, root, git_root):
    errors = []
    if result.get("execution_id") != FREEZE["execution_id"]:
        errors.append("execution id")
    if result.get("base_commit") != FREEZE["base_commit"]:
        errors.append("base commit")
    if result.get("freeze_sha256") != sha((PACKAGE / "FREEZE.json").read_bytes()):
        errors.append("freeze hash")
    if result.get("wad_sha256") != FREEZE["wad_sha256"]:
        errors.append("WAD identity")
    if result.get("input_sha256") != FREEZE["input_sha256"]:
        errors.append("frozen input hash map")
    if result.get("runtime") is None or any(
            result["runtime"].get(key) != value
            for key, value in FREEZE["runtime_versions"].items()):
        errors.append("runtime versions")
    if result.get("frame_count") != FREEZE["expected_frames"]:
        errors.append("frame count")
    rows = result.get("rows")
    if type(rows) is not list or len(rows) != FREEZE["expected_frames"]:
        errors.append("rows shape")
        return errors
    if result.get("observed_matching_values") != FREEZE["expected_frames"]:
        errors.append("matched values")
    if result.get("blank_roi_unknown") != FREEZE["expected_frames"]:
        errors.append("blank ROI controls")
    if result.get("blank_roi_total") != FREEZE["expected_frames"]:
        errors.append("blank ROI denominator")
    if result.get("status") != "PASS_CROSS_RUN_HEALTH_READER":
        errors.append("result status")
    for index, row in enumerate(rows):
        if row.get("index") != index:
            errors.append(f"row order {index}")
        if row.get("source_file") != FREEZE["frames"][index]["source_file"]:
            errors.append(f"source file {index}")
        if row.get("frame_sha256") != FREEZE["frames"][index]["sha256"]:
            errors.append(f"frame hash {index}")
        if row.get("sequence") != FREEZE["frames"][index]["sequence"]:
            errors.append(f"sequence {index}")
        if row.get("capture_ns") != FREEZE["frames"][index]["capture_ns"]:
            errors.append(f"capture time {index}")
        if row.get("pointer_binding") != FREEZE["frames"][index]["pointer_binding"]:
            errors.append(f"binding {index}")
        if row.get("expected_manual_health") != FREEZE["manual_health"][index]:
            errors.append(f"manual value {index}")
        if row.get("reader_status") != "observed":
            errors.append(f"reader status {index}")
        if row.get("reader_value") != FREEZE["manual_health"][index]:
            errors.append(f"reader value {index}")
        if row.get("blank_roi_status") != "unknown":
            errors.append(f"negative control {index}")
        if type(row.get("reader_slots")) is not list or len(row["reader_slots"]) != 3:
            errors.append(f"slot count {index}")
        else:
            digits = [slot.get("digit") for slot in row["reader_slots"]]
            rendered = int("".join(str(digit) for digit in digits if digit is not None))
            if rendered != row.get("reader_value"):
                errors.append(f"slot arithmetic {index}")
            for slot in row["reader_slots"]:
                if slot.get("digit") is None:
                    if slot.get("best_score", 1) >= 0.80:
                        errors.append(f"blank-slot score threshold {index}")
                else:
                    if not (0.80 <= slot.get("best_score", -1) <= 1.0):
                        errors.append(f"glyph score floor {index}")
                    if slot.get("best_score", 0) - slot.get("second_score", 0) < 0.05:
                        errors.append(f"glyph score margin {index}")
    for relative, expected in FREEZE["input_sha256"].items():
        actual = sha((root / relative).read_bytes())
        if actual != expected:
            errors.append(f"input hash {relative}")
    for relative, expected in FREEZE["source_blobs"].items():
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{FREEZE['base_commit']}:{relative}"],
            cwd=git_root, text=True).strip()
        if actual != expected:
            errors.append(f"source blob {relative}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.repo_root.resolve()
    git_root = args.git_root.resolve()
    result_path = PACKAGE / "results" / "a01.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(result, root, git_root)
    controls = []
    for mutate in (
            lambda x: x["rows"][0].__setitem__("reader_value", 99),
            lambda x: x["rows"][0].__setitem__("capture_ns", -1),
            lambda x: x["rows"][0].__setitem__("frame_sha256", "0" * 64),
            lambda x: x["rows"][0].__setitem__("reader_status", "unknown"),
            lambda x: x.__setitem__("blank_roi_unknown", 0)):
        mutant = copy.deepcopy(result)
        mutate(mutant)
        controls.append(bool(validate(mutant, root, git_root)))
    if not all(controls):
        errors.append("copied-result mutation control failed")
    audit_result = {
        "schema": "astra-v39-hud-reader-transfer-audit-v1",
        "status": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT",
        "errors": errors,
        "reconstructed": {
            "frames": len(result.get("rows", [])),
            "matching_values": result.get("observed_matching_values"),
            "blank_roi_unknown": result.get("blank_roi_unknown"),
        },
        "copied_result_mutation_controls_passed": sum(controls),
        "copied_result_mutation_controls_total": len(controls),
        "scope": "artifact/provenance audit; does not independently reimplement glyph extraction",
    }
    out = PACKAGE / "results" / "audit.json"
    out.write_text(json.dumps(audit_result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(audit_result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
