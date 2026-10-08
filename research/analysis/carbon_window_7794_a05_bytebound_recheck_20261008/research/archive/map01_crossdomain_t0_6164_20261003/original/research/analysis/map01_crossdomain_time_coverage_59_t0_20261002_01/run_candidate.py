import hashlib
import json
from pathlib import Path

from candidate import classify_cross_domain, parse_ait_records, parse_jsonl

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
FREEZE = HERE / "FREEZE.json"


def load_verified(freeze):
    loaded = {}
    for name, item in freeze["inputs"].items():
        data = (INPUTS / name).read_bytes()
        observed = hashlib.sha256(data).hexdigest()
        if observed != item["sha256"]:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}:{observed}")
        loaded[name] = data.decode("utf-8")
    return loaded


def run():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    sources = load_verified(freeze)
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
    outcome = openttd_audit["continuous_independent_observer_outcome"]
    result["openttd_task_outcome"] = {
        "status": outcome["status"],
        "records": outcome["records"],
        "unique_states": outcome["unique_states"],
        "transition_indices": outcome["transition_indices"],
        "hard_success": openttd_audit["hard_success"],
        "formal_finish_outcome": openttd_audit["formal_finish_outcome"],
    }
    result["allocation_id"] = freeze["allocation_id"]
    result["source_main_sha"] = freeze["source_main_sha"]
    result["source_sha256"] = {
        name: item["sha256"] for name, item in freeze["inputs"].items()
    }
    result["candidate_invocations"] = 1
    result["retries"] = 0
    (HERE / "candidate_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    run()
