#!/usr/bin/env python3
"""Post-freeze integrity mutations; never invokes candidate or formal auditor."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    frozen = json.loads((ROOT / "inputs.json").read_text())
    raw = json.loads((ROOT / "RAW_RESULT.json").read_text())
    baseline_input_hash = digest(frozen)
    baseline_result_hash = hashlib.sha256((ROOT / "RAW_RESULT.json").read_bytes()).hexdigest()
    mutations = {}

    x = copy.deepcopy(frozen)
    primary = next(t for t in x["traces"] if t["id"] == "memory_burst_primary")
    primary["memory_some_ms_in_1s"][2], primary["memory_some_ms_in_1s"][7] = primary["memory_some_ms_in_1s"][7], primary["memory_some_ms_in_1s"][2]
    mutations["signal_order"] = digest(x) != baseline_input_hash

    x = copy.deepcopy(frozen)
    next(t for t in x["traces"] if t["id"] == "memory_burst_primary")["memory_some_ms_in_1s"][2] += 1
    mutations["event_intensity"] = digest(x) != baseline_input_hash

    x = copy.deepcopy(raw)
    a = next(r for r in x["rows"] if r["trace"] == "memory_burst_primary" and r["policy"] == "fixed_concurrency")
    b = next(r for r in x["rows"] if r["trace"] == "memory_burst_primary" and r["policy"] == "psi_memory")
    a["policy"], b["policy"] = b["policy"], a["policy"]
    mutations["label_swap"] = hashlib.sha256((json.dumps(x, indent=2, sort_keys=True)+"\n").encode()).hexdigest() != baseline_result_hash

    x = copy.deepcopy(raw)
    x["rows"] = [r for r in x["rows"] if r["trace"] == "memory_burst_primary"]
    mutations["pooled_trace_omission"] = hashlib.sha256((json.dumps(x, indent=2, sort_keys=True)+"\n").encode()).hexdigest() != baseline_result_hash

    result = {"baseline_input_sha256": baseline_input_hash, "baseline_raw_result_sha256": baseline_result_hash,
              "mutations_rejected": sum(mutations.values()), "mutations_tested": len(mutations), "gates": mutations}
    (ROOT / "MUTATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, sort_keys=True))
    if not all(mutations.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
