"""Independent local CPU recheck of immutable #5315 raw/receipt; streaming only."""
import hashlib
import json
import math
import urllib.request
from collections import defaultdict


BASE = "https://raw.githubusercontent.com/Unjuno/agent-interface/e30ed8d5cf4b3e4846f6f8afc3c5b59e57d3dbc3/research/analysis/conformal_verifier_risk_contract_5315_v1/results/formal-01/"
RAW_URL = BASE + "raw.jsonl"
RECEIPT_URL = BASE + "receipt.json"
RAW_SHA = "4ead9d0a552db86332a4c8ac08b9f6e01fcc1f6066e645ae15ead9c9395c8b37"
RECEIPT_SHA = "6401627c5777b6ee42a5ce7fd26457d2355854fc53095be4cd35d4750ce6a55a"
ALPHA = 0.10
TRIALS = 10_000
NS = (4, 10)
TOL = 0.015


def order_cut(scores, rank):
    return None if rank > len(scores) else sorted(scores)[rank - 1]


def close_number(got, expected):
    if expected is None:
        return got is None
    return (isinstance(got, (int, float)) and not isinstance(got, bool)
            and math.isclose(got, expected, rel_tol=0.0, abs_tol=1e-14))


def outcome(cut, true_score, false_score, shift_override=False):
    if shift_override or cut is None:
        labels = {"PASS", "FAIL"}
    else:
        labels = set()
        if true_score <= cut:
            labels.add("PASS")
        if false_score <= cut:
            labels.add("FAIL")
    singleton = len(labels) == 1
    return {
        "true_included": "PASS" in labels,
        "singleton": singleton,
        "wrong_singleton": singleton and "PASS" not in labels,
        "set_size": len(labels),
        "empty": len(labels) == 0,
    }


def row_errors(row):
    errors = []
    n = row.get("n")
    if type(n) is not int or n not in NS or type(row.get("trial")) is not int:
        return ["identity"]
    expected_keys = {"n", "trial", "calibration_u", "id_u", "id_false_u",
                     "shift_u", "shift_false_u", "ranks", "thresholds", "outcomes"}
    if set(row) != expected_keys:
        errors.append("keys")
    cal_u = row.get("calibration_u")
    if not isinstance(cal_u, list) or len(cal_u) != n or any(
            type(x) not in (int, float) or not 0 <= x < 1 for x in cal_u):
        return errors + ["calibration_values"]
    ranks = {"plugin": math.ceil(n * (1 - ALPHA)),
             "conformal": math.ceil((n + 1) * (1 - ALPHA))}
    if row.get("ranks") != ranks:
        errors.append("ranks")
    cal = [math.sqrt(x) for x in cal_u]
    cuts = {"raw": 0.90,
            "plugin": order_cut(cal, ranks["plugin"]),
            "conformal": order_cut(cal, ranks["conformal"])}
    got_cuts = row.get("thresholds", {})
    if set(got_cuts) != set(cuts) or any(not close_number(got_cuts.get(k), v) for k, v in cuts.items()):
        errors.append("cutoffs")
    us = [row.get(k) for k in ("id_u", "id_false_u", "shift_u", "shift_false_u")]
    if any(type(u) not in (int, float) or not 0 <= u < 1 for u in us):
        return errors + ["test_uniforms"]
    id_true, id_false, shift_true, shift_false = us
    tests = {
        "id": (math.sqrt(id_true), math.sqrt(id_false)),
        "shift": (shift_true ** 0.25, shift_false ** 0.25),
    }
    expected_outcomes = {}
    for condition, (true_score, false_score) in tests.items():
        expected_outcomes[condition] = {
            policy: outcome(cut, true_score, false_score)
            for policy, cut in cuts.items()
        }
        if condition == "shift":
            expected_outcomes[condition]["known_shift_contract"] = outcome(
                cuts["conformal"], true_score, false_score, shift_override=True)
    if row.get("outcomes") != expected_outcomes:
        errors.append("decisions")
    return errors


def main():
    raw_hash = hashlib.sha256()
    counts = defaultdict(lambda: defaultdict(float))
    seen = {n: 0 for n in NS}
    first = None
    row_errors_total = 0
    first_errors = []
    with urllib.request.urlopen(RAW_URL, timeout=120) as response:
        for index, line in enumerate(response):
            raw_hash.update(line)
            row = json.loads(line)
            if first is None:
                first = row
            errs = row_errors(row)
            if errs and len(first_errors) < 20:
                first_errors.extend(f"row{index}:{e}" for e in errs)
            row_errors_total += len(errs)
            n = row.get("n")
            if n in seen:
                if row.get("trial") != seen[n]:
                    row_errors_total += 1
                    first_errors.append(f"row{index}:trial_order")
                seen[n] += 1
            for condition, policies in row.get("outcomes", {}).items():
                for policy, fields in policies.items():
                    acc = counts[f"n{n}/{condition}/{policy}"]
                    for key in ("true_included", "singleton", "wrong_singleton", "set_size", "empty"):
                        value = fields.get(key)
                        if key in ("true_included", "singleton", "wrong_singleton", "empty") and type(value) is not bool:
                            row_errors_total += 1
                            first_errors.append(f"row{index}:type_{key}")
                        elif key == "set_size" and type(value) is not int:
                            row_errors_total += 1
                            first_errors.append(f"row{index}:type_set_size")
                        acc[key] += int(value) if type(value) is bool else value
    raw_actual = raw_hash.hexdigest()
    if raw_actual != RAW_SHA:
        first_errors.append("raw_sha256")
    if seen != {n: TRIALS for n in NS}:
        first_errors.append("denominators")
    summary = {}
    for key, values in sorted(counts.items()):
        summary[key] = {
            "trials": TRIALS,
            "true_inclusion_rate": values["true_included"] / TRIALS,
            "singleton_rate": values["singleton"] / TRIALS,
            "wrong_singleton_rate": values["wrong_singleton"] / TRIALS,
            "mean_set_size": values["set_size"] / TRIALS,
            "empty_rate": values["empty"] / TRIALS,
        }
    with urllib.request.urlopen(RECEIPT_URL, timeout=30) as response:
        receipt_bytes = response.read()
    receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
    receipt = json.loads(receipt_bytes)
    if receipt_sha != RECEIPT_SHA:
        first_errors.append("receipt_sha256")
    if receipt.get("rows") != sum(seen.values()) or receipt.get("summary") != summary:
        first_errors.append("receipt_reconstruction")
    if (receipt.get("allocation"), receipt.get("seed"), receipt.get("alpha"),
            receipt.get("sample_sizes"), receipt.get("trials_per_sample_size")) != (
            "conformal-risk-5315-v01-20260930-01", 5315, ALPHA, list(NS), TRIALS):
        first_errors.append("receipt_contract")

    theoretical = {}
    for n in NS:
        for policy, rank in (("plugin", math.ceil(n * (1 - ALPHA))),
                             ("conformal", math.ceil((n + 1) * (1 - ALPHA)))):
            for condition in ("id", "shift"):
                if policy == "conformal" and rank > n:
                    expected = 1.0
                elif condition == "id":
                    expected = rank / (n + 1)
                else:
                    expected = rank * (rank + 1) / ((n + 1) * (n + 2))
                key = f"n{n}/{condition}/{policy}"
                theoretical[key] = expected
                observed = summary.get(key, {}).get("true_inclusion_rate", -1)
                if abs(observed - expected) > TOL:
                    first_errors.append("finite_sample_oracle:" + key)
        for condition, expected in (("id", 0.90 ** 2), ("shift", 0.90 ** 4)):
            key = f"n{n}/{condition}/raw"
            observed = summary.get(key, {}).get("true_inclusion_rate", -1)
            if abs(observed - expected) > TOL:
                first_errors.append("raw_threshold_oracle:" + key)
    if summary.get("n4/id/conformal", {}).get("singleton_rate") != 0:
        first_errors.append("n4_singleton")
    if summary.get("n4/id/conformal", {}).get("mean_set_size") != 2:
        first_errors.append("n4_full_set")
    if any(summary.get(f"n{n}/shift/known_shift_contract", {}).get("singleton_rate") != 0 for n in NS):
        first_errors.append("shift_override_singletons")

    mutations = {}
    for name, mutate in (
        ("outcome_flip", lambda x: x["outcomes"]["id"]["raw"].__setitem__(
            "singleton", not x["outcomes"]["id"]["raw"]["singleton"])),
        ("cutoff_change", lambda x: x["thresholds"].__setitem__("raw", 0.91)),
        ("calibration_corruption", lambda x: x["calibration_u"].__setitem__(0, 1.5)),
    ):
        changed = json.loads(json.dumps(first))
        mutate(changed)
        mutations[name] = bool(row_errors(changed))
    if not all(mutations.values()):
        first_errors.append("ineffective_mutation_control")
    print(json.dumps({
        "status": "PASS_INDEPENDENT_RAW_RECHECK" if not first_errors and row_errors_total == 0 else "FAIL_AUDIT",
        "raw_sha256": raw_actual,
        "receipt_sha256": receipt_sha,
        "rows": sum(seen.values()),
        "rows_per_n": seen,
        "row_errors": row_errors_total,
        "first_errors": first_errors[:20],
        "summary": summary,
        "theoretical_inclusion": theoretical,
        "mutations_rejected": mutations,
        "scope": "synthetic finite-sample unit only; no real verifier or shift detector",
    }, sort_keys=True))
    raise SystemExit(0 if not first_errors and row_errors_total == 0 else 1)


if __name__ == "__main__":
    main()

