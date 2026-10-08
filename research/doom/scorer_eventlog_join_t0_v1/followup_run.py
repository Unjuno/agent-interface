"""Execute the single frozen regression case against prior and successor policy."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH_DOOM = ROOT.parent
PRIOR_PATH = RESEARCH_DOOM / "scorer_admission_attribution_t0_v1" / "candidate.py"
CURRENT_PATH = ROOT / "candidate.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample(ns, kills):
    return {"sample_started_ns": ns - 1, "sample_finished_ns": ns + 1,
            "missed_periods_before": 0,
            "payload": {"schema": "independent-progress-sample-v2", "sample_ns": ns,
                        "kill_count": kills, "death_count": 0, "map_exit": False}}


def main():
    prior = load_module("merged_scorer_admission_t0_candidate", PRIOR_PATH)
    successor = load_module("scorer_eventlog_join_successor", CURRENT_PATH)
    sample_pairs = [(105, 0), (110, 0), (115, 1), (130, 1)]
    prior_result = prior.classify_progress(sample_pairs, 100, 120, max_gap_ns=100)
    events = [{"event": "accepted", "id": "recover-1", "accepted_ns": 100},
              {"event": "input_admission", "id": "recover-1", "admitted_ns": 120}]
    successor_result = successor.classify_intent(
        events, [sample(ns, kills) for ns, kills in sample_pairs],
        "recover-1", max_gap_ns=100)
    raw = {
        "schema": "scorer-eventlog-prior-policy-regression-raw-v1",
        "base_main": "b47d4d0b053f6e7d88c37e24be81777aa28feb6a",
        "prior_candidate_git_blob": "3a097172115b6d8c2cd482c37c80388b86404b25",
        "prior_candidate_sha256": hashlib.sha256(PRIOR_PATH.read_bytes()).hexdigest(),
        "successor_candidate_sha256": hashlib.sha256(CURRENT_PATH.read_bytes()).hexdigest(),
        "sample_history": sample_pairs,
        "prior_decision": prior_result["decision"],
        "prior_baseline_ns": prior_result.get("baseline_ns"),
        "pre_input_progress_observed_ns": 115,
        "first_input_ns": 120,
        "unchanged_post_input_sample_ns": 130,
        "successor_decision": successor_result["decision"],
        "successor_reason": successor_result.get("reason"),
        "causal_attribution": False,
        "candidate_started_in_container": False,
        "execution_scope": "local Python 3.12.13 on macOS arm64",
    }
    (ROOT / "followup_raw.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(raw, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
