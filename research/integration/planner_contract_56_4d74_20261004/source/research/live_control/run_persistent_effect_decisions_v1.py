"""Execute the preregistered A/B/B/A visual-effect receipt calls once."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / "results/persistent-effect-decisions-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    assert plan["status"] == "preregistered_before_model_execution"
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    image = Path(plan["image"])
    assert sha(image) == plan["image_sha256"]
    node = Path(r"C:\Program Files\nodejs\node.exe")
    cli = Path.home() / "AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"
    calls = []
    for name in plan["order"]:
        condition = name.split("-", 1)[0]
        prompt = OUT / f"{condition}-prompt.txt"
        started = time.perf_counter_ns()
        completed = subprocess.run([
            sys.executable, str(HERE / "model_pair_runner_v2.py"),
            str(node), str(cli), str(image), str(prompt), str(REPO),
            str(OUT / name), "gpt-6-astra", "medium",
        ], capture_output=True, timeout=120)
        ended = time.perf_counter_ns()
        calls.append({
            "name": name,
            "condition": condition,
            "started_ns": started,
            "ended_ns": ended,
            "duration_ns": ended - started,
            "exit_code": completed.returncode,
            "stdout": completed.stdout.decode("utf-8", errors="replace"),
            "stderr": completed.stderr.decode("utf-8", errors="replace"),
        })
        (OUT / "execution.json").write_text(json.dumps(calls, indent=2) + "\n", encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(f"model call failed without retry: {name}")
    print(json.dumps(calls, indent=2))


if __name__ == "__main__":
    main()
