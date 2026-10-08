from __future__ import annotations
from itertools import product
import json
from pathlib import Path

TARGETS = ("A", "B", "C")
LENGTHS = range(1, 8)
CACHE_SIZES = (1, 2, 3)
ROOT = Path(__file__).resolve().parent


def epochs_from_boundaries(n: int, boundaries: tuple[int, ...]) -> tuple[int, ...]:
    epoch = 0
    out = [epoch]
    for bit in boundaries:
        if bit:
            epoch += 1
        out.append(epoch)
    assert len(out) == n
    return tuple(out)


def lru_misses(targets: tuple[str, ...], epochs: tuple[int, ...], capacity: int):
    cache: list[tuple[str, int]] = []  # MRU at end
    misses = 0
    stale_hits = 0
    last_epoch = None
    for target, epoch in zip(targets, epochs):
        if epoch != last_epoch:
            cache.clear()
            last_epoch = epoch
        idx = next((i for i, item in enumerate(cache) if item[0] == target), None)
        if idx is None:
            misses += 1
            cache.append((target, epoch))
            if len(cache) > capacity:
                cache.pop(0)
        else:
            entry = cache.pop(idx)
            if entry[1] != epoch:
                stale_hits += 1
            cache.append(entry)
    return misses, stale_hits


def unbounded_misses(targets: tuple[str, ...], epochs: tuple[int, ...]):
    seen: set[str] = set()
    misses = 0
    stale_hits = 0
    last_epoch = None
    stored_epoch: dict[str, int] = {}
    for target, epoch in zip(targets, epochs):
        if epoch != last_epoch:
            seen.clear()
            stored_epoch.clear()
            last_epoch = epoch
        if target not in seen:
            misses += 1
            seen.add(target)
            stored_epoch[target] = epoch
        elif stored_epoch[target] != epoch:
            stale_hits += 1
    return misses, stale_hits


def closed_form(targets: tuple[str, ...], epochs: tuple[int, ...]):
    one = 0
    infinite = 0
    strict_predicate = False
    start = 0
    n = len(targets)
    for end in range(1, n + 1):
        if end == n or epochs[end] != epochs[end - 1]:
            seg = targets[start:end]
            if seg:
                one += 1 + sum(a != b for a, b in zip(seg, seg[1:]))
                infinite += len(set(seg))
                seen: set[str] = set()
                prev = None
                for t in seg:
                    if t in seen and prev is not None and t != prev:
                        strict_predicate = True
                    seen.add(t)
                    prev = t
            start = end
    return one, infinite, strict_predicate


def trace_metrics(targets, boundaries):
    epochs = epochs_from_boundaries(len(targets), boundaries)
    lru = {}
    stale = 0
    for k in CACHE_SIZES:
        m, s = lru_misses(targets, epochs, k)
        lru[str(k)] = m
        stale += s
    inf, s_inf = unbounded_misses(targets, epochs)
    stale += s_inf
    one_formula, inf_formula, strict_pred = closed_form(targets, epochs)
    return {
        "epochs": list(epochs),
        "lru": lru,
        "unbounded": inf,
        "one_formula": one_formula,
        "unbounded_formula": inf_formula,
        "strict_predicate": strict_pred,
        "saving_unbounded": lru["1"] - inf,
        "saving_k2": lru["1"] - lru["2"],
        "saving_k3": lru["1"] - lru["3"],
        "stale_hits": stale,
    }


def canonical(targets, boundaries):
    m = trace_metrics(tuple(targets), tuple(boundaries))
    return {"targets": list(targets), "boundaries": list(boundaries), **m}


def main():
    trace_count = 0
    access_count = 0
    formula_mismatches = 0
    strict_equivalence_mismatches = 0
    stale_cross_epoch_hits = 0
    unbounded_gt_one_violations = 0
    monotonicity_violations = 0
    k2_strict_gain_traces = 0
    k3_strict_gain_traces = 0
    unbounded_strict_gain_traces = 0
    total_one_misses = 0
    total_k2_misses = 0
    total_k3_misses = 0
    total_unbounded_misses = 0
    max_unbounded_saving = -1
    max_saving_witness = None
    by_length = {}

    for n in LENGTHS:
        count_n = 0
        boundary_space = product((0, 1), repeat=max(n - 1, 0))
        boundary_patterns = list(boundary_space)
        for targets in product(TARGETS, repeat=n):
            for boundaries in boundary_patterns:
                count_n += 1
                trace_count += 1
                access_count += n
                m = trace_metrics(targets, boundaries)
                m1 = m["lru"]["1"]
                m2 = m["lru"]["2"]
                m3 = m["lru"]["3"]
                mi = m["unbounded"]
                total_one_misses += m1
                total_k2_misses += m2
                total_k3_misses += m3
                total_unbounded_misses += mi
                if m1 != m["one_formula"] or mi != m["unbounded_formula"]:
                    formula_mismatches += 1
                if ((m1 - mi) > 0) != m["strict_predicate"]:
                    strict_equivalence_mismatches += 1
                stale_cross_epoch_hits += m["stale_hits"]
                if mi > m1:
                    unbounded_gt_one_violations += 1
                if not (m3 <= m2 <= m1):
                    monotonicity_violations += 1
                if m2 < m1:
                    k2_strict_gain_traces += 1
                if m3 < m1:
                    k3_strict_gain_traces += 1
                if mi < m1:
                    unbounded_strict_gain_traces += 1
                saving = m1 - mi
                if saving > max_unbounded_saving:
                    max_unbounded_saving = saving
                    max_saving_witness = {
                        "targets": list(targets),
                        "boundaries": list(boundaries),
                        "epochs": m["epochs"],
                        "one_misses": m1,
                        "unbounded_misses": mi,
                        "saving": saving,
                    }
        by_length[str(n)] = count_n

    examples = {
        "same_target": canonical(("A", "A", "A"), (0, 0)),
        "alternating_two": canonical(("A", "B", "A", "B"), (0, 0, 0)),
        "epoch_reset_before_revisit": canonical(("A", "B", "A"), (0, 1)),
        "capacity_two_thrash": canonical(("A", "B", "C", "A"), (0, 0, 0)),
        "all_new_epochs_same_identity": canonical(("A", "A", "A"), (1, 1)),
    }

    passed = all([
        formula_mismatches == 0,
        strict_equivalence_mismatches == 0,
        stale_cross_epoch_hits == 0,
        unbounded_gt_one_violations == 0,
        monotonicity_violations == 0,
        k2_strict_gain_traces > 0,
        examples["epoch_reset_before_revisit"]["saving_unbounded"] == 0,
        examples["all_new_epochs_same_identity"]["unbounded"] == 3,
    ])

    result = {
        "task": "MULTICURSOR-TARGET-HANDLE-REGROUNDING-R0-20260918-001",
        "formal_invocations": 1,
        "reruns": 0,
        "targets": list(TARGETS),
        "lengths": [min(LENGTHS), max(LENGTHS)],
        "cache_sizes": list(CACHE_SIZES),
        "trace_count": trace_count,
        "access_count": access_count,
        "by_length": by_length,
        "formula_mismatches": formula_mismatches,
        "strict_equivalence_mismatches": strict_equivalence_mismatches,
        "stale_cross_epoch_hits": stale_cross_epoch_hits,
        "unbounded_gt_one_violations": unbounded_gt_one_violations,
        "monotonicity_violations": monotonicity_violations,
        "k2_strict_gain_traces": k2_strict_gain_traces,
        "k3_strict_gain_traces": k3_strict_gain_traces,
        "unbounded_strict_gain_traces": unbounded_strict_gain_traces,
        "total_misses": {
            "k1": total_one_misses,
            "k2": total_k2_misses,
            "k3": total_k3_misses,
            "unbounded": total_unbounded_misses,
        },
        "max_unbounded_saving": max_unbounded_saving,
        "max_saving_witness": max_saving_witness,
        "examples": examples,
        "decision": "PASS_MULTITARGET_HANDLE_REGROUNDING_SCOPED" if passed else "FAIL_MULTITARGET_HANDLE_REGROUNDING_MODEL",
        "pass": passed,
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
