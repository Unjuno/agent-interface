import hashlib
import itertools
import json

BASE = "6b1ad36c0628098c2d1c28b0a1b371db099aecce"
GRID = {
    "p_safe": [0.20, 0.40, 0.60, 0.80, 0.95],
    "loss": [1.0, 4.0, 16.0],
    "sensitivity": [0.60, 0.80, 1.00],
    "false_pass": [0.0, 0.10, 0.30],
    "delay_cost": [0.0, 0.05, 0.20],
}
def evaluate(p, loss, sensitivity, false_pass, delay):
    action_value = p - (1.0 - p) * loss
    stop_value = max(0.0, action_value)
    pass_value = max(0.0, p * sensitivity - (1.0 - p) * loss * false_pass)
    fail_value = max(0.0, p * (1.0 - sensitivity) - (1.0 - p) * loss * (1.0 - false_pass))
    test_value = pass_value + fail_value
    continue_value = test_value - delay
    net_voi = continue_value - stop_value
    immediate_admit = action_value > 1e-12
    voi_continue = continue_value > stop_value + 1e-12
    premium = (1.0 - p) * loss if immediate_admit else 0.0
    premium_continue_value = continue_value + premium
    premium_continue = premium_continue_value > stop_value + 1e-12
    return {
        "action_value": action_value, "stop_value": stop_value,
        "pass_value": pass_value, "fail_value": fail_value,
        "test_value": test_value, "continue_value": continue_value,
        "net_voi": net_voi,
        "immediate_action": "ADMIT" if immediate_admit else "YIELD",
        "voi_decision": "CONTINUE" if voi_continue else "STOP",
        "bellman_decision": "CONTINUE" if continue_value > stop_value + 1e-12 else "STOP",
        "option_premium": premium, "premium_continue_value": premium_continue_value,
        "premium_decision": "CONTINUE" if premium_continue else "STOP",
        "premium_dominated_wait": premium_continue and continue_value < stop_value - 1e-12,
    }
grid_bytes = json.dumps(GRID, sort_keys=True, separators=(",", ":")).encode()
rows = []
for i, values in enumerate(itertools.product(GRID["p_safe"], GRID["loss"], GRID["sensitivity"], GRID["false_pass"], GRID["delay_cost"])):
    p, loss, sensitivity, false_pass, delay = values
    rows.append({"case_id": f"voi-option-{i:03d}",
                 "inputs": {"p_safe": p, "loss": loss, "sensitivity": sensitivity, "false_pass": false_pass, "delay_cost": delay},
                 **evaluate(*values)})
summary = {
    "case_count": len(rows),
    "voi_bellman_mismatches": sum(r["voi_decision"] != r["bellman_decision"] for r in rows),
    "premium_decision_changes": sum(r["premium_decision"] != r["voi_decision"] for r in rows),
    "premium_dominated_waits": sum(r["premium_dominated_wait"] for r in rows),
    "max_voi_value_identity_error": max(abs(r["net_voi"] - (r["continue_value"] - r["stop_value"])) for r in rows),
}
raw = {"schema": "voi_option_5306_t1_raw_v1", "base_main_sha": BASE,
       "grid_sha256": hashlib.sha256(grid_bytes).hexdigest(), "grid": GRID,
       "model": "one-step binary signal; exact enumeration; no sampling",
       "rows": rows, "summary": summary}
print(json.dumps(raw, sort_keys=True, separators=(",", ":")))
