"""Freeze WSL-live/Windows-model corrected host-boundary Chromium ABBA."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-target-handle-model-abba-02"
PREVIOUS = HERE / "results/chromium-target-handle-model-abba-01/preregistration.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    inherited = [
        name for name in previous["sources"]
        if name != "preregister_chromium_target_handle_model_abba_v1.py"
    ]
    sources = [
        "preregister_chromium_target_handle_model_abba_v2.py",
        "run_chromium_target_handle_model_abba_v2.py",
        *inherited,
    ]
    version = subprocess.run(
        [
            r"/mnt/c/Program Files/nodejs/node.exe",
            r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
            "--version",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    plan = {
        "status": "preregistered_before_fresh_live_execution",
        "study": "chromium-target-handle-model-abba-02",
        "predecessor": {
            "study": "chromium-target-handle-model-abba-01",
            "outcome": "Windows driver failed before GUI/model because fcntl was unavailable",
            "change": (
                "run journal, GUI and X11 driver under WSL; invoke only the fixed "
                "Codex model runner through Windows Python; use new seeds"
            ),
        },
        "execution_order": [
            {"mode": "coordinate", "seed": 991008},
            {"mode": "handle", "seed": 991008},
            {"mode": "handle", "seed": 991009},
            {"mode": "coordinate", "seed": 991009},
        ],
        "common": {
            "runtime": "same Chromium private form, session_v30 and executor_v4",
            "setup": (
                "navigate, type exact token, mint Save region, move surface [20,8], "
                "observe; after model return observe again before action admission"
            ),
            "model": "gpt-5.6-luna low, Fast disabled",
            "model_context": (
                "same short instructions, single action envelope, empty workspace, "
                "project_doc_max_bytes=0, user config/rules/tools disabled"
            ),
            "host_boundary": (
                "WSL Python owns fcntl journal and X11; Windows Python owns Codex CLI; "
                "model runner timings stay Windows-local and decision return timings "
                "stay WSL-local"
            ),
            "independent_oracle": "exact generated token in HTTP POST/file",
        },
        "coordinate_arm": (
            "attach current post-move frame; model chooses absolute point; normal admission"
        ),
        "handle_arm": (
            "read-only query; no image to model; model returns relation; admission "
            "revalidates again on the post-model observation"
        ),
        "promotion": {
            "fresh_independent_success": "4/4",
            "strict_model_outputs": "4/4",
            "handle_query_and_admission_status": "REVALIDATED for both handle cases",
            "within_arm_input_range_max": 128,
            "handle_input_mean_lower": True,
        },
        "failure_policy": (
            "retain first four sessions; no rerun, prompt, coordinate, box or order repair"
        ),
        "codex_cli": version,
        "predecessor_plan_sha256": sha(PREVIOUS),
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": (
            "four fresh private Chromium X11 sessions over two new seeds; one final "
            "model choice per session; no causal latency, monetary cost, human-speed, "
            "cross-domain or default-promotion claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
