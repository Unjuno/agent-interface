"""Freeze an archived OpenTTD history-needed memory comparison before model calls."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = HERE / "openttd_effect_memory_ablation_v1_prereg.json"
OUT = HERE / "results/openttd-effect-memory-ablation-01"
INPUTS = HERE / "results/openttd-action-effect-memory-inputs-01"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if PLAN.exists() or OUT.exists(): raise FileExistsError("plan/output already exists")
    contexts = ["segment-a-b", "segment-b-c"]
    orders = [["no_memory", "full_history", "action_crop"],
              ["action_crop", "no_memory", "full_history"]]
    schedule = []; ordinal = 1
    for context, arms in zip(contexts, orders):
        for arm in arms:
            schedule.append({"ordinal": ordinal, "context": context, "arm": arm,
                             "name": f"{ordinal:02d}-{context}-{arm}"}); ordinal += 1
    sources = ["openttd_effect_memory_ablation_v1.py", "openttd_effect_model_v1.py",
               "openttd_effect_model_runner_v1.py", "openttd_effect_decision_schema_v1.json",
               "openttd_effect_decision_responder_v1.txt", "audit_openttd_effect_memory_ablation_v1.py",
               "preregister_openttd_effect_memory_ablation_v1.py", "test_openttd_effect_decision_v1.py",
               "build_openttd_action_effect_memory_inputs_v1.py",
               "audit_openttd_action_effect_memory_inputs_v1.py"]
    plan = {"schema": "openttd-effect-memory-ablation-prereg-v1",
            "status": "preregistered_before_schema_preflight_and_comparison_calls",
            "requested_model": "gpt-5.6-luna", "requested_effort": "low",
            "contexts": contexts, "arms": ["no_memory", "full_history", "action_crop"],
            "schedule": schedule, "calls": {"schema_preflight": 1, "comparison": 6, "total": 7},
            "retries": 0, "same_current_frame_within_context": True,
            "same_prompt_within_context": True, "ground_truth": "independent retained engine transition: observed",
            "input_manifest_sha256": sha(INPUTS / "manifest.json"),
            "source_sha256": {name: sha(HERE / name) for name in sources},
            "formal_pass": "schema preflight and all six comparison calls complete once with complete usage",
            "crop_transfer_rule": "2/2 observed with safe advance, no worse correctness than both controls, fewer actual input tokens than full history",
            "default_rule": "if no-memory is also 2/2, retain current-only as default and allow crop only as a full-history replacement",
            "failure_policy": "retain first output and diagnostics; do not retry, repair in place, or replace allocation",
            "scope": "archived exact OpenTTD decisions only; no new game input; no causal latency, live-transfer, general memory, or human-tempo claim"}
    PLAN.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frozen": len(schedule), "requested_model": plan["requested_model"]}, indent=2))


if __name__ == "__main__": main()
