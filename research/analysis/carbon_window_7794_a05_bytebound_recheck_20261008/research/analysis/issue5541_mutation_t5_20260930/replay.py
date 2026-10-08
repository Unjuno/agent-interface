"""Replay the captured T5 Docker JSON without rerunning the experiment."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "docker-stdout.json"

def load_raw():
    data = json.loads(RAW.read_text(encoding="utf-8"))
    if data.get("schema") != "mutation-oracle-independence-t5-v1":
        raise ValueError("raw schema mismatch")
    if data.get("status") != "FAIL":
        raise ValueError("raw status mismatch")
    return data

def independent_reference(case):
    if case["lineage"] != "VALID":
        return "UNKNOWN"
    if case["epoch"] <= case["min_epoch"]:
        return "FAIL"
    if case["authority"] != "GRANTED":
        return "FAIL"
    return "PASS"

def mutant_outcome(case, operators):
    epoch_ok = case["epoch"] >= case["min_epoch"] if "epoch_nonstrict" in operators else case["epoch"] > case["min_epoch"]
    lineage_ok = case["lineage"] != "INVALID" if "lineage_inverted" in operators else case["lineage"] == "VALID"
    authority_ok = case["authority"] != "DENIED" if "authority_inverted" in operators else case["authority"] == "GRANTED"
    if not lineage_ok or not epoch_ok or not authority_ok:
        return "FAIL"
    return "PASS"

def replay(raw):
    cases = raw["cases"]
    mutants = raw["mutants"]
    for mutant in mutants:
        killed = [
            case["name"] for case in cases
            if mutant_outcome(case, mutant["operators"]) != independent_reference(case)
        ]
        if killed != mutant["killed"]:
            raise AssertionError(f"mutant discrepancy {mutant['operators']}: {killed}")
    singles = [m for m in mutants if len(m["operators"]) == 1]
    survivors = [m for m in mutants if not m["killed"]]
    semantic_payload = {k: v for k, v in raw.items() if k != "semantic_sha256"}
    digest = hashlib.sha256(json.dumps(semantic_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if digest != raw["semantic_sha256"]:
        raise AssertionError("semantic digest mismatch")
    return {
        "raw_status": raw["status"],
        "all_single_mutants_killed": all(m["killed"] for m in singles),
        "combination_count": sum(len(m["operators"]) > 1 for m in mutants),
        "survivor_count": len(survivors),
        "survivors": [m["operators"] for m in survivors],
        "raw_semantic_hash_recomputed": digest,
        "decision": "FAIL_PROBE_GATE_NO_COMBINATION_SURVIVOR" if not survivors else "SURVIVOR_PRESENT",
    }

if __name__ == "__main__":
    print(json.dumps(replay(load_raw()), sort_keys=True))
