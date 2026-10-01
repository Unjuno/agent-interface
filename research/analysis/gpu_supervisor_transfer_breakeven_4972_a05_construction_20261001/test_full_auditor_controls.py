"""Construction-only test of the corrected full raw auditor and all frozen controls."""
import copy
import json
import statistics
import tempfile
from pathlib import Path

import audit


def synthetic_fixture():
    rows = []
    strata = ("fresh_valid", "stale", "ambiguous", "forced_yield")
    for stratum in strata:
        for i in range(256):
            valid = stratum == "fresh_valid"
            rows.append({
                "id": f"{stratum}-{i:04d}",
                "stratum": stratum,
                "confidence_milli": 866 if valid else 500,
                "observed_sequence": 1,
                "current_sequence": 1 if valid else 2,
                "ambiguous": stratum == "ambiguous",
                "forced_yield": stratum == "forced_yield",
            })
    doc = {"rows": rows}
    freeze = {
        "allocation": "construction-only",
        "base_main_sha": "a" * 40,
        "prepare_sha256": "b" * 64,
        "runner_sha256": "c" * 64,
    }
    result = {
        "schema": "gpu-supervisor-transfer-break-even-result-v1",
        "allocation": freeze["allocation"],
        "base_main_sha": freeze["base_main_sha"],
        "source_sha256": {
            "prepare": freeze["prepare_sha256"],
            "runner": freeze["runner_sha256"],
        },
        "row_count": 1024,
        "stratum_counts": {s: 256 for s in strata},
        "raw_pairs": {},
        "timing_ns": {},
        "p50_ns": {},
    }
    for size in audit.SIZES:
        key = str(size)
        pairs = []
        cpu_times = [100 + rep for rep in range(audit.REPEATS)]
        cuda_times = [200 + rep for rep in range(audit.REPEATS)]
        for rep in range(audit.REPEATS):
            route_data = {
                route: [audit.oracle(row) for row in rows[:size]]
                for route in ("cpu", "cuda")
            }
            pair = {
                "rep": rep,
                "order": ["cpu", "cuda"] if rep % 2 == 0 else ["cuda", "cpu"],
            }
            for route in ("cpu", "cuda"):
                pair[route + "_hint"] = [v[0] for v in route_data[route]]
                pair[route + "_admitted"] = [v[1] for v in route_data[route]]
            pairs.append(pair)
        result["raw_pairs"][key] = pairs
        result["timing_ns"][key] = {
            "cpu_ns": cpu_times,
            "cuda_end_to_end_ns": cuda_times,
        }
        result["p50_ns"][key] = {
            "cpu": statistics.median(cpu_times),
            "cuda_end_to_end": statistics.median(cuda_times),
        }
    return result, doc, freeze


def run():
    with tempfile.TemporaryDirectory() as td:
        audit.ROOT = Path(td)
        result, doc, freeze = synthetic_fixture()
        (audit.ROOT / "dataset.json").write_text(
            json.dumps(doc), encoding="utf-8"
        )
        result["dataset_sha256"] = audit.sha(audit.ROOT / "dataset.json")
        assert audit.audit(result, doc, freeze) == []

        mutations = {
            "flip_cuda_hint": lambda r: r["raw_pairs"]["1"][0]["cuda_hint"].__setitem__(
                0, 1 - r["raw_pairs"]["1"][0]["cuda_hint"][0]
            ),
            "drop_timing_sample": lambda r: r["timing_ns"]["4"][
                "cuda_end_to_end_ns"
            ].pop(),
            "wrong_source_hash": lambda r: r["source_sha256"].__setitem__(
                "runner", "0" * 64
            ),
            "duplicate_pair": lambda r: r["raw_pairs"]["16"].__setitem__(
                1, copy.deepcopy(r["raw_pairs"]["16"][0])
            ),
            "unsafe_admission": audit.inject_unsafe_admission,
        }
        rejected = {}
        for name, mutate in mutations.items():
            corrupted = copy.deepcopy(result)
            mutate(corrupted)
            rejected[name] = bool(audit.audit(corrupted, doc, freeze))
        assert all(rejected.values()), rejected
        print(
            "PASS synthetic raw-auditor baseline; all 5/5 corruption controls rejected: "
            + json.dumps(rejected, sort_keys=True)
        )


if __name__ == "__main__":
    run()
