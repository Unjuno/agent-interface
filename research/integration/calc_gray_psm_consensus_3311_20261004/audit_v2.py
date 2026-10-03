import hashlib
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parent
MODES = [6, 7, 8, 10, 13]
BOXES = [(37, 161, 87, 14), (127, 161, 88, 14), (217, 161, 88, 14)]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    errors = []
    expected = json.loads((ROOT / "truth" / "ORACLE_HOST_ONLY.json").read_text())
    frozen_inputs = json.loads((ROOT / "input" / "INPUTS.json").read_text())
    raw = json.loads((ROOT / "candidate-out" / "RAW.json").read_text())
    if raw.get("candidate") != "gray_nearest4x_white20_unanimous_psm_6_7_8_10_13_v1":
        errors.append("candidate identity mismatch")
    if len(raw.get("rows", [])) != len(frozen_inputs) or len(expected) != len(frozen_inputs):
        errors.append("frame cardinality mismatch")
    totals = {"numeric_exact_cells": 0, "numeric_total_cells": 0,
              "blank_unknown_cells": 0, "blank_total_cells": 0,
              "numeric_exact_frames": 0, "numeric_total_frames": 0,
              "blank_unknown_frames": 0, "blank_total_frames": 0,
              "cells": 0, "calls": 0}
    frame_results = []
    for frame, row in zip(frozen_inputs, raw.get("rows", [])):
        if row.get("id") != frame["id"] or row.get("source_sha256") != frame["sha256"]:
            errors.append("frame identity mismatch: " + frame["id"])
        if sha256(ROOT / "input" / frame["path"]) != frame["sha256"]:
            errors.append("input hash mismatch: " + frame["id"])
        oracle = expected.get(frame["id"])
        if len(row.get("cells", [])) != len(BOXES):
            errors.append("cell cardinality mismatch: " + frame["id"])
            continue
        row_exact = True
        row_numeric = oracle is not None
        row_blank_unknown = True
        for index, (cell, box) in enumerate(zip(row["cells"], BOXES)):
            totals["cells"] += 1
            calls = cell.get("calls", [])
            totals["calls"] += len(calls)
            if [call.get("psm") for call in calls] != MODES:
                errors.append(f"PSM inventory mismatch: {frame['id']} cell {index}")
            x, y, width, height = box
            expected_preprocess = [
                "-colorspace", "Gray", "-crop", f"{width}x{height}+{x}+{y}", "+repage",
                "-filter", "point", "-resize", f"{width * 4}x{height * 4}!",
                "-bordercolor", "white", "-border", "20",
            ]
            expected_value = oracle[index] if oracle is not None else None
            values = []
            for call, psm in zip(calls, MODES):
                argv = call.get("argv", [])
                if "--psm" not in argv or argv[argv.index("--psm") + 1] != str(psm):
                    errors.append(f"argv PSM mismatch: {frame['id']} cell {index} mode {psm}")
                prep_argv = call.get("preprocess_argv", [])
                if not all(part in prep_argv for part in expected_preprocess) or "-threshold" in prep_argv:
                    errors.append(f"preprocessing argv mismatch: {frame['id']} cell {index} mode {psm}")
                value = call.get("value")
                if call.get("exit_code") != 0:
                    value = None
                else:
                    stdout = call.get("stdout", "").strip()
                    parsed = stdout if stdout.isascii() and stdout.isdigit() else None
                    if parsed != value:
                        errors.append(f"parsed value mismatch: {frame['id']} cell {index} mode {psm}")
                    value = parsed
                values.append(value)
                if call.get("end_ns", 0) < call.get("start_ns", 0):
                    errors.append(f"time inversion: {frame['id']} cell {index} mode {psm}")
                if not re.fullmatch(r"[0-9a-f]{64}", call.get("crop_sha256", "")):
                    errors.append(f"crop hash malformed: {frame['id']} cell {index} mode {psm}")
            consensus = values[0] if len(values) == len(MODES) and values[0] is not None and all(v == values[0] for v in values) else None
            if cell.get("mode_values") != values or cell.get("consensus") != consensus:
                errors.append(f"consensus inconsistency: {frame['id']} cell {index}")
            if expected_value is None:
                totals["blank_total_cells"] += 1
                if consensus is None:
                    totals["blank_unknown_cells"] += 1
                else:
                    row_blank_unknown = False
                row_exact = row_exact and consensus is None
            else:
                totals["numeric_total_cells"] += 1
                if consensus == expected_value:
                    totals["numeric_exact_cells"] += 1
                else:
                    row_exact = False
        if row_numeric:
            totals["numeric_total_frames"] += 1
            if row_exact:
                totals["numeric_exact_frames"] += 1
        else:
            totals["blank_total_frames"] += 1
            if row_blank_unknown:
                totals["blank_unknown_frames"] += 1
        frame_results.append({"id": frame["id"], "oracle_kind": "numeric" if row_numeric else "blank", "row_exact": row_exact, "blank_all_unknown": row_blank_unknown})
    numeric_pass = totals["numeric_exact_cells"] == totals["numeric_total_cells"]
    blank_pass = totals["blank_unknown_cells"] == totals["blank_total_cells"]
    totals["disposition"] = "PASS_CANDIDATE_GATE_SCOPED" if numeric_pass and blank_pass else "REJECT_GRAY_PSM_CONSENSUS_CANDIDATE"
    if totals["calls"] != totals["cells"] * len(MODES):
        errors.append("call cardinality mismatch")
    result = {"status": "PASS_AUDIT_SCOPED" if not errors else "FAIL_AUDIT", "totals": totals, "frame_results": frame_results, "errors": errors,
              "interpretation": "Audit integrity is separate from the candidate disposition; repeated frames are not independent samples."}
    with (ROOT / "AUDIT_V2.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
