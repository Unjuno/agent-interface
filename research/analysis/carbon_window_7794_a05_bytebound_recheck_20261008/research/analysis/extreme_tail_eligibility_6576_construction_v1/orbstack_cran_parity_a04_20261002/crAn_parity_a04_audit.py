"""Independent exact-data comparison of CRAN/R and Python candidate artifacts."""

import json
import sys
import hashlib
import math
from pathlib import Path


def main() -> int:
    r_rows = json.loads(Path(sys.argv[1]).read_text())["rows"]
    py_rows = json.loads(Path(sys.argv[2]).read_text())["rows"]
    sample_dir = Path(sys.argv[3])
    config = json.loads(Path(sys.argv[4]).read_text())
    errors = []
    if len(r_rows) != len(py_rows):
        errors.append(f"row count mismatch R={len(r_rows)} Python={len(py_rows)}")
    for rrow, prow in zip(r_rows, py_rows, strict=True):
        if rrow["seed"] != prow["seed"]:
            errors.append(f"seed mismatch {rrow['seed']} {prow['seed']}")
            continue
        if rrow["candidate_indices"] != prow["candidate_indices"]:
            errors.append(f"{rrow['case_id']} candidate-index mismatch R={rrow['candidate_indices']} Python={prow['candidate_indices']}")
        sample_path = sample_dir / f"{rrow['seed']}.txt"
        sample_bytes = sample_path.read_bytes()
        values = [float(value) for value in sample_bytes.decode().splitlines()]
        count = round(config["candidate_fraction_of_tail"] * (1 - config["threshold_probability"]) * len(values))
        expected_indices = sorted(sorted(range(len(values)), key=lambda i: values[i], reverse=True)[:count])
        expected_indices = [index + 1 for index in expected_indices]
        if prow.get("sample_sha256") != hashlib.sha256(sample_bytes).hexdigest():
            errors.append(f"{rrow['case_id']} sample hash mismatch")
        if prow["candidate_indices"] != expected_indices:
            errors.append(f"{rrow['case_id']} raw-only candidate selection mismatch")
        ordered = sorted(values)
        h = (len(values) - 1) * config["threshold_probability"]
        lower = math.floor(h)
        expected_threshold = ordered[lower] + (h - lower) * (ordered[min(lower + 1, len(values) - 1)] - ordered[lower])
        if abs(expected_threshold - rrow["threshold"]) > 1e-10 or abs(expected_threshold - prow["threshold"]) > 1e-10:
            errors.append(f"{rrow['case_id']} raw-only type-7 threshold mismatch")
        if len(rrow["states"]) < len(prow["states"]):
            errors.append(f"{rrow['case_id']} insufficient R fit states")
        if rrow["upper_sensitive_indices"] != prow["sensitive_indices"]:
            errors.append(f"{rrow['case_id']} sensitive-index mismatch R={rrow['upper_sensitive_indices']} Python={prow['sensitive_indices']}")
        for index, (rstate, pstate) in enumerate(zip(rrow["states"], prow["states"])):
            rfit = rstate["fit"]
            pfit = pstate["fit"]
            if len(rfit) != 2 or len(pfit) != 2:
                errors.append(f"{rrow['case_id']} state {index} malformed fit")
                continue
            if abs(rfit[0] - pfit[0]) > 1e-5 * max(abs(rfit[0]), 1e-12):
                errors.append(f"{rrow['case_id']} state {index} scale mismatch R={rfit[0]} Python={pfit[0]}")
            if abs(rfit[1] - pfit[1]) > 1e-5:
                errors.append(f"{rrow['case_id']} state {index} shape mismatch R={rfit[1]} Python={pfit[1]}")
            if any(abs(a - b) > 1e-5 for a, b in zip(rstate["ci"], pstate["ci"], strict=True)):
                errors.append(f"{rrow['case_id']} state {index} CI mismatch")
        if not all(state.get("convergence", 0) == 0 for state in rrow["states"]):
            errors.append(f"{rrow['case_id']} R MLE did not converge")
    print(f"R cases={len(r_rows)}; Python cases={len(py_rows)}")
    for error in errors:
        print("MISMATCH", error)
    if errors:
        print(f"FAIL_PARITY mismatches={len(errors)}")
        return 1
    print("PASS_PARITY raw selection, thresholds, all compared MLE/CI states, and sensitive indices match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
