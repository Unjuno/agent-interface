"""Execute and score the preregistered controlled-context target-handle screen."""
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/target-handle-model-screen-02"
IMAGE = HERE / "results/chromium-target-handle-pair-01/positive/runtime/014.png"
NODE = Path(r"C:\Program Files\nodejs\node.exe")
CLI = Path.home() / "AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"
INSTRUCTIONS = HERE / "gui_action_responder_v1.txt"
SCHEMA = HERE / "target_action_union_schema_v1.json"


def parse(text, mode):
    value = json.loads(text)
    if mode == "coordinate":
        expected = {"op", "x", "y", "button", "duration_ms"}
        correct = (set(value) == expected and value.get("op") == "pointer_click"
                   and type(value.get("x")) is int and type(value.get("y")) is int
                   and 270 <= value["x"] < 312 and 242 <= value["y"] < 260
                   and value.get("button") == 1 and value.get("duration_ms") == 80)
    else:
        expected = {"op": "pointer_click_target", "target_handle": "h_save_form",
                    "offset": [20, 9], "button": 1, "duration_ms": 80}
        correct = value == expected
    return value, correct


def arm_stats(rows):
    total = [row["usage"]["input_tokens"] for row in rows]
    uncached = [row["usage"]["input_tokens"] - row["usage"]["cached_input_tokens"]
                for row in rows]
    return {"reported": total, "reported_mean": sum(total) / len(total),
            "reported_range": max(total) - min(total), "derived_uncached": uncached,
            "derived_uncached_mean": sum(uncached) / len(uncached)}


def main():
    plan = json.loads((ROOT / "plan.json").read_text(encoding="utf-8"))
    results = []
    for index, mode in enumerate(plan["order"], 1):
        output = ROOT / f"call-{index}-{mode}"
        args = [sys.executable, str(HERE / "target_handle_model_runner_v2.py"),
                str(NODE), str(CLI), str(ROOT / f"{mode}-prompt.txt"),
                str(ROOT / "empty-workspace"), str(output), mode,
                str(IMAGE) if mode == "coordinate" else "-", str(INSTRUCTIONS),
                str(SCHEMA)]
        completed = subprocess.run(args, capture_output=True, timeout=90)
        (ROOT / f"call-{index}-stdout.txt").write_bytes(completed.stdout)
        (ROOT / f"call-{index}-stderr.txt").write_bytes(completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError(f"model call {index} failed; no retry")
        events = [json.loads(line) for line in
                  (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        messages = [row["item"]["text"] for row in events
                    if row.get("type") == "item.completed"
                    and row.get("item", {}).get("type") == "agent_message"]
        turns = [row for row in events if row.get("type") == "turn.completed"]
        if len(messages) != 1 or len(turns) != 1:
            raise ValueError("one agent message and one completed turn required")
        typed, correct = parse(messages[0], mode)
        process = json.loads((output / "process.json").read_text(encoding="utf-8"))
        row = {"call": index, "mode": mode, "typed": typed, "correct": correct,
               "usage": turns[0]["usage"],
               "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}
        (output / "result.json").write_text(json.dumps(row, indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
        results.append(row)
    coordinate = arm_stats([row for row in results if row["mode"] == "coordinate"])
    handle = arm_stats([row for row in results if row["mode"] == "handle"])
    gate = {
        "correct_4_of_4": len(results) == 4 and all(row["correct"] for row in results),
        "within_arm_reported_input_range_at_most_128":
            coordinate["reported_range"] <= 128 and handle["reported_range"] <= 128,
        "handle_reported_input_mean_lower":
            handle["reported_mean"] < coordinate["reported_mean"],
        "handle_derived_uncached_input_mean_lower":
            handle["derived_uncached_mean"] < coordinate["derived_uncached_mean"],
    }
    gate["passed"] = all(gate.values())
    report = {"results": results, "arms": {"coordinate": coordinate, "handle": handle},
              "promotion_gate": gate}
    (ROOT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
