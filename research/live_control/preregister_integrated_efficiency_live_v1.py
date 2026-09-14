"""Freeze the first formal integrated efficiency allocation before any calls."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-live-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    sources = [
        "run_integrated_efficiency_live_v1.py",
        "integrated_efficiency_protocol_v1.py",
        "integrated_efficiency_client_v1.py",
        "integrated_efficiency_model_v1.py",
        "integrated_efficiency_fixture_v1.py",
        "integrated_efficiency_runtime_v1.py",
        "integrated_efficiency_socket_v1.py",
        "interactive_integrated_efficiency_v1.py",
        "adaptive_acquisition_caller_v2.py",
        "schema_preflight_gate_v1.py", "schema_preflight_v1.py",
        "schema_preflight_responder_v1.txt",
        "plain_form_points_v1.py", "plain_form_points_schema_v1.json",
        "plain_form_points_responder_v1.txt",
        "compiled_form_grounding_v1.py", "compiled_form_grounding_schema_v1.json",
        "compiled_form_grounding_responder_v1.txt",
        "target_handle_model_runner_v2.py",
        "integrated_efficiency_discoveries_v1.json",
        "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py",
        "session_v33.py", "session_v32.py", "observe_target_handle_v1.py",
        "model_point_target_v1.py", "coordinate_frame_transform_v1.py",
    ]
    plan = {
        "schema": "integrated_efficiency_preregistration_v1",
        "status": "frozen_before_preflight_model_calls_and_gui_sessions",
        "study": "integrated-efficiency-live-01", "seed": 991028,
        "arm_order": ["plain", "ephemeral", "persistent"],
        "task_schedule": [
            {"task_id": f"task-{index}", "layout": "A" if index <= 3 else "B",
             "phase": ("cold" if index == 1 else "warm" if index <= 3 else
                       "invalidation_repair" if index == 4 else "post_repair_warm")}
            for index in range(1, 7)],
        "routes": {
            "plain": ["cold"] * 6, "ephemeral": ["cold"] * 6,
            "persistent": ["cold", "reuse", "reuse", "repair", "reuse", "reuse"]},
        "model": {"requested": "gpt-5.6-luna", "effort": "low",
                  "grounding_attempts": {"plain": 6, "ephemeral": 6,
                                         "persistent": 2},
                  "retry": False},
        "schema_acquisition": {
            "policy": "one forced-fresh no-image endpoint preflight per independently cold arm",
            "plain": "plain_form_points_schema_v1.json",
            "ephemeral": "compiled_form_grounding_schema_v1.json",
            "persistent": "compiled_form_grounding_schema_v1.json",
            "accounting": "each arm starts cumulative input tokens and planner generations with its own actual preflight; preflight image count is zero",
            "cache_policy": "separate empty cache directory per arm; cache hits invalidate the allocation"},
        "common": {
            "environment": "Linux/X11 private Chromium through session_v33 checked input",
            "fixture": "six append-only exact-token tasks, layouts A/A/A/B/B/B",
            "scorer": "private HTTP submission history; exact once with no unexpected submissions",
            "plain_capability": "one screenshot generation returns both points and one checked six-step batch",
            "compiled_capability": "same screenshot endpoint plus scoped point-derived handles and local checked continuation",
            "persistent_invalidation": "task-4 old A field handle must refuse before pointer input; one repair screenshot generation may mint B handles",
            "authority": "all pointer input uses the shared checked runtime; references carry no authority",
            "target_regions": {"field": [24, 38], "submit": [24, 14]},
        },
        "metrics": [
            "independent exact-once task correctness", "typed outcome and repair",
            "actual complete model usage and unique call ids", "model-visible images",
            "planner generations including preflight", "local observations and durable calls",
            "pointer admissions and verified empty releases",
            "source observation to independent receipt", "each button-down acknowledgement to next observation",
            "complete arm elapsed time and cumulative break-even"],
        "decision": {
            "retain": "all persistent tasks correct; zero old-target pointer admission; task-4 repair succeeds; all releases/accounting complete; persistent cumulative actual input tokens and planner generations are below both references by task 6; first measured token break-even is no later than task 4",
            "hold": "reference comparability/accounting fails, or a formal integration discovery invalidates this allocation",
            "reject": "persistent correctness/safety/repair fails, or frozen token/generation/break-even gates fail",
            "timing": "descriptive for this one allocation; faster only when persistent total elapsed is lower than both references"},
        "failure_policy": "preserve the first result and do not retry; a formal repair invalidates this allocation, which must HOLD before any new version or allocation",
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "one finite same-model three-arm allocation; no population success rate, generality, human-speed, product-completion or DOOM claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    print(json.dumps({"study": plan["study"], "status": plan["status"],
                      "source_count": len(sources)}, indent=2))


if __name__ == "__main__":
    main()
