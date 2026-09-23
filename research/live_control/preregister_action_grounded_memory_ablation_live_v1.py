"""Freeze the first crop/full/no-prior-memory live allocation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/action-grounded-memory-ablation-live-01"
PLAN = HERE / "action_grounded_memory_ablation_live_v1_prereg.json"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if PLAN.exists() or OUT.exists(): raise FileExistsError("plan/output already exists")
    scenarios = ["shifted", "duplicate", "restyled_trap"]
    orders = [["no_memory", "full_frame", "action_crop"],
              ["full_frame", "action_crop", "no_memory"],
              ["action_crop", "no_memory", "full_frame"]]
    schedule = []; ordinal = 1
    for scenario, arms in zip(scenarios, orders):
        for arm in arms:
            schedule.append({"ordinal": ordinal, "scenario": scenario, "arm": arm,
                             "name": f"{ordinal:02d}-{scenario}-{arm}"}); ordinal += 1
    sources = ["action_grounded_memory_ablation_live_v1.py", "visual_memory_fixture_v1.py",
               "visual_memory_model_v1.py", "visual_memory_model_runner_v1.py",
               "visual_memory_decision_schema_v1.json", "visual_memory_decision_responder_v1.txt",
               "test_action_grounded_memory_ablation_live_v1.py",
               "audit_action_grounded_memory_ablation_live_v1.py",
               "preregister_action_grounded_memory_ablation_live_v1.py"]
    full = "results/adaptive-semantic-repair-live-02/case-01-local/013.png"
    crop = "results/action-grounded-visual-memory-01/local/target.png"
    plan = {"schema": "action-grounded-memory-ablation-live-prereg-v1", "seed": 218,
            "chromium": "/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome",
            "requested_effort": "low", "arms": ["no_memory", "full_frame", "action_crop"],
            "scenarios": scenarios, "schedule": schedule,
            "calls": {"schema_preflight": 1, "comparison": 9, "total": 10}, "retries": 0,
            "same_prompt": True, "same_current_frame_per_scenario": True,
            "memory": {"full_frame_path": full, "full_frame_sha256": sha(HERE / full),
                       "action_crop_path": crop, "action_crop_sha256": sha(HERE / crop)},
            "source_sha256": {name: sha(HERE / name) for name in sources},
            "formal_pass": "schema preflight completes; all 9 arms complete; byte-identical current frame within each scenario; every action empty-release verified",
            "crop_transfer_rule": "3/3 correct, zero wrong-target, no worse correctness than both controls, and fewer actual input tokens than full-frame",
            "scope": "one finite actual Chromium allocation; first outcome retained; no retries; no general memory, token, latency, or human-tempo claim"}
    PLAN.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"frozen": len(schedule), "order": [row["name"] for row in schedule]}, indent=2))


if __name__ == "__main__": main()
