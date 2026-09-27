"""Freeze fresh live model coordinate-versus-handle Chromium ABBA."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-target-handle-model-abba-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    sources = [
        "preregister_chromium_target_handle_model_abba_v1.py",
        "run_chromium_target_handle_model_abba_v1.py",
        "target_handle_model_runner_v2.py",
        "gui_action_responder_v1.txt",
        "target_action_envelope_schema_v1.json",
        "target_handle_chromium_socket_v2.py",
        "interactive_target_handle_chromium_v2.py",
        "session_v30.py",
        "session_v29.py",
        "session_v28.py",
        "scoped_target_handle_v2.py",
        "scoped_target_handle_v1.py",
        "coordinate_frame_transform_v1.py",
        "session_v26.py",
        "session_v25.py",
        "session_v24.py",
        "session_v23.py",
        "session_v22.py",
        "session_v21.py",
        "session_v20.py",
        "session_v19.py",
        "session_v18.py",
        "session_v17.py",
        "session_v16.py",
        "session_v15.py",
        "session_v14.py",
        "session_v13.py",
        "session_v12.py",
        "session_v11.py",
        "session_v10.py",
        "session_v9.py",
        "executor_v4.py",
        "executor_v3.py",
        "cause_servo_interactive_v4.py",
        "cause_servo_session_v1.py",
        "cause_session_v1.py",
        "event_socket_v11.py",
        "durable_submit_v4.py",
        "append_checkpoint_v1.py",
        "received_continuation_v1.py",
        "received_exchange_v2.py",
        "lease.py",
    ]
    node = r"C:\Program Files\nodejs\node.exe"
    cli = Path.home() / "AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"
    version = subprocess.run(
        [node, str(cli), "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    plan = {
        "status": "preregistered_before_fresh_live_execution",
        "study": "chromium-target-handle-model-abba-01",
        "execution_order": [
            {"mode": "coordinate", "seed": 991006},
            {"mode": "handle", "seed": 991006},
            {"mode": "handle", "seed": 991007},
            {"mode": "coordinate", "seed": 991007},
        ],
        "common": {
            "runtime": "same Chromium private form, session_v30 and executor_v4",
            "setup": (
                "navigate, type exact seed token, mint textured Save region, move "
                "surface by requested [20,8], acquire fresh observation; after model "
                "return acquire another observation before action admission"
            ),
            "model": "gpt-5.6-luna low, Fast disabled",
            "model_context": (
                "same short instructions, single action envelope schema, empty workspace, "
                "project_doc_max_bytes=0, user config/rules/tools disabled"
            ),
            "independent_oracle": "exact generated token in HTTP POST/file",
        },
        "coordinate_arm": (
            "attach current post-move frame; model chooses absolute point; normal "
            "pointer admission"
        ),
        "handle_arm": (
            "read-only target_handle_query on current observation; no image to model; "
            "model returns handle relation; admission resolves handle again before input"
        ),
        "promotion": {
            "fresh_independent_success": "4/4",
            "strict_model_outputs": "4/4",
            "handle_query_and_admission_status": "REVALIDATED for both handle cases",
            "within_arm_input_range_max": 128,
            "handle_input_mean_lower": True,
        },
        "metrics": [
            "independent correctness",
            "reported model tokens",
            "model runner time",
            "decision start to independent evaluation return",
            "action to first useful feedback",
            "action to semantic completion",
            "durable calls",
        ],
        "failure_policy": "retain first four sessions; no rerun, prompt, coordinate, box or order repair",
        "codex_cli": version,
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": (
            "four fresh private Chromium X11 sessions over two seeds; one final model "
            "choice per session; no causal latency, monetary cost, human-speed, "
            "cross-domain or default-promotion claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
