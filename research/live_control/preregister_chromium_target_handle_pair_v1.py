"""Freeze matched Chromium semantic-positive and changed-target handle cases."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-target-handle-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    sources = ["preregister_chromium_target_handle_pair_v1.py",
        "run_chromium_target_handle_pair_v1.py", "target_handle_chromium_socket_v1.py",
        "interactive_target_handle_chromium_v1.py", "scoped_target_handle_v2.py",
        "scoped_target_handle_v1.py", "coordinate_frame_transform_v1.py",
        "session_v29.py", "session_v28.py", "session_v26.py", "executor_v4.py",
        "cause_servo_interactive_v4.py", "cause_servo_session_v1.py",
        "cause_session_v1.py", "event_socket_v11.py", "durable_submit_v4.py",
        "append_checkpoint_v1.py", "received_continuation_v1.py",
        "received_exchange_v2.py", "session_v25.py", "session_v24.py", "session_v23.py",
        "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
        "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
        "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
        "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py"]
    plan = {"status": "preregistered_before_fresh_chromium_execution",
        "study": "chromium-target-handle-pair-01", "seed": 991005,
        "execution_order": ["changed-target", "positive"],
        "common": {"same_runtime": "Chromium private form via session_v29/executor_v4",
            "setup": "navigate to generated local URL, type exact generated token, mint textured Save-button region, request one bounded surface move, acquire fresh observation",
            "handle_action": "runtime handle plus [20,9] offset only; no absolute point or coordinate frame at use",
            "requested_move": [20, 8],
            "binding_rule": "derive from the actual fresh before/after pointer binding; do not require requested and observed deltas to match"},
        "positive_endpoint": "REVALIDATED exact region, ordinary pointer admission, completed/released terminal, independent HTTP POST equals generated token",
        "negative_intervention": "after mint/move/fresh observation, navigate the same Chromium surface to about:blank before handle use",
        "negative_endpoint": "MISSING, needs_decision, zero pointer admission and no submitted file",
        "metrics": ["task correctness", "action-to-first-useful-feedback",
                    "action-to-independent-semantic-completion", "durable calls"],
        "failure_policy": "retain first fresh result for each case; no coordinate, box, threshold or order correction",
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "two fresh scripted same-seed private Chromium X11 sessions; no model calls, human-speed, token, general semantic-identity or default-promotion claim"}
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
