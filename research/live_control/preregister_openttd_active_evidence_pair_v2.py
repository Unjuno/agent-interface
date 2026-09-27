"""Freeze screen-derived local toolbar probing before fresh execution."""
import json
from pathlib import Path

import preregister_openttd_active_evidence_pair_v1 as prior


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-active-evidence-pair-02"
LIVE = prior.LIVE_SOURCES + [
    "run_openttd_active_evidence_pair_v1.py",
    "run_openttd_active_evidence_pair_v2.py",
    "preregister_openttd_active_evidence_pair_v2.py",
    "openttd_toolbar_slots_v1.py",
    "openttd_hover_receipt_batches_v1.py",
    "openttd_hover_receipt_sheet_v1.py",
    "evidence_target_contract_schema_v2.json",
]


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    plan = {
        "status": "preregistered_before_fresh_openttd_execution",
        "study": "openttd-active-evidence-pair-02",
        "execution_order": [
            {"name": "association-fault", "association_fault": True, "seed": 991004},
            {"name": "stable", "association_fault": False, "seed": 991004},
        ],
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "task": "open the company finances window",
        "candidate_policy": (
            "use the model direct point, or median-x candidate when it requests probing, as a "
            "coarse anchor; detect repeated 22px toolbar slots from exact source pixels; probe the "
            "anchor slot plus two slots on each side; no semantic labels or answer point in code"),
        "batch_policy": (
            "split five 800ms persistent hover probes into at most three points per submit to "
            "preserve the runtime 3000ms passive-dwell bound; compose only under identical binding"),
        "positive": (
            "same model selects one of five persistent tooltip receipts; exact selected receipt is "
            "rehovered before ordinary admission; fixed-seed exact-title oracle must succeed"),
        "negative": (
            "reverse the first batch receipt association after actual hover execution; composition "
            "must refuse before the second model call and target input"),
        "failure_policy": "retain both first formal sessions; no model or runtime retry and no repair",
        "sources": {
            **{name: prior.sha(HERE / name) for name in dict.fromkeys(LIVE)},
            **{name: prior.sha(HERE.parent / name) for name in prior.TASK_SOURCES},
        },
        "scope": (
            "two fresh same-seed X11 cases and one OpenTTD toolbar task; same Luna-low model; "
            "model supplies the coarse anchor and selects runtime evidence; no broad unknown-GUI, "
            "cross-toolkit, latency, token-reduction or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
