"""Bounded synthetic audit of owner-helper pagination completeness."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/map01-owner-pagination-source")
from formal_allocation_global_owner_v1 import select_global_owner

PATH = ".github/workflows/synthetic-map01.yml"
ALLOC = "synthetic-map01-allocation"


def row(run_id: int, number: int) -> dict:
    return {
        "id": run_id,
        "run_number": number,
        "path": PATH,
        "head_branch": "main",
        "head_sha": f"{run_id:040x}",
        "status": "completed",
    }


def independent_full_set_oracle(full_rows: list[dict], current_id: int) -> bool:
    matching = [r for r in full_rows if r.get("path") == PATH]
    if not matching or any(not isinstance(r.get("id"), int) for r in matching):
        return False
    earliest = min(matching, key=lambda r: (r["run_number"], r["id"]))
    return earliest["id"] == current_id and all(r["head_branch"] == "main" for r in matching)


def main() -> None:
    cases = []
    counterexamples = []
    for n in (2, 3):
        full = [row(i, i) for i in range(1, n + 1)]
        for current in range(1, n + 1):
            for page_size in range(1, n + 1):
                for subset in itertools.combinations(full, page_size):
                    for duplicate_indices in itertools.product(range(len(subset)), repeat=1):
                        visible = list(subset)
                        if page_size > 1:
                            visible.append(dict(subset[duplicate_indices[0]]))
                        payload = {"workflow_runs": visible, "total_count": len(visible)}
                        helper = select_global_owner(
                            payload,
                            current_run_id=current,
                            workflow_path=PATH,
                            allocation_id=ALLOC,
                        )
                        oracle = independent_full_set_oracle(full, current)
                        incomplete = len({r["id"] for r in visible}) < n
                        case = {
                            "full_run_ids": [r["id"] for r in full],
                            "visible_run_ids": [r["id"] for r in visible],
                            "api_total_count": len(visible),
                            "current_run_id": current,
                            "incomplete": incomplete,
                            "helper_result": helper["result_class"],
                            "helper_admitted": helper["may_enter_formal_step"],
                            "oracle_admitted": oracle,
                        }
                        cases.append(case)
                        if incomplete and helper["may_enter_formal_step"] and not oracle:
                            counterexamples.append(case)
    result = {
        "schema": "map01-owner-pagination-integrity-59-t1-result-v1",
        "source_intake": "5eb0c44f2fc3d851b6469ceabda57b091ec76668",
        "case_count": len(cases),
        "counterexample_count": len(counterexamples),
        "decision": "PASS_BOUNDED_FAIL_CLOSED_GAP_FOUND" if counterexamples else "HOLD_NO_GAP_IN_BOUNDED_MODEL",
        "counterexamples": counterexamples,
        "cases": cases,
        "scope": "synthetic payload/parser model only; no claim GitHub emits duplicate IDs or misstates total_count",
    }
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/map01-owner-pagination-candidate.json")
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: result[k] for k in ("case_count", "counterexample_count", "decision", "counterexamples")}, indent=2))


if __name__ == "__main__":
    main()
