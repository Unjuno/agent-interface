import json
from pathlib import Path
from common import compute, MODEL_KEYS, LOCAL_KEYS
ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixture.json").read_text())
p, e, diffs, ratios = compute(fixture)
model_lower = all(p[k] < e[k] for k in MODEL_KEYS)
wall_lower = p["elapsed_ms"] < e["elapsed_ms"]
repeat_zero = all(fixture["arms"]["persistent"]["repeat_B"][k] == 0 for k in MODEL_KEYS)
decision = "PASS_POST_REPAIR_REUSE_PAYBACK_RECONSTRUCTED_SCOPED" if (model_lower and wall_lower and repeat_zero) else "HOLD_POST_REPAIR_HORIZON_NOT_LOWER"
result = {
  "schema": "integrated_efficiency_post_repair_payback_result_v1",
  "task": fixture["task"],
  "decision": decision,
  "formal_invocation": 1,
  "reruns": 0,
  "source_git_blob": fixture["source_git_blob"],
  "horizon_phases": fixture["horizon_phases"],
  "persistent": {k: str(v) if k == "elapsed_ms" else v for k,v in p.items()},
  "ephemeral": {k: str(v) if k == "elapsed_ms" else v for k,v in e.items()},
  "persistent_minus_ephemeral": diffs,
  "persistent_over_ephemeral": ratios,
  "repeat_B_persistent": fixture["arms"]["persistent"]["repeat_B"],
  "repeat_B_ephemeral": fixture["arms"]["ephemeral"]["repeat_B"],
  "checks": {"wall_lower": wall_lower, "model_side_lower": model_lower, "repeat_B_zero_model": repeat_zero,
             "local_units_separate": all(k in p and k in e for k in LOCAL_KEYS)},
  "context_only": fixture["context_only"],
  "interpretation": [
    "same retained task4-task6 schedule only; no synthetic future horizon",
    "different-arm descriptive accounting, not a same-arm causal ablation",
    "model-side, local-work, and wall units remain separate",
    "cached input is subset-only and not added to input tokens"
  ]
}
(ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"decision": decision, "wall_ms": [str(p['elapsed_ms']), str(e['elapsed_ms'])], "input_tokens": [p['input_tokens'], e['input_tokens']], "generations": [p['planner_generations'], e['planner_generations']]}))
