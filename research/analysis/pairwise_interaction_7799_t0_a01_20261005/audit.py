"""Independent raw-only audit for Issue #7799 T0 eligibility output."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys


EXPECTED_COMMIT = "b5be19963454ce5edafc945b78b100012952dd15"
EXPECTED_PROTOCOL_ARMS = ["plain", "ephemeral", "persistent"]
EXPECTED_MISSING = [[0, 1], [1, 0]]
EXPECTED_CELLS = [[0, 0], [0, 1], [1, 0], [1, 1]]


def rank(matrix: list[list[int]]) -> int:
    work = [[float(x) for x in row] for row in matrix]
    pivot_row = 0
    columns = len(work[0]) if work else 0
    for column in range(columns):
        pivot = next((r for r in range(pivot_row, len(work))
                      if abs(work[r][column]) > 1e-12), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        value = work[pivot_row][column]
        work[pivot_row] = [x / value for x in work[pivot_row]]
        for r in range(len(work)):
            if r != pivot_row:
                factor = work[r][column]
                work[r] = [a - factor * b
                           for a, b in zip(work[r], work[pivot_row])]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW_JSON OUTPUT_JSON")
    raw_path, out_path = map(pathlib.Path, sys.argv[1:])
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    checks = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    check("schema", raw.get("schema") == "issue-7799-pairwise-eligibility-t0-v1",
          str(raw.get("schema")))
    check("source_commit", raw.get("source_commit") == EXPECTED_COMMIT,
          str(raw.get("source_commit")))
    check("protocol_arms", raw.get("protocol_arms") == EXPECTED_PROTOCOL_ARMS,
          repr(raw.get("protocol_arms")))
    cells = raw.get("observed_factor_cells")
    missing = raw.get("missing_factor_cells")
    check("required_cells", raw.get("required_2x2_cells") == EXPECTED_CELLS,
          repr(raw.get("required_2x2_cells")))
    check("observed_cell_set", cells == [[0, 0], [1, 1]], repr(cells))
    check("missing_cells", missing == EXPECTED_MISSING, repr(missing))
    vectors = raw.get("arm_factor_values", {})
    check("plain_factor_vector", vectors.get("plain") == [0, 0],
          repr(vectors.get("plain")))
    check("compiled_arms_coupled", vectors.get("ephemeral") == [1, 1]
          and vectors.get("persistent") == [1, 1], repr(vectors))
    design = [[1, a, b, a * b] for a, b in (tuple(row) for row in cells or [])]
    design_rank = rank(design)
    check("interaction_unidentifiable", design_rank < 4,
          f"rank={design_rank}, coefficients=4")
    check("hold_classification",
          raw.get("eligibility") == "HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR",
          str(raw.get("eligibility")))
    hashes = raw.get("source_sha256", {})
    check("two_source_pins", len(hashes) == 2 and all(
        isinstance(v, str) and len(v) == 64 for v in hashes.values()), repr(hashes))
    report = {
        "schema": "issue-7799-pairwise-eligibility-audit-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "checks": checks,
        "passed": sum(c["pass"] for c in checks),
        "total": len(checks),
        "decision": "PASS_AUDIT" if all(c["pass"] for c in checks)
                    else "FAIL_AUDIT",
        "rederived_design_matrix_rank": design_rank,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    return 0 if all(c["pass"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
