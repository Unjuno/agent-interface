#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #8638 split-control T0."""
import hashlib
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

SCALE = 1000
MASS_DEN = SCALE**4


def rat(text):
    return Fraction(text)


def fmt(value):
    return f"{value.numerator}/{value.denominator}"


def binary_entropy(value):
    if value == 0 or value == 1:
        return 0.0
    return -value*math.log2(value)-(1-value)*math.log2(1-value)


def canonical_hash(data):
    return hashlib.sha256((json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()).hexdigest()


def verify(config, raw):
    errors = []
    if raw.get("allocation") != config.get("allocation"):
        errors.append("allocation mismatch")
    input_hash = hashlib.sha256((Path(__file__).with_name("inputs.json")).read_bytes()).hexdigest()
    if raw.get("input_sha256") != input_hash:
        errors.append("input hash mismatch")
    if raw.get("weight_denominator") != MASS_DEN:
        errors.append("weight denominator mismatch")
    records = raw.get("cases")
    if not isinstance(records, list) or len(records) != len(config["cases"]):
        return errors + ["case frame incomplete"]
    by_id = {x.get("case_id"): x for x in records if isinstance(x, dict)}
    if len(by_id) != len(records):
        errors.append("duplicate or malformed case identity")
    summaries = {}
    for c in config["cases"]:
        r = by_id.get(c["id"])
        if r is None:
            errors.append(f"missing {c['id']}")
            continue
        if r.get("authority") != "NONE" or r.get("mandatory_gates_unchanged") is not True:
            errors.append(f"hard-gate invariant changed: {c['id']}")
        if c["support"] != "known":
            if r.get("disposition") != "UNKNOWN_SUPPORT" or r.get("base_loss") is not None or r.get("split_net_value") is not None or r.get("rows") != []:
                errors.append(f"unknown-support case was scored: {c['id']}")
            continue

        p1 = c["prior_state1"]
        prior = [SCALE-p1, p1]
        q = c["accuracy"]
        like = [[q, SCALE-q], [SCALE-q, q]]
        loss = c["loss"]
        base_act = min(range(2), key=lambda a: sum(prior[s]*loss[s][a] for s in (0, 1)))
        base = Fraction(sum(prior[s]*loss[s][base_act] for s in (0, 1)), SCALE)
        optimal = []
        for y in (0, 1):
            scores = [sum(prior[s]*like[s][y]*loss[s][a] for s in (0, 1)) for a in (0, 1)]
            optimal.append(0 if scores[0] <= scores[1] else 1)
        oracle = Fraction(sum(prior[s]*like[s][y]*loss[s][optimal[y]] for s in (0, 1) for y in (0, 1)), SCALE**2)
        cost = Fraction(c["cost_milli"], SCALE)
        expected_voi = base-oracle-cost

        rows = r.get("rows")
        if not isinstance(rows, list) or len(rows) != 16:
            errors.append(f"row count mismatch: {c['id']}")
            continue
        mass_by_key = Counter()
        for row in rows:
            if row.get("case_id") != c["id"]:
                errors.append(f"row identity mismatch: {c['id']}")
                continue
            s, y, delivered, consumed = (row.get(k) for k in ("state", "latent_signal", "delivered", "consumed"))
            if any(v not in (0, 1) for v in (s, y, delivered, consumed)):
                errors.append(f"invalid row key: {c['id']}")
                continue
            pd = c["delivery"] if delivered else SCALE-c["delivery"]
            pu = ((c["uptake"] if consumed else SCALE-c["uptake"]) if delivered else (0 if consumed else SCALE))
            expected_mass = prior[s]*like[s][y]*pd*pu
            mass_by_key[(s, y, delivered, consumed)] += row.get("weight_num", -1)
            if row.get("weight_num") != expected_mass or row.get("weight_den") != MASS_DEN:
                errors.append(f"probability mass mismatch: {c['id']}:{s}{y}{delivered}{consumed}")
            live_signal = y if c["validity"] == "valid" and delivered else None
            expected_use = c["validity"] == "valid" and delivered == 1 and consumed == 1
            if row.get("observed_signal") != live_signal or row.get("used_signal") is not expected_use:
                errors.append(f"delivery/uptake custody mismatch: {c['id']}:{s}{y}{delivered}{consumed}")
            if expected_use and c["response"] == "follow":
                action = y
            elif expected_use and c["response"] == "invert":
                action = 1-y
            else:
                action = base_act
            if row.get("action") != action or row.get("task_loss") != loss[s][action] or row.get("authority") != "NONE":
                errors.append(f"action/loss/authority mismatch: {c['id']}:{s}{y}{delivered}{consumed}")
        if len(mass_by_key) != 16 or sum(mass_by_key.values()) != MASS_DEN:
            errors.append(f"incomplete mass partition: {c['id']}")
        task_loss = Fraction(sum(row["weight_num"]*row["task_loss"] for row in rows), MASS_DEN)
        net = base-task_loss-cost
        if r.get("base_action") != base_act or r.get("oracle_action_by_signal") != optimal:
            errors.append(f"decision oracle mismatch: {c['id']}")
        if r.get("base_loss") != fmt(base) or r.get("oracle_signal_loss") != fmt(oracle) or r.get("acquisition_cost") != fmt(cost):
            errors.append(f"VOI-C inputs mismatch: {c['id']}")
        if r.get("split_task_loss") != fmt(task_loss) or r.get("split_net_value") != fmt(net):
            errors.append(f"split-control outcome mismatch: {c['id']}")
        if r.get("no_acquisition_net_value") != "0/1":
            errors.append(f"no-acquisition baseline mismatch: {c['id']}")
        if c["validity"] == "valid":
            if r.get("disposition") != "SCORED" or r.get("voi_c") != fmt(expected_voi):
                errors.append(f"valid cue scoring mismatch: {c['id']}")
            if not isinstance(r.get("acquisition_information_bits"), (float, int)) or not isinstance(r.get("acquisition_only_net_value"), (float, int)):
                errors.append(f"acquisition-only proxy absent: {c['id']}")
            else:
                prior_probability = p1/SCALE
                p_signal1 = (prior[0]*like[0][1]+prior[1]*like[1][1])/(SCALE*SCALE)
                p_signal0 = 1-p_signal1
                posterior1_signal1 = (prior[1]*like[1][1]/(SCALE*SCALE))/p_signal1 if p_signal1 else 0.0
                posterior1_signal0 = (prior[1]*like[1][0]/(SCALE*SCALE))/p_signal0 if p_signal0 else 0.0
                mutual_info = binary_entropy(prior_probability)-p_signal1*binary_entropy(posterior1_signal1)-p_signal0*binary_entropy(posterior1_signal0)
                if abs(r["acquisition_information_bits"]-mutual_info) > 1e-12:
                    errors.append(f"information proxy mismatch: {c['id']}")
                expected_proxy = mutual_info-float(cost)
                if abs(r["acquisition_only_net_value"]-expected_proxy) > 1e-12:
                    errors.append(f"acquisition-only net value mismatch: {c['id']}")
        else:
            if r.get("disposition") != "UNKNOWN_STALE" or r.get("voi_c") is not None or r.get("acquisition_information_bits") is not None or r.get("acquisition_only_net_value") is not None:
                errors.append(f"stale cue promoted to evidence: {c['id']}")
        summaries[c["id"]] = {"base": base, "voi_c": expected_voi, "split": net,
                               "info": r.get("acquisition_only_net_value"), "case": c}

    pair_expected = {}
    for pair in ("reference", "holdout_1", "holdout_2"):
        aa, bb = summaries.get(f"pair_A_{pair}"), summaries.get(f"pair_B_{pair}")
        if aa is None or bb is None:
            errors.append(f"pair missing: {pair}")
            continue
        pair_expected[pair] = {
            "voi_c_A_gt_B": aa["voi_c"] > bb["voi_c"],
            "split_A_lt_B": aa["split"] < bb["split"],
            "acquisition_only_A_gt_B": aa["info"] > bb["info"]}
    if raw.get("pair_comparisons") is None:
        errors.append("pair comparisons missing")
    else:
        for pair, expected in pair_expected.items():
            got = raw["pair_comparisons"].get(pair, {})
            if any(got.get(k) is not v for k, v in expected.items()):
                errors.append(f"pair ranking mismatch: {pair}")
            aa, bb = summaries[f"pair_A_{pair}"], summaries[f"pair_B_{pair}"]
            expected_values = {"A_voi_c": fmt(aa["voi_c"]), "B_voi_c": fmt(bb["voi_c"]),
                               "A_split": fmt(aa["split"]), "B_split": fmt(bb["split"])}
            if any(got.get(k) != v for k, v in expected_values.items()):
                errors.append(f"pair values mismatch: {pair}")
    for pair in ("reference", "holdout_1", "holdout_2"):
        p = pair_expected.get(pair, {})
        if not (p.get("voi_c_A_gt_B") and p.get("split_A_lt_B") and p.get("acquisition_only_A_gt_B")):
            errors.append(f"preregistered rank reversal absent: {pair}")
    if "positive_but_unconsumed" in summaries:
        s = summaries["positive_but_unconsumed"]
        if not (s["voi_c"] > 0 and s["split"] < 0 and s["case"]["uptake"] == 0):
            errors.append("positive-but-unconsumed control failed")
    if "irrelevant_cue" in summaries and summaries["irrelevant_cue"]["voi_c"] != Fraction(-1, 100):
        errors.append("irrelevant-cue negative control failed")
    if "rare_high_consequence" in summaries and summaries["rare_high_consequence"]["split"] <= 0:
        errors.append("rare high-consequence control did not retain positive split value")
    if "misleading_response" in summaries and summaries["misleading_response"]["split"] >= 0:
        errors.append("misleading-response control did not expose negative value")
    if raw.get("all_authority_none") is not True or raw.get("all_mandatory_gates_unchanged") is not True:
        errors.append("global hard-gate invariant failed")
    return errors


def main(input_path, raw_path, out_path):
    config = json.loads(Path(input_path).read_text())
    raw = json.loads(Path(raw_path).read_text())
    errs = verify(config, raw)
    result = {"allocation": config["allocation"], "status": "PASS_METHOD_SCOPED" if not errs else "FAIL_AUDIT",
              "errors": errs, "cases": len(config["cases"]), "rows": sum(len(x.get("rows", [])) for x in raw.get("cases", [])),
              "candidate_sha256": hashlib.sha256(Path(raw_path).read_bytes()).hexdigest(),
              "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out = Path(out_path)
    tmp = out.with_name(out.name + ".partial")
    data = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with open(tmp, "xb") as f:
        f.write(data)
        f.flush()
        import os
        os.fsync(f.fileno())
    tmp.replace(out)
    print(json.dumps(result, sort_keys=True))
    return 0 if not errs else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: auditor.py INPUT_JSON CANDIDATE_RAW_JSON AUDIT_JSON")
    raise SystemExit(main(*sys.argv[1:]))
