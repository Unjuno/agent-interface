"""Freeze one wrong-anchor recovery allocation before execution."""
import json
from pathlib import Path

import preregister_openttd_active_evidence_pair_v1 as prior
import preregister_openttd_translated_compact_live_v1 as translated


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-wrong-anchor-recovery-live-01"
BASELINE = HERE / "results/openttd-anchor-first-live-01/report.json"
ARCHIVED_WRONG = HERE / "results/openttd-anchor-evidence-abba-01/wrong-1-result.json"
SOURCES = translated.SOURCES + [
    "preregister_openttd_wrong_anchor_recovery_live_v1.py",
    "run_openttd_wrong_anchor_recovery_live_v1.py",
    "anchor_evidence_contract_schema_v1.json",
    "anchor_evidence_contract_v1.py",
    "anchor_evidence_responder_v1.txt",
]


def main():
    archived = json.loads(ARCHIVED_WRONG.read_text(encoding="utf-8"))
    assert archived["typed"]["op"] == "expand_search"
    assert [archived["typed"]["point"]["x"], archived["typed"]["point"]["y"]] == [436, 51]
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    plan = {
        "status": "preregistered_before_one_fresh_fault_injection_live_execution",
        "study": "openttd-wrong-anchor-recovery-live-01", "seed": 991004,
        "model": "gpt-5.6-luna", "reasoning_effort": "low",
        "task": "open the company finances window after the same requested surface move",
        "fault_injection": {
            "source": str(ARCHIVED_WRONG.relative_to(HERE)),
            "source_sha256": prior.sha(ARCHIVED_WRONG),
            "archived_wrong_point": [436, 51],
            "transform": "add the newly observed whole-surface origin delta, then normalize to the nearest detected toolbar slot",
            "classification": "deterministic fault injection; not a natural model error or error-rate sample",
        },
        "policy": (
            "hover only the translated archived wrong anchor first; require the same Luna-low "
            "model to return expand_search; grant no click; collect the other four radius-2 "
            "slots; require strict five-receipt selection, exact selected rehover, ordinary "
            "released click and shifted independent finance oracle"),
        "positive_gate": (
            "one wrong receipt yields EXPANSION_REQUIRED; five verified receipts yield a different "
            "finance target; only the final selected click emits button_down; the shifted independent "
            "RGB oracle passes and every terminal verifies release"),
        "comparison": (
            "report receipt count, durable calls, model input tokens and stage timings; make no "
            "causal speed comparison because this is a recovery fault allocation"),
        "baseline_report": str(BASELINE.relative_to(HERE)),
        "baseline_sha256": prior.sha(BASELINE),
        "sources": {
            **{name: prior.sha(HERE / name) for name in dict.fromkeys(SOURCES)},
            **{name: prior.sha(HERE.parent / name) for name in prior.TASK_SOURCES},
        },
        "failure_policy": "retain the first fault allocation including failure; no model, runtime or task retry",
        "scope": (
            "one fixed-seed translated OpenTTD deterministic wrong-anchor fault; same Luna-low "
            "model for both semantic decisions, no subagents; proves recovery capability for this "
            "injected case only, not natural error frequency, general recovery, speed, resize/reflow, "
            "unknown-app or human-tempo performance"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
