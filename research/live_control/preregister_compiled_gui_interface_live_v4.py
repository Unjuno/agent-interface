"""Freeze v4 after v3's preserved read-check status mismatch."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/compiled-gui-interface-live-04"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    sources = [
        "preregister_compiled_gui_interface_live_v4.py",
        "run_compiled_gui_interface_live_v4.py",
        "compiled_gui_interface_v1.py", "compiled_form_grounding_v1.py",
        "compiled_form_grounding_schema_v1.json",
        "adaptive_acquisition_caller_v1.py", "target_handle_model_runner_v2.py",
        "compiled_form_grounding_responder_v1.txt", "schema_preflight_gate_v1.py",
        "schema_preflight_v1.py", "schema_preflight_responder_v1.txt",
        "target_handle_chromium_socket_v5.py",
        "interactive_target_handle_chromium_v5.py", "session_v33.py",
        "session_v32.py", "observe_target_handle_v1.py",
        "model_point_target_v1.py", "coordinate_frame_transform_v1.py",
        "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py",
    ]
    plan = {
        "status": "preregistered_before_schema_preflight_and_fresh_gui_execution",
        "study": "compiled-gui-interface-live-04", "seed": 991024,
        "execution_order": [
            {"name": "changed-target", "changed_after_first": True},
            {"name": "positive", "changed_after_first": False},
        ],
        "common": {
            "fixture": "isolated private Chromium form with independent POST scoring",
            "requested_model": "gpt-5.6-luna", "requested_effort": "low",
            "grounding_calls": "one screenshot call per case; no retry",
            "model_output": "two source-observation points plus fixed method declaration",
            "caller": "adaptive_acquisition_caller_v1 injected-cold subpath; coarse stage omitted and not comparable to full cold",
            "method": "fresh-check field -> enter exact token -> fresh-check submit and field pixel change -> submit -> fresh submission pixel change -> independent score",
            "authority": "symbols are references only; observe-target read check plus ordinary pointer-target revalidation/admission per action",
            "runtime_budget": "two actions and 10000ms local runtime",
            "v1_fix": "mint form_field and submit_control in two independent one-step programs because the retained v1 batch was rejected before input",
            "v2_fix": "expand only form_field point region from 24x14 to 24x22 so the stable top/bottom field border supplies texture; use derived offset [12,11]",
            "v3_fix": "treat the read-only observe_target_handle result as present only for eligible=true and status=VALID; ordinary pointer execution still requires its own REVALIDATED event",
            "target_region_sizes": {"field": [24, 22], "submit": [24, 14]},
            "independent_point_boxes": {"field": [135, 233, 105, 21],
                                         "submit": [248, 232, 48, 23]},
            "field_effect": {"crop": [62, 233, 185, 21],
                             "minimum_changed_pixels": 40,
                             "baseline": "first local observation after grounding and handle mint; separate from model point patch"},
        },
        "positive_endpoint": {
            "compiled_outcome": "TASK_SUCCEEDED", "local_transitions": 2,
            "frontier_model_resumptions_inside_runtime": 0,
            "actions": ["enter_token", "submit_form"],
            "independent_submission": True,
        },
        "changed_intervention": "after the first action terminal, navigate the same Chromium surface to about:blank before the next local observation",
        "changed_endpoint": {
            "compiled_outcome": "SAFE_YIELD", "local_transitions": 1,
            "target_actions": ["enter_token"], "submit_target_action": False,
            "independent_submission": False,
        },
        "metrics": ["independent correctness and actual POST", "all model attempts and usage missingness",
            "planner boundaries and model-visible images", "local observation/action transitions",
            "action-to-first-useful-feedback per action", "first action-to-independent semantic completion",
            "source observation-to-independent completion", "grounding wait and local runtime separately",
            "durable calls", "pointer admissions and releases", "raw frame existence/hash"],
        "promotion_rule": "advance to matched efficiency comparison only if both model point pairs fall inside the frozen independent boxes and every positive/changed/schema/release/raw-evidence/no-retry gate passes",
        "failure_policy": "retain first result; no point, region, prompt, order, predicate, threshold or method correction and no retry",
        "known_limits": [
            "caller provides the bounded method scaffold; this does not prove open-ended planner-authored interface synthesis",
            "field effect is pixel change, with exact task correctness decided only by the independent POST scorer",
            "the field click region is frozen to the right half so its handle patch excludes the blinking left caret",
            "the changed intervention can make field pixels differ for an external reason; it must still prevent Submit",
            "one matched pair gives no success rate, tail latency, token saving, break-even, portability or human-tempo claim",
        ],
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "two fresh same-seed Linux/X11 Chromium sessions after a no-GUI schema gate; one Luna-low grounding call each, bounded local continuation, no efficiency or generality claim",
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
