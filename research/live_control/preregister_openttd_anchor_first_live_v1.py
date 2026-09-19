"""Freeze one anchor-first translated OpenTTD live allocation."""
import json
from pathlib import Path

import preregister_openttd_active_evidence_pair_v1 as prior
import preregister_openttd_translated_compact_live_v1 as translated


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-anchor-first-live-01"
BASELINE = HERE / "results/openttd-translated-compact-live-01/report.json"
SOURCES = translated.SOURCES + [
    "preregister_openttd_anchor_first_live_v1.py",
    "run_openttd_anchor_first_live_v1.py",
    "anchor_evidence_contract_schema_v1.json",
    "anchor_evidence_contract_v1.py",
    "anchor_evidence_responder_v1.txt",
]


def main():
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    plan = {
        "status": "preregistered_before_one_fresh_anchor_first_live_execution",
        "study": "openttd-anchor-first-live-01", "seed": 991004,
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "task": "open the company finances window after the same requested surface move",
        "policy": (
            "derive the nearest slot to the model coarse anchor; hover only that slot first; the "
            "same model accepts only a matching verified tooltip or requests expansion; on "
            "expansion collect the other four radius-2 slots and run the existing five-receipt "
            "selection; exact selected rehover remains mandatory before ordinary click"),
        "positive_gate": (
            "fresh natural anchor takes the one-receipt branch, opens finances, releases input, "
            "and passes the shifted independent RGB oracle"),
        "comparison": (
            "report deterministic hover, durable-call and exact-frame differences against the "
            "immutable prior five-receipt translated live allocation; total/model latency is "
            "descriptive because the sequential sessions are not order-balanced"),
        "baseline_report": str(BASELINE.relative_to(HERE)),
        "baseline_sha256": prior.sha(BASELINE),
        "sources": {
            **{name: prior.sha(HERE / name) for name in dict.fromkeys(SOURCES)},
            **{name: prior.sha(HERE.parent / name) for name in prior.TASK_SOURCES},
        },
        "failure_policy": "retain the first live allocation; no model, runtime or task retry",
        "scope": (
            "one fresh fixed-seed translated OpenTTD task after fixed archived branch evidence; "
            "same Luna-low model, no subagents; no order-balanced total-latency claim, live wrong-"
            "anchor expansion efficacy, resize/reflow, unknown-app or human-tempo claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
