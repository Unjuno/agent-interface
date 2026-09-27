#!/usr/bin/env python3
from decimal import Decimal, getcontext
from fractions import Fraction
getcontext().prec = 50
UNITS = [
    "wall_ns", "input_tokens", "output_tokens", "reasoning_output_tokens",
    "planner_generations", "model_visible_images", "local_observations", "durable_calls"
]

def ms_to_ns(text):
    value = Decimal(text) * Decimal(1_000_000)
    if value != value.to_integral_value():
        raise ValueError("elapsed_ms_not_exact_integer_ns")
    return int(value)

def normalized(row):
    return {
        "wall_ns": ms_to_ns(row["elapsed_ms"]),
        "input_tokens": int(row["input_tokens"]),
        "output_tokens": int(row["output_tokens"]),
        "reasoning_output_tokens": int(row["reasoning_output_tokens"]),
        "planner_generations": int(row["planner_generations"]),
        "model_visible_images": int(row["model_visible_images"]),
        "local_observations": int(row["local_observations"]),
        "durable_calls": int(row["durable_calls"]),
    }

def validate_fixture(f):
    assert f["source"]["git_blob"] == "7db368b2d492b5b95f5f038fb7cb5dd6b78a27a7"
    assert f["source"]["report_json_blob"] == "57954e7608f823ec031600a12e0062eeceafdcf4"
    assert f["source"]["preflight_wall_result_blob"] == "89e8bc08d4d81f93a496eac83437ad77a06f1214"
    assert f["primary_comparator"] == {
        "numerator_id": "persistent.task4.layout_B.repair",
        "denominator_id": "ephemeral.task4.layout_B.cold_reacquisition"
    }
    r, d = f["repair"], f["matched_reacquisition"]
    assert (r["arm"], r["phase"], r["task"], r["layout"], r["route"]) == ("persistent", "layout_change", 4, "B", "repair")
    assert (d["arm"], d["phase"], d["task"], d["layout"], d["route"]) == ("ephemeral", "layout_change", 4, "B", "cold")
    assert r["cached_input_tokens"] == 0 and d["cached_input_tokens"] == 0
    rb = f["persistent_repeat_B"]
    for k in ["input_tokens", "output_tokens", "reasoning_output_tokens", "planner_generations", "model_visible_images"]:
        assert rb[k] == 0
    normalized(r); normalized(d)
    return True

def ratio_record(n, d):
    if d == 0:
        if n == 0:
            return {"numerator": n, "denominator": d, "difference": 0, "ratio": "undefined_0_over_0"}
        return {"numerator": n, "denominator": d, "difference": n-d, "ratio": "undefined_divide_by_zero"}
    frac = Fraction(n, d)
    dec = Decimal(frac.numerator) / Decimal(frac.denominator)
    return {
        "numerator": n,
        "denominator": d,
        "difference": n-d,
        "ratio_fraction": f"{frac.numerator}/{frac.denominator}",
        "ratio_decimal": format(dec, ".15f")
    }

def compute(f):
    validate_fixture(f)
    rn, dn = normalized(f["repair"]), normalized(f["matched_reacquisition"])
    return {u: ratio_record(rn[u], dn[u]) for u in UNITS}
