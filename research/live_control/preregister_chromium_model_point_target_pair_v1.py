"""Freeze model-point target derivation with a changed-patch negative."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-model-point-target-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    names = [
        "preregister_chromium_model_point_target_pair_v1.py",
        "run_chromium_model_point_target_pair_v1.py", "model_point_target_v1.py",
        "session_v33.py", "target_handle_chromium_socket_v5.py",
        "interactive_target_handle_chromium_v5.py", "target_handle_model_runner_v2.py",
        "gui_action_responder_v1.txt", "target_action_envelope_schema_v1.json",
        "session_v32.py", "observe_target_handle_v1.py", "session_v31.py",
        "session_v30.py", "session_v29.py", "scoped_target_handle_v3.py",
        "scoped_target_handle_v2.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py",
        "received_exchange_v2.py",
    ]
    version = subprocess.run([
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
        "--version"], capture_output=True, text=True, check=True).stdout.strip()
    plan = {
        "status": "preregistered_before_fresh_live_execution",
        "study": "chromium-model-point-target-pair-01",
        "execution_order": [
            {"name": "changed-target", "changed_target": True, "seed": 991014},
            {"name": "stable", "changed_target": False, "seed": 991014},
        ],
        "common": (
            "same seed/task/coordinate prompt, Luna-low and current 1280x800 image; "
            "runtime derives a24x14 region centered on the model point and retains "
            "up to16 exact source observations; no caller-authored absolute target box"
        ),
        "stable": (
            "fresh exact patch permits alias mint; move surface[20,8]; combined handle "
            "check; second no-image Luna-low alias action; independent exact save"
        ),
        "changed_target": (
            "after the coordinate model returns, navigate same surface to about:blank; "
            "point mint must capture fresh, detect source_patch_changed, create no handle "
            "and stop needs_decision"
        ),
        "fixed_region_size": [24, 14],
        "archived_feasibility": (
            "prior coordinate point[290,252] yields one unique patch in its frame with "
            "RGB stddev approximately77 per channel"
        ),
        "promotion": (
            "coordinate grounding2/2 and input range<=128; stable exact mint, moved alias "
            "reuse and independent success; changed patch refusal with no handle and no save"
        ),
        "failure_policy": "retain both first sessions; no retry, point, size, prompt or order repair",
        "codex_cli": version,
        "sources": {name: sha(HERE / name) for name in names},
        "scope": (
            "two fresh same-seed Chromium sessions, two coordinate Luna-low calls and one "
            "handle Luna-low call; point-derived target plus constructed changed-patch "
            "negative; no causal latency, cost, broad token, unknown-app or human-speed claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
