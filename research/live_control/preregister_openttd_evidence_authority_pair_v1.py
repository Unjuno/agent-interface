"""Freeze one fresh positive/no-match OpenTTD authority pair."""
import json
from pathlib import Path
import shutil

import preregister_openttd_active_evidence_pair_v1 as prior
import preregister_openttd_translated_compact_live_v1 as translated

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-evidence-authority-pair-01"
BASELINE = HERE / "results/openttd-wrong-anchor-recovery-live-02/report.json"
ARCHIVED_WRONG = HERE / "results/openttd-anchor-evidence-abba-01/wrong-1-result.json"
CACHE_SOURCES = [
    HERE / "results/schema-preflight-gate-01/cache/d673b6dee8f288ab3a98460f748f81e468d928f4b32332c0b72d04134767fdb3.json",
    HERE / "results/evidence-target-contract-v2-01/cache/b45ef3be88084ecbb48e53ccaaf8baab99996185e8aeb0919e7c1707d4f49ae2.json",
]
SOURCES = translated.SOURCES + [
    "preregister_openttd_evidence_authority_pair_v1.py",
    "run_openttd_evidence_authority_pair_v1.py",
    "anchor_evidence_contract_schema_v1.json", "anchor_evidence_contract_v1.py",
    "anchor_evidence_responder_v1.txt", "evidence_target_contract_schema_v3.json",
    "evidence_target_contract_v2.py", "evidence_target_reference_responder_v3.txt",
    "schema_preflight_gate_v1.py", "schema_preflight_v1.py",
    "schema_preflight_responder_v1.txt", "target_handle_model_runner_v2.py",
]


def main():
    archived = json.loads(ARCHIVED_WRONG.read_text(encoding="utf-8"))
    assert archived["typed"]["op"] == "expand_search"
    OUT.mkdir(parents=True, exist_ok=False); (OUT / "empty-workspace").mkdir()
    cache = OUT / "schema-cache"; cache.mkdir()
    for source in CACHE_SOURCES: shutil.copy2(source, cache / source.name)
    plan = {
        "status": "preregistered_before_one_fresh_positive-no-match-live-pair",
        "study": "openttd-evidence-authority-pair-01", "seed": 991004,
        "model": "gpt-5.6-luna", "reasoning_effort": "low", "condition_order": ["positive", "no-match"],
        "task": "choose from the same five persistent hover receipts, then either open the requested control or withhold target input",
        "preflight_schemas": [{"name": "anchor", "schema": "anchor_evidence_contract_schema_v1.json"},
            {"name": "selection", "schema": "evidence_target_contract_schema_v3.json"}],
        "conditions": {"positive": "Company Finances is receipt5 and must independently open",
            "no-match": "Airport construction is absent from all five receipts; require NO_TARGET_AUTHORITY and no target button"},
        "policy": "fresh private GUI per condition; same seed, surface move, archived wrong anchor, five receipts, Luna-low and authority checks; schema gate before first GUI",
        "positive_gate": "TARGET_REFERENCE_ONLY, exact rehover, one released target button and shifted finance oracle success",
        "negative_gate": "NO_TARGET_AUTHORITY with no receipt/point, zero target button, independent task false and diagnostic reported separately",
        "failure_policy": "retain first ordered pair and all completed evidence; no model, GUI, condition or task retry",
        "fault_injection": {"source": ARCHIVED_WRONG.relative_to(HERE).as_posix(),
            "source_sha256": prior.sha(ARCHIVED_WRONG), "archived_wrong_point": [436, 51]},
        "baseline_report": BASELINE.relative_to(HERE).as_posix(), "baseline_sha256": prior.sha(BASELINE),
        "sources": {**{name: prior.sha(HERE / name) for name in dict.fromkeys(SOURCES)},
            **{name: prior.sha(HERE.parent / name) for name in prior.TASK_SOURCES}},
        "schema_cache_sources": {source.relative_to(HERE).as_posix(): prior.sha(source) for source in CACHE_SOURCES},
        "schema_cache": {(cache / source.name).name: prior.sha(cache / source.name) for source in CACHE_SOURCES},
        "scope": "one fixed-seed positive/no-match OpenTTD pair with deterministic wrong-anchor injection; no natural error rate, causal speedup, token saving, broad reliability or human-tempo claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__": main()
