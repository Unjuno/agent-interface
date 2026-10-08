#!/usr/bin/env python3
"""Exact finite split-control value ledger candidate for Issue #8638."""
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

S = 1000
DEN = S ** 4


def fstr(x):
    return f"{x.numerator}/{x.denominator}"


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + ".partial")
    data = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    with open(tmp, "xb") as f:
        f.write(data)
        f.flush()
        import os
        os.fsync(f.fileno())
    tmp.replace(path)
    return hashlib.sha256(data).hexdigest()


def entropy(p):
    return 0.0 if p in (0.0, 1.0) else -p * math.log2(p) - (1-p) * math.log2(1-p)


def derive(c):
    if c["support"] != "known":
        return {"case_id": c["id"], "disposition": "UNKNOWN_SUPPORT", "authority": "NONE",
                "mandatory_gates_unchanged": True, "base_loss": None, "voi_c": None,
                "split_net_value": None, "acquisition_only": None, "rows": []}
    p1 = c["prior_state1"]
    p = [S-p1, p1]
    q = c["accuracy"]
    likelihood = [[q, S-q], [S-q, q]]  # indexed state, then signal
    losses = c["loss"]
    base_action = min(range(2), key=lambda a: sum(p[s] * losses[s][a] for s in range(2)))
    base = Fraction(sum(p[s] * losses[s][base_action] for s in range(2)), S)
    optimal_by_signal = []
    for y in range(2):
        action = min(range(2), key=lambda a: sum(p[s] * likelihood[s][y] * losses[s][a] for s in range(2)))
        optimal_by_signal.append(action)
    oracle_num = sum(p[s] * likelihood[s][y] * losses[s][optimal_by_signal[y]]
                     for s in range(2) for y in range(2))
    oracle_loss = Fraction(oracle_num, S*S)
    cost = Fraction(c["cost_milli"], S)
    voi_c = base - oracle_loss - cost
    uptake_num = c["delivery"] * c["uptake"]
    split_loss_num = 0
    rows = []
    for s in range(2):
        for y in range(2):
            for delivered in range(2):
                p_delivery = c["delivery"] if delivered else S-c["delivery"]
                for consumed in range(2):
                    p_consume = (c["uptake"] if consumed else S-c["uptake"]) if delivered else (0 if consumed else S)
                    weight = p[s] * likelihood[s][y] * p_delivery * p_consume
                    effective = c["validity"] == "valid" and delivered == 1 and consumed == 1
                    observed = y if c["validity"] == "valid" and delivered == 1 else None
                    if effective:
                        if c["response"] == "follow":
                            action = y
                        elif c["response"] == "invert":
                            action = 1-y
                        else:
                            action = base_action
                    else:
                        action = base_action
                    loss = losses[s][action]
                    split_loss_num += weight * loss
                    rows.append({"case_id": c["id"], "state": s, "latent_signal": y,
                                 "delivered": delivered, "consumed": consumed,
                                 "observed_signal": observed, "used_signal": effective,
                                 "action": action, "task_loss": loss, "weight_num": weight,
                                 "weight_den": DEN, "authority": "NONE"})
    split_task_loss = Fraction(split_loss_num, DEN)
    split_net = base - split_task_loss - cost
    prior_p1 = p1 / S
    signal_p1 = sum((p[s] / S) * (likelihood[s][1] / S) for s in range(2))
    cond_p1_y1 = (p1 * likelihood[1][1] / (S*S)) / signal_p1 if signal_p1 else 0.0
    signal_p0 = 1.0 - signal_p1
    cond_p1_y0 = (p1 * likelihood[1][0] / (S*S)) / signal_p0 if signal_p0 else 0.0
    info = entropy(prior_p1) - signal_p1 * entropy(cond_p1_y1) - signal_p0 * entropy(cond_p1_y0)
    if c["validity"] != "valid":
        disposition = "UNKNOWN_STALE"
        voi_c_out = None
        info_out = None
    else:
        disposition, voi_c_out, info_out = "SCORED", fstr(voi_c), info
    return {"case_id": c["id"], "disposition": disposition, "authority": "NONE",
            "mandatory_gates_unchanged": True, "base_action": base_action,
            "oracle_action_by_signal": optimal_by_signal,
            "base_loss": fstr(base), "oracle_signal_loss": fstr(oracle_loss),
            "acquisition_cost": fstr(cost), "voi_c": voi_c_out,
            "split_task_loss": fstr(split_task_loss), "split_net_value": fstr(split_net),
            "no_acquisition_net_value": "0/1",
            "acquisition_information_bits": info_out,
            "acquisition_only_net_value": None if info_out is None else info_out-float(cost),
            "delivery_uptake_milli": uptake_num,
            "rows": rows}


def main(inp, out):
    raw_bytes = Path(inp).read_bytes()
    config = json.loads(raw_bytes)
    results = [derive(c) for c in config["cases"]]
    lookup = {r["case_id"]: r for r in results}
    pair_summary = {}
    for pair in ("reference", "holdout_1", "holdout_2"):
        a = lookup[f"pair_A_{pair}" if pair == "reference" else f"pair_A_{pair}"]
        b = lookup[f"pair_B_{pair}" if pair == "reference" else f"pair_B_{pair}"]
        pair_summary[pair] = {
            "voi_c_A_gt_B": Fraction(a["voi_c"]) > Fraction(b["voi_c"]),
            "split_A_lt_B": Fraction(a["split_net_value"]) < Fraction(b["split_net_value"]),
            "acquisition_only_A_gt_B": a["acquisition_only_net_value"] > b["acquisition_only_net_value"],
            "A_voi_c": a["voi_c"], "B_voi_c": b["voi_c"],
            "A_split": a["split_net_value"], "B_split": b["split_net_value"]}
    raw = {"allocation": config["allocation"], "protocol": config["protocol"],
           "input_sha256": hashlib.sha256(raw_bytes).hexdigest(), "weight_denominator": DEN,
           "enumeration": "state x latent-signal x delivery x uptake; exact integer masses",
           "cases": results, "pair_comparisons": pair_summary,
           "all_authority_none": all(r["authority"] == "NONE" for r in results),
           "all_mandatory_gates_unchanged": all(r["mandatory_gates_unchanged"] for r in results)}
    digest = atomic_json(out, raw)
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "allocation": config["allocation"],
                      "cases": len(results), "rows": sum(len(r["rows"]) for r in results),
                      "output_sha256": digest, "pairs": pair_summary}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py INPUT_JSON OUTPUT_JSON")
    main(sys.argv[1], sys.argv[2])
