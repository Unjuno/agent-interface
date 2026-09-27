"""Freeze one translated-layout compact active-evidence allocation."""
import json
from pathlib import Path

import preregister_openttd_active_evidence_pair_v1 as prior


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-translated-compact-live-01"
SOURCES = prior.LIVE_SOURCES + [
    "run_openttd_active_evidence_pair_v1.py",
    "preregister_openttd_translated_compact_live_v1.py",
    "run_openttd_translated_compact_live_v1.py",
    "openttd_toolbar_slots_v2.py",
    "openttd_hover_receipt_batches_v1.py",
    "openttd_compact_hover_sheet_v1.py",
    "openttd_finance_oracle_v2.py",
    "evidence_target_contract_v1.py",
    "evidence_target_contract_schema_v2.json",
    "evidence_target_reference_responder_v2.txt",
]


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    plan = {
        "status": "preregistered_before_one_fresh_translated_openttd_execution",
        "study": "openttd-translated-compact-live-01",
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "task": "open the company finances window",
        "surface_intervention": (
            "after initial stabilization request test_move_surface dx20 dy8, settle, then derive "
            "all subsequent screen positions from the fresh moved observation"),
        "candidate_policy": (
            "model supplies a coarse point; discover the unique maximum repeated 20-24px slot "
            "row across the full moved screen; probe the nearest slot plus two on each side"),
        "evidence_policy": (
            "five persistent 800ms hover receipts in bounded 3+2 batches; pass only exact tooltip "
            "pixels plus receipt/point bindings to the same model; exact rehover before click"),
        "success": (
            "nonzero actual surface delta, dynamically detected toolbar row at the moved surface "
            "top, five composed receipts, strict evidence-bound selection, exact rehover, released "
            "ordinary click, and independent finance-title RGB oracle shifted only by observed delta"),
        "failure_policy": "retain the first live allocation; no model, runtime or task retry",
        "sources": {
            **{name: prior.sha(HERE / name) for name in dict.fromkeys(SOURCES)},
            **{name: prior.sha(HERE.parent / name) for name in prior.TASK_SOURCES},
        },
        "scope": (
            "one fresh fixed-seed OpenTTD translated-window task; same single Luna-low model "
            "proposes and interprets evidence; no subagents; no matched latency/token baseline, "
            "unknown-app, resize/reflow, cross-toolkit, broad reliability or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
