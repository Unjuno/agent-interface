"""WSL live driver with explicit Windows-only model runner handoff."""
import subprocess
from pathlib import Path

import run_chromium_target_handle_model_abba_v1 as shared


HERE = Path(__file__).resolve().parent
shared.OUT = HERE / "results/chromium-target-handle-model-abba-02"
WINDOWS_PYTHON = Path(
    "/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe"
)


def windows_path(path):
    return subprocess.run(
        ["wslpath", "-w", str(Path(path).resolve())],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def model_call(root, index, mode, prompt, image):
    prompt_path = root / "model-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "model"
    args = [
        str(WINDOWS_PYTHON),
        windows_path(HERE / "target_handle_model_runner_v2.py"),
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
        windows_path(prompt_path),
        windows_path(shared.OUT / "empty-workspace"),
        windows_path(output),
        mode,
        windows_path(image) if image is not None else "-",
        windows_path(HERE / "gui_action_responder_v1.txt"),
        windows_path(HERE / "target_action_envelope_schema_v1.json"),
    ]
    completed = subprocess.run(args, capture_output=True, timeout=90)
    (root / "model-runner-stdout.txt").write_bytes(completed.stdout)
    (root / "model-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"model call {index} failed; no retry")
    result = shared.parse_model(output, mode)
    shared.dump(root / "model-result.json", result)
    return result


shared.model_call = model_call


if __name__ == "__main__":
    shared.main()
