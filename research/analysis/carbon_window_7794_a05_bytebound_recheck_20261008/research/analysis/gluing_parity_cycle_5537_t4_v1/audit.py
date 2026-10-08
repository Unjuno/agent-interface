#!/usr/bin/env python3
"""Independent exhaustive raw-only checker for Issue #5537 T4."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

RAW = Path(__file__).with_name("raw") / "formal.jsonl"
VARS = ("x", "y", "z")
EXPECTED_CASES = {"pairwise_compatible_parity_cycle", "coherent_equality_control", "missing_context_control"}
EXPECTED_CONTEXTS = {
    "pairwise_compatible_parity_cycle": [
        {"name": "C_xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]]},
        {"name": "C_yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]]},
        {"name": "C_zx", "vars": ["z", "x"], "tuples": [[0, 1], [1, 0]]},
    ],
    "coherent_equality_control": [
        {"name": "C_xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]]},
        {"name": "C_yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]]},
        {"name": "C_zx", "vars": ["z", "x"], "tuples": [[0, 0], [1, 1]]},
    ],
    "missing_context_control": [
        {"name": "C_xy", "vars": ["x", "y"], "tuples": [[0, 0], [1, 1]]},
        {"name": "C_yz", "vars": ["y", "z"], "tuples": [[0, 0], [1, 1]]},
    ],
}


def ref_sections(contexts):
    found = []
    for bits in itertools.product((0, 1), repeat=3):
        assignment = dict(zip(VARS, bits))
        if all(any(all(assignment[v] == value for v, value in zip(c["vars"], row)) for row in c["tuples"]) for c in contexts):
            found.append(assignment)
    return found


def ref_pairwise(contexts):
    for i, left in enumerate(contexts):
        for right in contexts[i + 1:]:
            for variable in set(left["vars"]) & set(right["vars"]):
                li = left["vars"].index(variable)
                ri = right["vars"].index(variable)
                lp = {row[li] for row in left["tuples"]}
                rp = {row[ri] for row in right["tuples"]}
                if lp != rp:
                    return False
    return True


def errors(rows):
    problems, seen, cases = [], set(), set()
    for n, row in enumerate(rows):
        cases.add(row.get("case"))
        if row.get("contexts") != EXPECTED_CONTEXTS.get(row.get("case")):
            problems.append(f"row {n}: frozen context fixture mismatch")
        payload = {k: v for k, v in row.items() if k != "record_id"}
        rid = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if row.get("record_id") != rid or rid in seen:
            problems.append(f"row {n}: record identity invalid")
        seen.add(rid)
        complete = row["case"] != "missing_context_control"
        sections = ref_sections(row["contexts"]) if complete else []
        expected_status = "UNKNOWN" if not complete else "GLOBAL_SECTION_CERTIFIED" if sections else "NO_GLOBAL_SECTION"
        for field, value in (("complete", complete), ("pairwise_compatible", ref_pairwise(row["contexts"])),
                             ("global_sections", sections), ("status", expected_status),
                             ("irreversible_admitted", expected_status == "GLOBAL_SECTION_CERTIFIED")):
            if row.get(field) != value:
                problems.append(f"row {n}: {field} mismatch")
    if len(rows) != 3 or cases != EXPECTED_CASES:
        problems.append("case coverage mismatch")
    return problems


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    base = errors(rows)
    changed = [dict(r) for r in rows]
    changed[0]["status"] = "GLOBAL_SECTION_CERTIFIED"
    changed_context = [dict(r) for r in rows]
    changed_context[0]["contexts"] = EXPECTED_CONTEXTS["coherent_equality_control"]
    controls = {"false_certificate_rejected": bool(errors(changed)),
                "changed_context_rejected": bool(errors(changed_context)),
                "dropped_case_rejected": bool(errors(rows[:-1])),
                "duplicate_case_rejected": bool(errors(rows + [rows[0]]))}
    result = {"status": "PASS_SCOPED" if not base and all(controls.values()) else "FAIL_AUDIT",
              "rows": len(rows), "errors": base, "mutation_controls": controls,
              "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    out = RAW.with_name("audit.json")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
