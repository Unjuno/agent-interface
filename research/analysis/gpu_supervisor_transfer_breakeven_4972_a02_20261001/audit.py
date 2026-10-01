#!/usr/bin/env python3
"""Independent CPU-only raw audit; intentionally imports no CUDA/runtime code."""
import copy
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SIZES = (1, 4, 16, 64, 256, 1024)
REPEATS = 30
THRESHOLD = 700


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def oracle(row):
    hint = int(row["confidence_milli"] >= THRESHOLD)
    admitted = int(bool(hint) and row["observed_sequence"] == row["current_sequence"]
                   and row["ambiguous"] is False and row["forced_yield"] is False)
    return hint, admitted


def audit(result, doc, freeze):
    errors = []
    rows = doc.get("rows", [])
    if result.get("schema") != "gpu-supervisor-transfer-break-even-result-v1": errors.append("schema")
    if result.get("allocation") != freeze.get("allocation"): errors.append("allocation")
    if result.get("base_main_sha") != freeze.get("base_main_sha"): errors.append("base_main_sha")
    if result.get("dataset_sha256") != sha(ROOT / "dataset.json"): errors.append("dataset_sha256")
    source = result.get("source_sha256", {})
    if source.get("prepare") != freeze.get("prepare_sha256"): errors.append("prepare_sha256")
    if source.get("runner") != freeze.get("runner_sha256"): errors.append("runner_sha256")
    if result.get("row_count") != 1024 or len(rows) != 1024: errors.append("row_count")
    counts = {s: sum(r.get("stratum") == s for r in rows)
              for s in ("fresh_valid", "stale", "ambiguous", "forced_yield")}
    if counts != {s: 256 for s in counts}: errors.append("stratum_counts")
    if result.get("stratum_counts") != counts: errors.append("reported_stratum_counts")
    by_id = {r.get("id"): r for r in rows}
    if len(by_id) != 1024: errors.append("duplicate_dataset_id")

    timing = result.get("timing_ns", {})
    raw = result.get("raw_pairs", {})
    medians = result.get("p50_ns", {})
    for size in SIZES:
        key = str(size)
        pairs = raw.get(key, [])
        cpu_times = timing.get(key, {}).get("cpu_ns", [])
        cuda_times = timing.get(key, {}).get("cuda_end_to_end_ns", [])
        if len(pairs) != REPEATS or len(cpu_times) != REPEATS or len(cuda_times) != REPEATS:
            errors.append(f"sample_count:{size}")
            continue
        for rep, pair in enumerate(pairs):
            if pair.get("rep") != rep or pair.get("order") != (["cpu", "cuda"] if rep % 2 == 0 else ["cuda", "cpu"]):
                errors.append(f"pair_order:{size}:{rep}")
            for route in ("cpu", "cuda"):
                hs, ads = pair.get(route + "_hint", []), pair.get(route + "_admitted", [])
                if len(hs) != size or len(ads) != size: errors.append(f"pair_rows:{size}:{rep}:{route}")
                for j, (hint, admitted) in enumerate(zip(hs, ads)):
                    row = rows[j]
                    oh, oa = oracle(row)
                    if hint != oh: errors.append(f"hint:{size}:{rep}:{route}:{j}")
                    if admitted != oa: errors.append(f"admission:{size}:{rep}:{route}:{j}")
                    if row["stratum"] != "fresh_valid" and admitted != 0:
                        errors.append(f"unsafe_admission:{size}:{rep}:{route}:{j}")
            if pair.get("cpu_hint") != pair.get("cuda_hint"): errors.append(f"parity_hint:{size}:{rep}")
            if pair.get("cpu_admitted") != pair.get("cuda_admitted"):
                errors.append(f"parity_admission:{size}:{rep}")
        if any(type(v) is not int or v <= 0 for v in cpu_times + cuda_times): errors.append(f"invalid_timing:{size}")
        expected = {"cpu": statistics.median(cpu_times),
                    "cuda_end_to_end": statistics.median(cuda_times)}
        if medians.get(key) != expected: errors.append(f"median:{size}")
    return sorted(set(errors))


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    if sha(Path(__file__)) != freeze.get("audit_sha256"):
        raise SystemExit("STOP: auditor hash mismatch")
    result = json.loads((ROOT / "candidate_result.json").read_text(encoding="utf-8"))
    doc = json.loads((ROOT / "dataset.json").read_text(encoding="utf-8"))
    errors = audit(result, doc, freeze)
    controls = {}
    mutations = {
        "flip_cuda_hint": lambda r: r["raw_pairs"]["1"][0]["cuda_hint"].__setitem__(0, 1 - r["raw_pairs"]["1"][0]["cuda_hint"][0]),
        "drop_timing_sample": lambda r: r["timing_ns"]["4"]["cuda_end_to_end_ns"].pop(),
        "wrong_source_hash": lambda r: r["source_sha256"].__setitem__("runner", "0" * 64),
        "duplicate_pair": lambda r: r["raw_pairs"]["16"].__setitem__(1, copy.deepcopy(r["raw_pairs"]["16"][0])),
        "unsafe_admission": lambda r: r["raw_pairs"]["64"][0]["cuda_admitted"].__setitem__(0, 1),
    }
    for name, mutate in mutations.items():
        corrupted = copy.deepcopy(result)
        mutate(corrupted)
        controls[name] = bool(audit(corrupted, doc, freeze))
    status = "PASS_CPU_AUDIT_SCOPED" if not errors and all(controls.values()) else "HOLD_INTEGRITY"
    receipt = {"schema": "gpu-supervisor-transfer-break-even-audit-v1",
               "allocation": freeze["allocation"], "candidate_sha256": sha(ROOT / "candidate_result.json"),
               "dataset_sha256": sha(ROOT / "dataset.json"), "errors": errors,
               "corruption_controls_rejected": controls, "disposition": status}
    out = ROOT / "audit_result.json"
    if out.exists():
        raise SystemExit("STOP: audit output already exists")
    out.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"errors": len(errors), "corruption_controls": controls,
                      "disposition": status}, sort_keys=True))
    if status != "PASS_CPU_AUDIT_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

