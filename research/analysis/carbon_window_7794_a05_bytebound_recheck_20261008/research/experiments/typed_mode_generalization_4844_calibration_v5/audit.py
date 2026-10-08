#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #5198."""
import copy
import hashlib
import json
import math
import random
import sys
from pathlib import Path

ALLOC = "typed-mode-4844-risk-calibration-20260928-01"
SEEDS = {"train": 67010231, "calibration": 67010232, "test": 67010233}
TRAIN_SIZE = 2000
BLOCK_SIZE = 960
LABELS = (0, 0, 1, 2, 2)
PATTERNS = ((0,0,0,0,0,0),(1,1,1,1,1,1),(0,1,0,1,0,1),(1,0,1,0,1,0),(0,0,1,1,0,1))
BLOCK_ORDER = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")
PRIMARY_BLOCKS = ("SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT")
TARGET = 0.65


def draw(rng, mode, block):
    v = list(PATTERNS[mode])
    if block == "COMPOSITION_HOLDOUT":
        v[0], v[5] = 1 - v[0], 1 - v[5]
    elif block == "NUISANCE_SHIFT":
        v[3] = 1 - v[3]
    for k in range(6):
        if rng.random() < 0.08:
            v[k] = 1 - v[k]
    visible = [True] * 6
    if block in ("SINGLE_MISSING", "MULTI_MISSING"):
        visible[1] = False
    if block == "MULTI_MISSING":
        visible[4] = False
    if block != "COMPLETE":
        for k in range(6):
            if rng.random() < 0.20:
                visible[k] = False
    return tuple(v[k] if visible[k] else -1 for k in range(6))


def learn(vectors, classes, k):
    table = [{"n": 0, "one": [0] * 6, "seen": [0] * 6} for _ in range(k)]
    for x, y in zip(vectors, classes):
        t = table[y]
        t["n"] += 1
        for j, bit in enumerate(x):
            if bit >= 0:
                t["seen"][j] += 1
                t["one"][j] += bit
    return table


def probabilities(x, table):
    n_total = sum(c["n"] for c in table)
    logp = []
    for c in table:
        z = math.log((c["n"] + 1.0) / (n_total + len(table)))
        for j, bit in enumerate(x):
            if bit >= 0:
                p = (c["one"][j] + 1.0) / (c["seen"][j] + 2.0)
                z += math.log(p if bit == 1 else 1.0 - p)
        logp.append(z)
    ceiling = max(logp)
    masses = [math.exp(z - ceiling) for z in logp]
    norm = sum(masses)
    return [z / norm for z in masses]


def classify(x, direct_model, mode_model):
    pd = probabilities(x, direct_model)
    pm = probabilities(x, mode_model)
    d = min(range(3), key=lambda i: (-pd[i], i))
    grouped = [sum(pm[j] for j in range(5) if LABELS[j] == i) for i in range(3)]
    t = min(range(3), key=lambda i: (-grouped[i], i))
    return d, pd[d], t, grouped[t]


def threshold(conf, target=TARGET):
    vals = sorted(set(conf))
    vals += [math.nextafter(vals[-1], math.inf)]
    possibilities = []
    for cutoff in vals:
        ratio = sum(x >= cutoff for x in conf) / len(conf)
        possibilities.append((abs(ratio - target), -ratio, cutoff, ratio))
    best = min(possibilities)
    return best[2], best[3]


def dataset(seed, size, model_d, model_m, cutoffs):
    r = random.Random(seed)
    rows = []
    for block in BLOCK_ORDER:
        for row_no in range(size):
            mode = row_no % len(PATTERNS)
            x = draw(r, mode, block)
            truth = LABELS[mode]
            d, dc, t, tc = classify(x, model_d, model_m)
            de = d if dc >= cutoffs["direct"] else None
            te = t if tc >= cutoffs["typed"] else None
            rows.append({"block": block, "mode": mode, "truth": truth, "x": x,
                         "direct_class": d, "direct_confidence": dc,
                         "typed_class": t, "typed_confidence": tc,
                         "direct_emit": de, "typed_emit": te,
                         "direct_wrong": de is not None and de != truth,
                         "typed_wrong": te is not None and te != truth,
                         "direct_covered": de is not None, "typed_covered": te is not None})
    return rows


def metric_table(rows):
    table = {}
    for name in BLOCK_ORDER:
        chosen = [r for r in rows if r["block"] == name]
        total = len(chosen)
        table[name] = {"n": total,
                       "direct_wrong": sum(r["direct_wrong"] for r in chosen),
                       "typed_wrong": sum(r["typed_wrong"] for r in chosen),
                       "direct_coverage": sum(r["direct_covered"] for r in chosen) / total,
                       "typed_coverage": sum(r["typed_covered"] for r in chosen) / total}
    return table


def guard_outputs(model_d, model_m, cutoffs):
    base = []
    for m, x in enumerate(PATTERNS):
        d, dc, t, tc = classify(x, model_d, model_m)
        base.append({"mode": m, "expected": LABELS[m],
                     "direct": d if dc >= cutoffs["direct"] else None,
                     "typed": t if tc >= cutoffs["typed"] else None})
    fail = []
    for label, x in (("unknown", (-1, -1, -1, -1, -1, -1)), ("contradictory", (0,0,0,1,0,1))):
        d, dc, t, tc = classify(x, model_d, model_m)
        fail.append({"kind": label, "direct": d if dc >= cutoffs["direct"] else None,
                     "typed": t if tc >= cutoffs["typed"] else None})
    return {"prototypes": base, "fail_closed": fail}


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def reconstruct(seeds=SEEDS, block_size=BLOCK_SIZE):
    trng = random.Random(seeds["train"])
    train = [{"mode": i % 5, "x": draw(trng, i % 5, "TRAIN")} for i in range(TRAIN_SIZE)]
    vectors = [z["x"] for z in train]
    modes = [z["mode"] for z in train]
    direct = learn(vectors, [LABELS[m] for m in modes], 3)
    typed = learn(vectors, modes, 5)
    no_cut = {"direct": 0.0, "typed": 0.0}
    cal = dataset(seeds["calibration"], block_size, direct, typed, no_cut)
    td, cd = threshold([r["direct_confidence"] for r in cal])
    tt, ct = threshold([r["typed_confidence"] for r in cal])
    cutoffs = {"direct": td, "typed": tt}
    cal_info = {"target_coverage": TARGET, "direct_threshold": td, "direct_coverage": cd,
                "typed_threshold": tt, "typed_coverage": ct, "n": len(cal)}
    test = dataset(seeds["test"], block_size, direct, typed, cutoffs)
    counts = [modes.count(m) for m in range(5)]
    return {"schema": "typed-mode-risk-calibration-v1",
            "allocation": ALLOC,
            "seeds": {"train": seeds["train"], "calibration": seeds["calibration"], "test": seeds["test"]},
            "config": {"train_n": TRAIN_SIZE, "per_block": block_size, "blocks": BLOCK_ORDER,
                       "modes": 5, "dispositions": LABELS, "prototypes": PATTERNS,
                       "flip_p": 0.08, "drop_p": 0.20, "alpha": 1.0,
                       "target_coverage": TARGET,
                       "threshold_rule": "nearest pooled coverage; tie higher coverage then lower threshold"},
            "train": {"n": len(train), "mode_counts": counts,
                      "rows_sha256": hashlib.sha256(encode(train)).hexdigest()},
            "calibration": {"summary": cal_info, "rows": cal},
            "test": {"summary": metric_table(test), "rows": test},
            "controls": guard_outputs(direct, typed, cutoffs)}


def gate(expected):
    cal = expected["calibration"]["summary"]
    metrics = expected["test"]["summary"]
    direct_all = [r for r in expected["test"]["rows"] if r["direct_covered"]]
    typed_all = [r for r in expected["test"]["rows"] if r["typed_covered"]]
    pooled_d = len(direct_all) / len(expected["test"]["rows"])
    pooled_t = len(typed_all) / len(expected["test"]["rows"])
    calib_ok = abs(cal["direct_coverage"] - TARGET) <= 0.02 and abs(cal["typed_coverage"] - TARGET) <= 0.02
    test_cov_ok = abs(pooled_d - pooled_t) <= 0.03 and all(
        abs(metrics[b]["direct_coverage"] - metrics[b]["typed_coverage"]) <= 0.05 for b in PRIMARY_BLOCKS)
    controls = expected["controls"]
    proto_ok = all(p["direct"] == p["expected"] and p["typed"] == p["expected"] for p in controls["prototypes"])
    abstain_ok = all(c["direct"] is None and c["typed"] is None for c in controls["fail_closed"])
    risk_ok = all(metrics[b]["direct_wrong"] > 0 and
                  metrics[b]["typed_wrong"] <= 0.75 * metrics[b]["direct_wrong"] and
                  metrics[b]["typed_wrong"] <= metrics[b]["direct_wrong"] for b in PRIMARY_BLOCKS)
    if not calib_ok or not test_cov_ok:
        disposition = "HOLD_CALIBRATION_COVERAGE_INSTABILITY"
    elif not proto_ok or not abstain_ok:
        disposition = "FAIL_CONTROL_OR_INTEGRITY"
    elif risk_ok:
        disposition = "PASS_TYPED_MODE_MATCHED_COVERAGE_SCOPED"
    else:
        disposition = "FAIL_TYPED_MODE_NO_SELECTIVE_RISK_ADVANTAGE"
    return {"disposition": disposition, "calibration_coverage_ok": calib_ok,
            "test_coverage_match_ok": test_cov_ok, "prototype_controls_ok": proto_ok,
            "fail_closed_controls_ok": abstain_ok, "primary_risk_gate_ok": risk_ok,
            "test_pooled_direct_coverage": pooled_d, "test_pooled_typed_coverage": pooled_t}


def changed_copy(reference, change):
    candidate = copy.deepcopy(reference)
    change(candidate)
    return candidate


def mutations(ref):
    return [
        lambda x: x.__setitem__("schema", "tampered"),
        lambda x: x.__setitem__("allocation", "other"),
        lambda x: x["seeds"].__setitem__("train", x["seeds"]["train"] + 1),
        lambda x: x["train"].__setitem__("rows_sha256", "0" * 64),
        lambda x: x["config"].__setitem__("target_coverage", 0.66),
        lambda x: x["calibration"]["summary"].__setitem__("direct_threshold", 0.0),
        lambda x: x["calibration"]["rows"][0].__setitem__("x", [1] * 6),
        lambda x: x["calibration"]["rows"][0].__setitem__("mode", (x["calibration"]["rows"][0]["mode"] + 1) % 5),
        lambda x: x["calibration"]["rows"][0].__setitem__("direct_confidence", 0.0),
        lambda x: x["calibration"]["rows"][0].__setitem__("typed_confidence", 0.0),
        lambda x: x["test"]["rows"][0].__setitem__("block", "SINGLE_MISSING"),
        lambda x: x["test"]["rows"][0].__setitem__("truth", 2),
        lambda x: x["test"]["rows"][0].__setitem__("direct_emit", None),
        lambda x: x["test"]["rows"][0].__setitem__("typed_wrong", not x["test"]["rows"][0]["typed_wrong"]),
        lambda x: x["test"]["summary"]["COMPLETE"].__setitem__("direct_wrong", 999),
        lambda x: x["controls"]["fail_closed"][0].__setitem__("direct", 0),
    ]


def audit_file(path, expected_sha):
    raw = Path(path).read_bytes()
    observed = json.loads(raw)
    errors = []
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        errors.append("raw_sha256_mismatch")
    if encode(observed) != raw:
        errors.append("noncanonical_json")
    if observed.get("seeds") != SEEDS or observed.get("config", {}).get("per_block") != BLOCK_SIZE:
        errors.append("formal_allocation_identity_mismatch")
    reference = reconstruct()
    if observed != reference:
        errors.append("independent_reconstruction_mismatch")
    rejected = sum(changed_copy(reference, edit) != reference for edit in mutations(reference))
    if rejected != 16:
        errors.append("corruption_controls_not_all_rejected")
    result = {"pass": not errors, "errors": errors, "rows": len(observed.get("test", {}).get("rows", [])),
              "calibration_rows": len(observed.get("calibration", {}).get("rows", [])),
              "corruption_controls": {"rejected": rejected, "total": 16},
              "decision": gate(reference) if not errors else None,
              "raw_sha256": hashlib.sha256(raw).hexdigest()}
    return result


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW_JSON EXPECTED_SHA256")
    result = audit_file(sys.argv[1], sys.argv[2])
    destination = Path("/audit")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "audit.json").write_bytes(encode(result))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
