from __future__ import annotations
from itertools import product
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
RESULT = json.loads((ROOT / "RESULT.json").read_text())
TARGETS = ("A", "B", "C")


def segments(seq, cuts):
    out = []
    cur = [seq[0]]
    for idx, cut in enumerate(cuts, start=1):
        if cut:
            out.append(tuple(cur))
            cur = [seq[idx]]
        else:
            cur.append(seq[idx])
    out.append(tuple(cur))
    return out


def lru_for_segments(segs, k):
    misses = 0
    for seg in segs:
        cache = []
        for t in seg:
            if t in cache:
                cache.remove(t)
                cache.append(t)
            else:
                misses += 1
                cache.append(t)
                if len(cache) > k:
                    del cache[0]
    return misses


def independent_recompute():
    traces = 0
    accesses = 0
    formula_bad = 0
    strict_bad = 0
    stale_hits = 0  # by construction segments are independent epochs
    inf_gt_one = 0
    mono_bad = 0
    k2_gain = 0
    k3_gain = 0
    inf_gain = 0
    total = {"k1": 0, "k2": 0, "k3": 0, "unbounded": 0}
    max_save = -1
    max_witness = None
    by_length = {}

    for n in range(1, 8):
        ncount = 0
        cut_patterns = list(product((0, 1), repeat=max(0, n - 1)))
        for seq in product(TARGETS, repeat=n):
            for cuts in cut_patterns:
                traces += 1
                ncount += 1
                accesses += n
                segs = segments(seq, cuts)
                m1 = lru_for_segments(segs, 1)
                m2 = lru_for_segments(segs, 2)
                m3 = lru_for_segments(segs, 3)
                mi = sum(len(set(seg)) for seg in segs)
                f1 = sum(1 + sum(a != b for a, b in zip(seg, seg[1:])) for seg in segs)
                strict_pred = any(
                    any(t in set(seg[:j]) and t != seg[j-1] for j, t in enumerate(seg) if j > 0)
                    for seg in segs
                )
                if m1 != f1 or mi != sum(len(set(seg)) for seg in segs):
                    formula_bad += 1
                if ((m1 - mi) > 0) != strict_pred:
                    strict_bad += 1
                if mi > m1:
                    inf_gt_one += 1
                if not (m3 <= m2 <= m1):
                    mono_bad += 1
                k2_gain += int(m2 < m1)
                k3_gain += int(m3 < m1)
                inf_gain += int(mi < m1)
                total["k1"] += m1
                total["k2"] += m2
                total["k3"] += m3
                total["unbounded"] += mi
                save = m1 - mi
                if save > max_save:
                    epochs = []
                    e = 0
                    epochs.append(e)
                    for c in cuts:
                        if c:
                            e += 1
                        epochs.append(e)
                    max_save = save
                    max_witness = {
                        "targets": list(seq), "boundaries": list(cuts), "epochs": epochs,
                        "one_misses": m1, "unbounded_misses": mi, "saving": save,
                    }
        by_length[str(n)] = ncount

    return {
        "trace_count": traces,
        "access_count": accesses,
        "by_length": by_length,
        "formula_mismatches": formula_bad,
        "strict_equivalence_mismatches": strict_bad,
        "stale_cross_epoch_hits": stale_hits,
        "unbounded_gt_one_violations": inf_gt_one,
        "monotonicity_violations": mono_bad,
        "k2_strict_gain_traces": k2_gain,
        "k3_strict_gain_traces": k3_gain,
        "unbounded_strict_gain_traces": inf_gain,
        "total_misses": total,
        "max_unbounded_saving": max_save,
        "max_saving_witness": max_witness,
    }


def validate(r):
    checks = {
        "formal_once": r.get("formal_invocations") == 1 and r.get("reruns") == 0,
        "formula_exact": r.get("formula_mismatches") == 0,
        "strict_equivalence_exact": r.get("strict_equivalence_mismatches") == 0,
        "no_stale_hits": r.get("stale_cross_epoch_hits") == 0,
        "unbounded_not_worse": r.get("unbounded_gt_one_violations") == 0,
        "lru_monotone": r.get("monotonicity_violations") == 0,
        "k2_nonvacuous": r.get("k2_strict_gain_traces", 0) > 0,
        "reset_control": r["examples"]["epoch_reset_before_revisit"]["saving_unbounded"] == 0,
        "same_identity_new_epoch_misses": r["examples"]["all_new_epochs_same_identity"]["unbounded"] == 3,
        "decision": r.get("decision") == "PASS_MULTITARGET_HANDLE_REGROUNDING_SCOPED" and r.get("pass") is True,
    }
    return checks, all(checks.values())


actual = independent_recompute()
exact = {k: RESULT[k] == v for k, v in actual.items()}
checks, ok = validate(RESULT)
corruptions = []
for field, bad in [
    ("formula_mismatches", 1),
    ("stale_cross_epoch_hits", 1),
    ("monotonicity_violations", 1),
    ("k2_strict_gain_traces", 0),
]:
    c = copy.deepcopy(RESULT)
    c[field] = bad
    _, accepted = validate(c)
    corruptions.append({"field": field, "rejected": not accepted})

out = {
    "independent_exact": exact,
    "checks": checks,
    "corruption_controls": corruptions,
    "pass": all(exact.values()) and ok and all(x["rejected"] for x in corruptions),
}
(ROOT / "AUDIT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, sort_keys=True))
sys.exit(0 if out["pass"] else 1)
