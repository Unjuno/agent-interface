"""Execute and strictly score the preregistered target-handle model ABBA screen."""
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/target-handle-model-screen-01"
IMAGE = HERE / "results/chromium-target-handle-pair-01/positive/runtime/014.png"
REPO = HERE.parent.parent
NODE = Path(r"C:\Program Files\nodejs\node.exe")
CLI = Path.home() / "AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"


def parse(text, mode):
    value = json.loads(text)
    if mode == "coordinate":
        if set(value) != {"op", "x", "y", "button", "duration_ms"}:
            raise ValueError("coordinate fields")
        if value["op"] != "pointer_click" or value["button"] != 1 or value["duration_ms"] != 80:
            raise ValueError("coordinate constants")
        if any(type(value[key]) is not int for key in ("x", "y")):
            raise ValueError("coordinate types")
        correct = 270 <= value["x"] < 312 and 242 <= value["y"] < 260
    else:
        expected = {"op": "pointer_click_target", "target_handle": "h_save_form",
                    "offset": [20, 9], "button": 1, "duration_ms": 80}
        correct = value == expected
    return value, correct


def main():
    plan = json.loads((ROOT / "plan.json").read_text(encoding="utf-8"))
    results = []
    for index, mode in enumerate(plan["order"], 1):
        output = ROOT / f"call-{index}-{mode}"
        args = [sys.executable, str(HERE / "target_handle_model_runner_v1.py"),
                str(NODE), str(CLI), str(ROOT / f"{mode}-prompt.txt"), str(REPO),
                str(output), mode, str(IMAGE) if mode == "coordinate" else "-"]
        completed = subprocess.run(args, capture_output=True, timeout=90)
        (ROOT / f"call-{index}-stdout.txt").write_bytes(completed.stdout)
        (ROOT / f"call-{index}-stderr.txt").write_bytes(completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError(f"model call {index} failed; no retry")
        events = [json.loads(line) for line in
                  (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        messages = [row["item"]["text"] for row in events
                    if row.get("type") == "item.completed" and
                    row.get("item", {}).get("type") == "agent_message"]
        completed_turns = [row for row in events if row.get("type") == "turn.completed"]
        if len(messages) != 1 or len(completed_turns) != 1:
            raise ValueError("one message and completed turn required")
        typed, correct = parse(messages[0], mode)
        process = json.loads((output / "process.json").read_text())
        result = {"call": index, "mode": mode, "typed": typed, "correct": correct,
                  "usage": completed_turns[0]["usage"],
                  "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
    summary = {"results": results, "all_correct": all(row["correct"] for row in results)}
    (ROOT / "report.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
