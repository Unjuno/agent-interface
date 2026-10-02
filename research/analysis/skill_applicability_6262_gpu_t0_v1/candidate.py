"""Frozen CUDA candidate for Issue #6262's finite T0 method fixture."""
import hashlib
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import torch


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main():
    fixture_path = Path(__file__).with_name("FIXTURE.json")
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; frozen GPU candidate cannot run")
    device = torch.device("cuda:0")
    factors = list(fixture["factors"].items())
    names = [name for name, _ in factors]
    levels = [values for _, values in factors]
    combos = [dict(zip(names, values)) for values in itertools.product(*levels)]
    feasible = [row for row in combos if not (row["mode"] == "dialog" and row["target"] == "alternate")]
    trials = fixture["trials"]
    by_id = {row["id"]: row for row in trials}
    if len(by_id) != len(trials) or len(trials) != len(feasible):
        raise ValueError("fixture requires one uniquely named trial for each feasible cell")
    for row in feasible:
        matches = [t for t in trials if all(t[n] == row[n] for n in names)]
        if len(matches) != 1:
            raise ValueError(f"fixture trial denominator mismatch for {row}")

    # Outcomes are deliberately stricter than authority: a granted action with
    # no independently qualified route is UNKNOWN, never PASS.
    outcomes = []
    for trial in trials:
        if trial["effect"] == "FAIL":
            outcomes.append("FAIL")
        elif trial["effect"] != "PASS":
            outcomes.append("UNKNOWN")
        elif trial["route_qualified"] is not True:
            outcomes.append("UNKNOWN")
        else:
            outcomes.append("PASS")
    n = len(trials)
    masks = torch.arange(1 << n, dtype=torch.int64, device=device)
    bits = torch.arange(n, dtype=torch.int64, device=device)
    present = ((masks[:, None] >> bits[None, :]) & 1).bool()
    pass_vec = torch.tensor([x == "PASS" for x in outcomes], dtype=torch.bool, device=device)
    fail_vec = torch.tensor([x == "FAIL" for x in outcomes], dtype=torch.bool, device=device)
    unknown_vec = torch.tensor([x == "UNKNOWN" for x in outcomes], dtype=torch.bool, device=device)
    observed = present.sum(dim=1)
    passed = (present & pass_vec).sum(dim=1)
    flat = (observed > 0) & (passed.to(torch.float64) / observed.clamp_min(1) >= fixture["flat_success_threshold"])

    # Naive factorwise coverage only asks whether each level has any PASS.
    level_masks = []
    for name, values in factors:
        for value in values:
            level_masks.append(torch.tensor([t[name] == value for t in trials], dtype=torch.bool, device=device))
    factorwise = torch.ones((1 << n,), dtype=torch.bool, device=device)
    for level_mask in level_masks:
        factorwise &= (present & level_mask[None, :] & pass_vec[None, :]).any(dim=1)

    # Exact feasible pair projections. A projection is PASS only when it is
    # represented and every represented trial has a qualified PASS.
    pair_groups = []
    pair_labels = []
    for (left, _), (right, _) in itertools.combinations(factors, 2):
        keys = sorted({(row[left], row[right]) for row in feasible})
        for lv, rv in keys:
            group = torch.tensor([t[left] == lv and t[right] == rv for t in trials], dtype=torch.bool, device=device)
            pair_groups.append(group)
            pair_labels.append([left, lv, right, rv])
    group_present = torch.stack([(present & g[None, :]).any(dim=1) for g in pair_groups], dim=1)
    group_bad = torch.stack([(present & g[None, :] & (~pass_vec | fail_vec | unknown_vec)[None, :]).any(dim=1) for g in pair_groups], dim=1)
    wide = group_present.all(dim=1) & (~group_bad).all(dim=1)
    narrow_index = next(i for i, t in enumerate(trials) if t["id"] == fixture["narrow_claim_trial"])
    narrow = present[:, narrow_index] & pass_vec[narrow_index]

    torch.cuda.synchronize(device)
    started = time.perf_counter()
    # Force materialization/readback for every subset and every gate.
    subset_rows = []
    observed_cpu = observed.cpu().tolist()
    passed_cpu = passed.cpu().tolist()
    flat_cpu = flat.cpu().tolist()
    factor_cpu = factorwise.cpu().tolist()
    wide_cpu = wide.cpu().tolist()
    narrow_cpu = narrow.cpu().tolist()
    coverage_cpu = group_present.cpu().tolist()
    bad_cpu = group_bad.cpu().tolist()
    for mask in range(1 << n):
        missing = [pair_labels[j] for j, value in enumerate(coverage_cpu[mask]) if not value]
        nonpass = [pair_labels[j] for j, value in enumerate(bad_cpu[mask]) if value]
        subset_rows.append({
            "mask": mask,
            "observed": observed_cpu[mask],
            "passed": passed_cpu[mask],
            "flat_promotes": bool(flat_cpu[mask]),
            "factorwise_promotes": bool(factor_cpu[mask]),
            "wide_certificate_passes": bool(wide_cpu[mask]),
            "narrow_certificate_passes": bool(narrow_cpu[mask]),
            "missing_pair_projections": missing,
            "nonpass_pair_projections": nonpass,
        })
    torch.cuda.synchronize(device)
    elapsed = (time.perf_counter() - started) * 1000.0
    result = {
        "experiment_id": fixture["experiment_id"],
        "candidate_disposition": "METHOD_PASS_SCOPED" if len(subset_rows) == (1 << n) else "STOP_INCOMPLETE_ENUMERATION",
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "device": torch.cuda.get_device_name(device),
        "cuda_runtime": torch.version.cuda,
        "torch_version": torch.__version__,
        "python": platform.python_version(),
        "trial_count": n,
        "feasible_cell_count": len(feasible),
        "feasible_pair_projection_count": len(pair_groups),
        "enumerated_evidence_subsets": len(subset_rows),
        "gpu_readback_ms_not_a_performance_claim": round(elapsed, 6),
        "effective_trial_outcomes": dict(zip([t["id"] for t in trials], outcomes)),
        "all_subsets": subset_rows,
    }
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("CANDIDATE_RAW.json")
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "all_subsets"}, sort_keys=True))


if __name__ == "__main__":
    main()
