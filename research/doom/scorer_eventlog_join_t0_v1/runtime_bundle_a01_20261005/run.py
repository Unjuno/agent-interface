"""Run the frozen synthetic same-directory MAP01 bundle cases."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from runtime_bundle import classify_run

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT.parent / "file_join_fixtures" / "valid"


def _write_bundle(runtime, *, source_change=None, summary_change=None):
    runtime.mkdir(parents=True)
    shutil.copyfile(FIXTURE / "events.jsonl", runtime / "events.jsonl")
    shutil.copyfile(FIXTURE / "scorer-samples.jsonl", runtime / "scorer-samples.jsonl")
    policy = json.loads((ROOT / "SOURCE_POLICY.json").read_text(encoding="utf-8"))
    sources = dict(policy["sources"])
    if source_change == "hash":
        first = next(iter(sources))
        sources[first] = "0" * 64
    elif source_change == "extra":
        sources["doom/unexpected.py"] = "f" * 64
    (runtime / "sources.json").write_text(json.dumps(sources, sort_keys=True) + "\n", encoding="utf-8")
    sample_count = sum(1 for row in (runtime / "scorer-samples.jsonl").read_text().splitlines() if row.strip())
    summary = {"schema": "map01-independent-scorer-integration-v3",
               "controller_visible": False, "sample_count": sample_count, "event_count": 0}
    if summary_change:
        summary.update(summary_change)
    (runtime / "scorer-summary.json").write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")


def run():
    cases = [
        ("valid", {}, "ADMISSION_BRACKETED_PROGRESS", "bounded_independent_progress_observed_after_first_input"),
        ("source_hash_changed", {"source_change": "hash"}, "POST_CANCELLATION_COOCCURRENCE", "source_manifest_mismatch"),
        ("source_entry_unexpected", {"source_change": "extra"}, "POST_CANCELLATION_COOCCURRENCE", "source_manifest_mismatch"),
        ("summary_count_changed", {"summary_change": {"sample_count": 99}}, "POST_CANCELLATION_COOCCURRENCE", "scorer_summary_sample_count_mismatch"),
        ("summary_schema_changed", {"summary_change": {"schema": "unknown"}}, "POST_CANCELLATION_COOCCURRENCE", "invalid_scorer_summary"),
        ("controller_visible", {"summary_change": {"controller_visible": True}}, "POST_CANCELLATION_COOCCURRENCE", "invalid_scorer_summary"),
        ("summary_missing", {"summary_missing": True}, "POST_CANCELLATION_COOCCURRENCE", "invalid_or_missing_runtime_metadata"),
    ]
    rows = []
    with tempfile.TemporaryDirectory() as temp:
        for case_id, mutations, decision, reason in cases:
            runtime = Path(temp) / case_id
            _write_bundle(runtime, **{k: v for k, v in mutations.items() if k != "summary_missing"})
            if mutations.get("summary_missing"):
                (runtime / "scorer-summary.json").unlink()
            observed = classify_run(runtime, "recover-1", max_gap_ns=100,
                                    source_policy=ROOT / "SOURCE_POLICY.json", freeze=ROOT / "FREEZE.json")
            rows.append({"id": case_id, "expected_decision": decision, "expected_reason": reason,
                         "observed": observed})
    return {"schema": "scorer-run-bundle-raw-v1", "experiment_id": "scorer-run-bundle-provenance-a01-20261005",
            "base_main": "31ce02c0a148aed9650b58ef31a8746d5e85e091",
            "live_game_model_or_input_launched": False,
            "input_provenance": "source policy copied from current-main retained sources.json; event and scorer files are synthetic fixtures",
            "cases": rows}


if __name__ == "__main__":
    result = run()
    path = ROOT / "RAW.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
