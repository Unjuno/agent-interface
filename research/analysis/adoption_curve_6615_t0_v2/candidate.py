"""Emit full first-use cumulative ledgers from a frozen synthetic fixture."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def route_rows(scenario: dict, route: str) -> list[dict]:
    setup = scenario[f"{route}_setup"]
    wall, active, verified = setup["wall_s"], setup["active_s"], 0
    rows = [{"scenario": scenario["id"], "route": route, "prefix": 0,
             "event": "SETUP_SUCCESS" if setup["success"] else "SETUP_FAILURE",
             "task_id": None, "wall_s": wall, "active_s": active,
             "verified_useful": False, "cumulative_wall_s": wall,
             "cumulative_active_s": active, "verified_count": 0,
             "supported": scenario["supported"]}]
    for index, task in enumerate(scenario["tasks"], 1):
        arm = task[route]
        if not setup["success"] or not scenario["supported"]:
            outcome, tw, ta, ok = "BLOCKED_SETUP_OR_UNSUPPORTED_HOST", 0, 0, False
        elif not arm["eligible"]:
            outcome, tw, ta, ok = "ROUTE_INELIGIBLE", arm["wall_s"], arm["active_s"], False
        else:
            repair = task.get("repair_before", {}) if route == "guarded" else {}
            tw, ta = arm["wall_s"] + repair.get("wall_s", 0), arm["active_s"] + repair.get("active_s", 0)
            ok = bool(arm["correct"])
            outcome = "VERIFIED_USEFUL" if ok else "ATTEMPTED_WRONG_OR_UNVERIFIED_EFFECT"
        wall += tw
        active += ta
        verified += int(ok)
        rows.append({"scenario": scenario["id"], "route": route, "prefix": index,
                     "event": outcome, "task_id": task["id"], "wall_s": tw,
                     "active_s": ta, "verified_useful": ok,
                     "cumulative_wall_s": wall, "cumulative_active_s": active,
                     "verified_count": verified, "supported": scenario["supported"]})
    return rows


def run(fixture: dict) -> list[dict]:
    return [row for scenario in fixture["scenarios"]
            for route in ("direct", "guarded")
            for row in route_rows(scenario, route)]


def main() -> None:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = run(fixture)
    Path(sys.argv[2]).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"allocation": fixture["allocation"], "rows": len(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
