"""Freeze the one-allocation adaptive semantic repair live block."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "adaptive_semantic_repair_live_v2_prereg.json"
SOURCES = [
    "research/live_control/adaptive_semantic_repair_live_v2.py",
    "research/live_control/audit_adaptive_semantic_repair_live_v2.py",
    "research/live_control/test_adaptive_semantic_repair_live_v2.py",
    "research/live_control/adaptive_acquisition_caller_v3.py",
    "research/live_control/post_model_target_revalidation_v1.py",
    "research/live_control/semantic_repair_model_v2.py",
    "research/live_control/semantic_grounding_admission_v1.py",
    "research/live_control/target_handle_semantic_binding_v1.py",
    "research/live_control/target_relative_crop_semantic_probe_v1.py",
    "research/live_control/scoped_target_handle_v1.py",
    "research/live_control/semantic_probe_backend_v3.py",
    "research/live_control/semantic_probe_runtime_v3.py",
    "research/live_control/executor_v13.py",
    "research/live_control/executor_v11.py",
    "research/observation_gating/gui_suite.py",
    "research/live_control/compiled_form_grounding_v1.py",
    "research/live_control/compiled_form_grounding_schema_v1.json",
    "research/live_control/target_handle_model_runner_v2.py",
]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUT.exists(): raise RuntimeError("preregistration already exists")
    output = ROOT / "research/live_control/results/adaptive-semantic-repair-live-02"
    if output.exists(): raise RuntimeError("formal output already exists")
    plan = {
        "schema": "adaptive-semantic-repair-live-prereg-v2",
        "allocation_id": "adaptive-semantic-repair-live-02",
        "output": "research/live_control/results/adaptive-semantic-repair-live-02",
        "allocations": 1, "retry_limit": 0, "order": ["local", "model"],
        "seed": 217,
        "model": {"name": "gpt-5.6-luna", "effort": "low"},
        "expected_model_calls": {"local": 1, "model": 2},
        "required_cases": ["window_resize_local_repair", "button_hover_model_fallback"],
        "chromium": "/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome",
        "resize_width_delta": -120,
        "field_box": [135, 233, 240, 254],
        "submit_box": [248, 232, 296, 255],
        "semantic_screen_box": [15, 170, 330, 215],
        "expected_crop_sha256": "879ad35b666f63b1c9a401c359bd563c52170146b3e4ca5c7314448fdfb5784c",
        "max_positive_exchanges": 8,
        "hard_gates": [
            "both cases complete on their first allocation",
            "local case uses zero repair model calls",
            "hover case enters fallback from observed missing, ambiguous or changed evidence",
            "model fallback uses one later exact call-bound observation before input",
            "final current crop is evaluable and the completion predicate is missing before Submit",
            "independent exact submission",
            "zero unintended duplicate submission",
            "verified empty release for every input program",
            "all attempted model calls, images, waits and usage accounted",
            "zero retry"],
        "stop_rule": {
            "retain": "all hard gates pass in both cases",
            "hold": "typed upstream capacity deferral or formally invalid setup; retain without retry",
            "reject": "wrong/duplicate submission, stale target input, untyped failure or required branch mismatch"},
        "scope": ("V2 changes failed v1 only by treating an exact evaluable expected_crop_missing "
                  "result as the required pre-Submit state rather than requiring completion early. "
                  "One finite no-retry Linux/X11 Chromium integration allocation through "
                  "adaptive_acquisition_caller_v3. The two mutations differ, so this is not a "
                  "latency or token comparison. It tests one natural local resize repair and one "
                  "hover-patch model fallback with independent task/release evidence. No general "
                  "repair rate, savings, portability or human-tempo claim follows."),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES}}
    OUT.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("adaptive_semantic_repair_live_v2_preregistered")


if __name__ == "__main__": main()
