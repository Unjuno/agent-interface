#!/usr/bin/env python3
"""Single hand-authored construction check; does not enumerate the formal grid."""
import importlib.util
from fractions import Fraction as F
from pathlib import Path

source = Path(__file__).with_name("experiment.py")
spec = importlib.util.spec_from_file_location("option_t1_experiment", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

case = {
    "case_id": "smoke-route-emerges", "irreversibility": "one_shot",
    "loss": F(2), "p_bad": F(1, 2), "accuracy": F(1, 2),
    "wait_cost": F(1, 4), "deadline_slack": True,
    "alternative_now": False, "alternative_after": True,
    "primary_survives": True, "gate_open": True,
}
row = module.evaluate(case)
assert row["option_aware"]["action"] == "WAIT_PROBE"
assert row["voi_only"]["action"] != "WAIT_PROBE"
assert row["hard_gate_violations"] == 0
blocked = dict(case, gate_open=False)
assert module.evaluate(blocked)["option_aware"]["action"] == "NOOP"
print("construction smoke PASS: route-preserving wait separates from zero-EVSI policy; closed gate abstains")
