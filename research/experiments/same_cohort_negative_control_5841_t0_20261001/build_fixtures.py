"""Build the frozen, authored T0 fixture deck for Issue #5841."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = [1, 1, 0, 0]
CASES = ["clean_null", "true_primary_benefit", "route_missingness", "task_id_swap", "joint_export_error", "real_sentinel_collateral"]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


rows, oracle = [], []
for case in CASES:
    for route in ("direct", "guarded"):
        for n, primary in enumerate(BASE):
            task_id = f"{case}-task-{n+1}"
            truth_primary = primary
            if case == "true_primary_benefit" and route == "guarded" and n == 2:
                truth_primary = 1
            sentinel_after = 0
            if case == "real_sentinel_collateral" and route == "guarded" and n == 0:
                sentinel_after = 1
            observed_primary = truth_primary
            observed_after = sentinel_after
            if case == "route_missingness" and route == "guarded" and n >= 2:
                observed_primary = None
            if case == "joint_export_error" and route == "guarded":
                # Task-window-only export corruption; bracketing reference checks remain correct.
                observed_primary, observed_after = 1, 1
            observed_task_id = task_id
            if case == "task_id_swap" and route == "guarded" and n in (0, 1):
                observed_task_id = f"{case}-task-{2 if n == 0 else 1}"
            row = {
                "kind": "episode",
                "case": case,
                "route": route,
                "assigned_task_id": task_id,
                "observed_task_id": observed_task_id,
                "primary_observed": observed_primary,
                "sentinel_before_observed": 0,
                "sentinel_after_observed": observed_after,
                "outcome_record_present": observed_primary is not None,
            }
            rows.append(row)
            oracle.append({
                "case": case,
                "route": route,
                "assigned_task_id": task_id,
                "primary_true": truth_primary,
                "sentinel_before_true": 0,
                "sentinel_after_true": sentinel_after,
                "sentinel_is_route_null": case != "real_sentinel_collateral",
                "injected_mechanism": case,
            })

references = []
for case in CASES:
    for route in ("direct", "guarded"):
        for phase in ("pre", "post"):
            references.append({"kind": "reference", "case": case, "route": route, "phase": phase, "expected": 1, "observed": 1})

dump(ROOT / "reported_rows.json", rows)
dump(ROOT / "oracle.json", oracle)
dump(ROOT / "reference_deck.json", references)

