"""Independent structural audit for the #5306 construction probe output."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import voi_probe  # noqa: E402 -- frozen case table only; no policy/reducer functions imported


def expected_policy(case: dict, policy: str) -> list[str]:
    feasible = {name for name, val in case["checks"].items()
                if name in ("M", "X", "Y") and val[2] <= case["deadline"]}
    if case["stale"] or case["gap"] or "M" not in feasible:
        return []
    if policy == "FIXED":
        return [name for name in ("M", "X", "Y") if name in feasible]
    if policy == "SELECTIVE":
        return ([name for name in ("M", "X", "Y") if name in feasible]
                if case["ambiguous"] else ["M"])
    if policy == "VOI":
        # Frozen planning contract: M is mandatory; X has positive net value.
        # Its exact signal resolves this toy case, so no Y check follows.
        return ["M", "X"] if "X" in feasible else ["M"]
    return []


def independent_reduce(case: dict, checks: list[str]) -> str:
    if case["stale"] or case["gap"] or "M" not in checks:
        return "YIELD"
    if any(name != "M" and case["checks"][name][0] == 1 for name in checks):
        return "BLOCK"
    return "ALLOW"


def independent_loss(case: dict, disposition: str) -> int:
    if disposition == "YIELD":
        return 12
    if disposition == "ALLOW" and case["hazard"]:
        return 100
    if disposition == "BLOCK" and not case["hazard"]:
        return 5
    return 0


def audit() -> dict:
    observed = json.loads(subprocess.check_output([sys.executable, str(HERE / "voi_probe.py")], text=True))
    expected_cases = {c["id"]: c for c in voi_probe.CASES}
    errors = []
    if len(observed.get("rows", [])) != len(expected_cases) * 3:
        errors.append("row_count")
    for row in observed.get("rows", []):
        case = expected_cases.get(row.get("case"))
        if case is None:
            errors.append("unknown_case")
            continue
        policy = row.get("policy")
        expected_checks = expected_policy(case, policy)
        if policy == "VOI" and "X" in expected_checks:
            # This arm is expected to stop immediately after X's decisive signal.
            expected_checks = expected_checks[:2]
        if row.get("checks") != expected_checks:
            errors.append(f"check_policy:{row['case']}:{policy}")
        if row.get("cost") != sum(case["checks"][name][2] for name in expected_checks):
            errors.append(f"cost:{row['case']}:{policy}")
        expected_disp = independent_reduce(case, expected_checks)
        if row.get("disposition") != expected_disp:
            errors.append(f"reducer:{row['case']}:{policy}")
        if row.get("loss") != independent_loss(case, expected_disp):
            errors.append(f"loss:{row['case']}:{policy}")
        if row.get("disposition") == "ALLOW" and (case["stale"] or case["gap"]):
            errors.append(f"unsafe_yield_bypass:{row['case']}:{policy}")
    # The probe must surface whether its preregistered held-out gate actually passes.
    s = observed["summary"]["heldout"]
    heldout_voi_beats_selective = (s["VOI"]["cost"] < s["SELECTIVE"]["cost"] and
                                   s["VOI"]["loss"] <= s["SELECTIVE"]["loss"] and
                                   s["VOI"]["false_allows"] == 0)
    return {"audit": "independent_reducer_and_accounting_v1", "errors": errors,
            "row_count": len(observed["rows"]), "heldout_voi_beats_selective": heldout_voi_beats_selective,
            "disposition": "CONSTRUCTION_GATE_FAIL" if errors else "CONSTRUCTION_AUDIT_PASS_GATE_FAIL",
            "summary": observed["summary"]}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True, indent=2))
