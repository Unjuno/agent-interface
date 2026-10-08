from decimal import Decimal, getcontext
from fractions import Fraction
getcontext().prec = 50

COUNT_KEYS = [
    "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
    "planner_generations", "model_visible_images", "local_observations", "durable_calls"
]
MODEL_KEYS = [
    "input_tokens", "output_tokens", "reasoning_output_tokens",
    "planner_generations", "model_visible_images"
]
LOCAL_KEYS = ["local_observations", "durable_calls"]
EXPECTED_SOURCE = "7db368b2d492b5b95f5f038fb7cb5dd6b78a27a7"
EXPECTED_PHASES = ["layout_change", "repeat_B"]


def validate_fixture(f):
    assert f["source_git_blob"] == EXPECTED_SOURCE
    assert f["horizon_phases"] == EXPECTED_PHASES
    assert f["cached_input_semantics"].endswith("separate only")
    p, e = f["arms"]["persistent"], f["arms"]["ephemeral"]
    assert p["routes"][3:] == ["repair", "reuse", "reuse"]
    assert e["routes"][3:] == ["cold", "cold", "cold"]
    for arm in (p, e):
        assert set(EXPECTED_PHASES).issubset(arm)
        for phase in EXPECTED_PHASES:
            row = arm[phase]
            assert set(row) == {"elapsed_ms", *COUNT_KEYS}
            assert Decimal(row["elapsed_ms"]) >= 0
            assert all(type(row[k]) is int and row[k] >= 0 for k in COUNT_KEYS)
    assert all(p["repeat_B"][k] == 0 for k in MODEL_KEYS)
    return True


def horizon(arm):
    out = {"elapsed_ms": sum((Decimal(arm[p]["elapsed_ms"]) for p in EXPECTED_PHASES), Decimal(0))}
    for key in COUNT_KEYS:
        out[key] = sum(arm[p][key] for p in EXPECTED_PHASES)
    return out


def ratio_num_den(a, b):
    if isinstance(a, Decimal):
        scale = max(-a.as_tuple().exponent, -b.as_tuple().exponent)
        ai = int(a * (Decimal(10) ** scale))
        bi = int(b * (Decimal(10) ** scale))
        fr = Fraction(ai, bi)
    else:
        fr = Fraction(a, b)
    return {"numerator": fr.numerator, "denominator": fr.denominator, "decimal": format(Decimal(fr.numerator) / Decimal(fr.denominator), ".15f")}


def compute(f):
    validate_fixture(f)
    p = horizon(f["arms"]["persistent"])
    e = horizon(f["arms"]["ephemeral"])
    diffs, ratios = {}, {}
    for key in ["elapsed_ms", *COUNT_KEYS]:
        diffs[key] = str(p[key] - e[key]) if key == "elapsed_ms" else p[key] - e[key]
        ratios[key] = ratio_num_den(p[key], e[key]) if e[key] != 0 else None
    return p, e, diffs, ratios
