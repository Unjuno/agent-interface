"""Freeze fresh live ABBA using short session aliases for target handles."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-target-handle-model-abba-03"
PREVIOUS = HERE / "results/chromium-target-handle-model-abba-02/preregistration.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    sources = [
        "preregister_chromium_target_handle_model_abba_v3.py",
        "run_chromium_target_handle_model_abba_v3.py",
        "target_handle_chromium_socket_v3.py",
        "interactive_target_handle_chromium_v3.py",
        "session_v31.py",
        "scoped_target_handle_v3.py",
        *previous["sources"].keys(),
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
        "study": "chromium-target-handle-model-abba-03",
        "predecessor": {
            "study": "chromium-target-handle-model-abba-02",
            "outcome": (
                "coordinate 2/2 passed; handle 0/2 safely refused unknown h_save_form "
                "because runtime minted private random IDs"
            ),
            "change": (
                "model and runtime use unique session alias save_form; private random "
                "registry ID remains undisclosed; new seeds only"
            ),
        },
        "execution_order": [
            {"mode": "coordinate", "seed": 991010},
            {"mode": "handle", "seed": 991010},
            {"mode": "handle", "seed": 991011},
            {"mode": "coordinate", "seed": 991011},
        ],
        "common": previous["common"],
        "coordinate_arm": previous["coordinate_arm"],
        "handle_arm": (
            "read-only query of session alias save_form; no image to model; model "
            "returns the alias relation; admission revalidates alias against the "
            "private random registry ID on the post-model observation"
        ),
        "promotion": previous["promotion"],
        "failure_policy": (
            "retain first four sessions; no rerun, prompt, coordinate, alias, box or order repair"
        ),
        "codex_cli": version,
        "predecessor_plan_sha256": sha(PREVIOUS),
        "sources": {name: sha(HERE / name) for name in dict.fromkeys(sources)},
        "scope": (
            "four fresh private Chromium X11 sessions over two new seeds; one final "
            "model choice per session; isolated alias change; no causal latency, "
            "monetary cost, human-speed, cross-domain or default-promotion claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
