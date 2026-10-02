"""Independent raw-only CRAN/R and Python implementation parity audit."""

import hashlib
import json
import math
import sys
from pathlib import Path


def as_indices(value):
    if value is None:
        return []
    return sorted(value if isinstance(value, list) else [value])


def main() -> int:
    r_rows = json.loads(Path(sys.argv[1]).read_text())["rows"]
    py_rows = json.loads(Path(sys.argv[2]).read_text())["rows"]
    sample_dir = Path(sys.argv[3])
    config = json.loads(Path(sys.argv[4]).read_text())
    errors = []
    if len(r_rows) != len(py_rows):
        errors.append(f"row count mismatch R={len(r_rows)} Python={len(py_rows)}")

    for row_number, (rrow, prow) in enumerate(zip(r_rows, py_rows)):
        seed = rrow.get("seed", row_number)
        label = f"seed-{seed}"
        if rrow.get("seed") != prow.get("seed"):
            errors.append(f"{label} seed mismatch")
            continue
        sample_bytes = (sample_dir / f"{seed}.txt").read_bytes()
        values = [float(value) for value in sample_bytes.decode().splitlines()]
        if len(values) != config["n"]:
            errors.append(f"{label} sample length mismatch")

        candidate_count = round(
            config["candidate_fraction_of_tail"]
            * (1 - config["threshold_probability"])
            * len(values)
        )
        expected_candidates = [
            index + 1
            for index in sorted(
                range(len(values)), key=lambda i: values[i], reverse=True
            )[:candidate_count]
        ]
        if rrow.get("candidate_indices") != expected_candidates:
            errors.append(f"{label} R candidate indices/order disagree with raw order statistic")
        if prow.get("candidate_indices") != expected_candidates:
            errors.append(f"{label} Python candidate indices/order disagree with raw order statistic")
        if rrow.get("candidate_indices") != prow.get("candidate_indices"):
            errors.append(f"{label} candidate indices/order mismatch")
        if prow.get("sample_sha256") != hashlib.sha256(sample_bytes).hexdigest():
            errors.append(f"{label} Python sample hash mismatch")

        ordered = sorted(values)
        h = (len(values) - 1) * config["threshold_probability"]
        lower = math.floor(h)
        expected_threshold = ordered[lower] + (h - lower) * (
            ordered[min(lower + 1, len(values) - 1)] - ordered[lower]
        )
        for name, row in (("R", rrow), ("Python", prow)):
            if abs(expected_threshold - row.get("threshold", math.inf)) > config["acceptance"]["threshold_abs_tolerance"]:
                errors.append(f"{label} {name} raw type-7 threshold mismatch")

        if as_indices(rrow.get("upper_sensitive_indices")) != as_indices(
            prow.get("sensitive_indices")
        ):
            errors.append(f"{label} sensitive-index set mismatch")

        r_states = rrow.get("states", [])
        py_states = prow.get("states", [])
        if len(r_states) < len(py_states):
            errors.append(f"{label} R has fewer refit states than Python")
        for index, (rstate, pstate) in enumerate(zip(r_states, py_states)):
            rfit = rstate.get("fit", [])
            pfit = pstate.get("fit", [])
            if len(rfit) != 2 or len(pfit) != 2:
                errors.append(f"{label} state {index} malformed MLE")
                continue
            scale_delta = abs(rfit[0] - pfit[0]) / max(abs(rfit[0]), 1e-12)
            shape_delta = abs(rfit[1] - pfit[1])
            ci_delta = max(
                abs(a - b)
                for a, b in zip(rstate.get("ci", []), pstate.get("ci", []), strict=True)
            )
            if scale_delta > config["acceptance"]["scale_rel_tolerance"]:
                errors.append(f"{label} state {index} scale mismatch relative={scale_delta:.9g}")
            if shape_delta > config["acceptance"]["shape_abs_tolerance"]:
                errors.append(f"{label} state {index} shape mismatch absolute={shape_delta:.9g}")
            if ci_delta > config["acceptance"]["conf_interval_abs_tolerance"]:
                errors.append(f"{label} state {index} CI mismatch absolute={ci_delta:.9g}")
            if index and rstate.get("restored_index") != pstate.get("restored_index"):
                errors.append(f"{label} state {index} restoration order mismatch")
        if not all(state.get("convergence") == 0 for state in r_states):
            errors.append(f"{label} at least one R fit did not converge")

    print(f"R cases={len(r_rows)}; Python cases={len(py_rows)}")
    for error in errors:
        print("MISMATCH", error)
    if errors:
        print(f"FAIL_PARITY mismatches={len(errors)}")
        return 1
    print("PASS_PARITY raw selection, thresholds, cumulative MLE/CI states, convergence, and sensitive indices match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
