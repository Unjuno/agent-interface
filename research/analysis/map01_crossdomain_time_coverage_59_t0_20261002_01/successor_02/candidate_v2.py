"""T0-02 wrapper around the frozen T0-01 classifier; no source trace is changed."""
from pathlib import Path
import sys
import json

PARENT = Path(__file__).resolve().parent.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))


def normalize_openttd_observer_counts(summary, raw_record_count, transition_witness_count):
    """Keep raw observer-record count distinct from transition witness count."""
    fixed = dict(summary)
    fixed["observer_records"] = raw_record_count
    fixed["observer_record_count"] = raw_record_count
    fixed["observer_transition_witness_count"] = transition_witness_count
    return fixed


def analyze_sources(sources):
    from candidate import classify_cross_domain, parse_ait_records, parse_jsonl

    analysis = json.loads(sources["doom-analysis.json"])
    observer = parse_ait_records(sources["openttd-observer.txt"])
    openttd_audit = json.loads(sources["openttd-audit.json"])
    result = classify_cross_domain(
        parse_jsonl(sources["doom-v38-events.jsonl"]),
        parse_jsonl(sources["doom-v39-events.jsonl"]),
        analysis,
        parse_jsonl(sources["openttd-events.jsonl"]),
        observer,
    )
    openttd = next(row for row in result["domains"] if row["domain"] == "openttd")
    witness_count = len(openttd["observer_transition_indices"])
    result["domains"][result["domains"].index(openttd)] = normalize_openttd_observer_counts(
        openttd, raw_record_count=len(observer), transition_witness_count=witness_count)
    outcome = openttd_audit["continuous_independent_observer_outcome"]
    result["openttd_task_outcome"] = {
        "status": outcome["status"], "records": outcome["records"],
        "unique_states": outcome["unique_states"],
        "transition_indices": outcome["transition_indices"],
        "hard_success": openttd_audit["hard_success"],
        "formal_finish_outcome": openttd_audit["formal_finish_outcome"],
    }
    return result
