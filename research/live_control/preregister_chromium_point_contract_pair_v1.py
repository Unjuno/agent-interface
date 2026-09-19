"""Freeze explicit point-space/motion authorship before fresh live execution."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-point-contract-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    names = [
        "preregister_chromium_point_contract_pair_v1.py",
        "run_chromium_point_contract_pair_v1.py", "point_target_contract_v2.py",
        "point_target_contract_schema_v1.json",
        "point_target_reference_responder_v1.txt",
        "target_handle_model_runner_v2.py", "session_v33.py",
        "model_point_target_v1.py", "target_handle_chromium_socket_v5.py",
        "interactive_target_handle_chromium_v5.py", "session_v32.py",
        "observe_target_handle_v1.py", "session_v31.py", "session_v30.py",
        "session_v29.py", "scoped_target_handle_v3.py",
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
        "study": "chromium-point-contract-pair-01",
        "execution_order": [
            {"name": "stable", "changed_target": False, "seed": 991015},
            {"name": "changed-target", "changed_target": True, "seed": 991015},
        ],
        "common": (
            "same seed/task/model prompt, controlled Luna-low and current 1280x800 "
            "image; model must author source_observation_pixels plus "
            "surface_origin_translation; runtime uses fixed24x14 region; one model call/case"),
        "stable": (
            "fresh exact point mint; move surface[20,8]; combined handle check; "
            "scripted alias click; independent exact save"),
        "changed_target": (
            "after model return navigate same surface to about:blank; fresh point mint "
            "must refuse source_patch_changed before handle or target pointer input"),
        "promotion": (
            "strict explicit model contract2/2 and input range<=128; stable follows "
            "surface origin and saves independently; changed patch refuses before handle"),
        "failure_policy": "retain both first sessions; no retry or prompt/point/frame/size/order repair",
        "codex_cli": version,
        "sources": {name: sha(HERE / name) for name in names},
        "scope": (
            "two fresh same-seed Chromium sessions and two Luna-low image calls; "
            "explicit model-authored point space/motion contract on one known button; "
            "no cross-domain, causal latency, monetary cost, broad token or human-speed claim"),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
