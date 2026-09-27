"""Freeze model use of combined observe-target with a post-model stale target."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-observe-target-model-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    names = [
        "preregister_chromium_observe_target_model_pair_v1.py",
        "run_chromium_observe_target_model_pair_v1.py",
        "target_handle_model_runner_v2.py", "gui_action_responder_v1.txt",
        "target_action_envelope_schema_v1.json", "target_handle_chromium_socket_v4.py",
        "interactive_target_handle_chromium_v4.py", "session_v32.py",
        "observe_target_handle_v1.py", "session_v31.py", "session_v30.py",
        "session_v29.py", "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
        "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py",
    ]
    version = subprocess.run([
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
        "--version"], capture_output=True, text=True, check=True).stdout.strip()
    plan = {
        "status": "preregistered_before_fresh_live_execution",
        "study": "chromium-observe-target-model-pair-01",
        "execution_order": [
            {"name": "changed-target", "changed_target": True, "seed": 991013},
            {"name": "stable", "changed_target": False, "seed": 991013},
        ],
        "common": (
            "isolated Chromium X11, same seed/task/prompt, Luna-low, private-ID-backed "
            "save_form alias, no model image, empty workspace, project docs zero, "
            "user config/rules/plugins/shell/fast mode disabled"
        ),
        "intervention": (
            "after identical model return, changed-target navigates the same surface "
            "to about:blank; stable leaves the form unchanged; both capture fresh "
            "post-model observations before attempting the identical model action"
        ),
        "promotion": (
            "strict actions 2/2 with input range <=128; stable independently saves and "
            "uses14 durable calls; changed-target returns MISSING with zero target-click "
            "pointer admissions, needs_decision, verified release and no submission"
        ),
        "failure_policy": "retain both first sessions; no retry, prompt, alias, box or order repair",
        "codex_cli": version,
        "sources": {name: sha(HERE / name) for name in names},
        "scope": (
            "two fresh same-seed Chromium sessions and two Luna-low calls; one stable "
            "success plus one post-model target-loss refusal; no causal latency, monetary "
            "cost, broad token reduction, human-speed, unknown-app or default claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
