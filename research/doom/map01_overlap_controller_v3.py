"""Pre-formal Luna-low controller with gameplay continuing during inference."""
import argparse
import hashlib
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WINDOWS_PYTHON = "/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe"
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"


def win(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          check=True, capture_output=True, text=True).stdout.strip()


def parse_message(root):
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    messages = [row["item"]["text"] for row in events if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    if len(messages) != 1 or len(turns) != 1:
        raise RuntimeError("one model message and completed turn required")
    return json.loads(messages[0]), turns[0]["usage"]


def model_call(root, image, history):
    prompt = root / "prompt.txt"
    compact = json.dumps(history[-3:], separators=(",", ":"))
    prompt.write_text("Select the next bounded MAP01 action from this current game screen. "
                      "Recent prior visual decisions, oldest first: " + compact + "\n")
    output = root / "model"
    command = [WINDOWS_PYTHON, win(REPO / "research/live_control/target_handle_model_runner_v2.py"),
               NODE, CLI, win(prompt), win(REPO), win(output), "coordinate", win(image),
               win(HERE / "map01_action_responder_v1.txt"), win(HERE / "map01_action_schema_v1.json")]
    started = time.perf_counter_ns()
    completed = subprocess.run(command, capture_output=True, timeout=90)
    (root / "runner-stdout.txt").write_bytes(completed.stdout)
    (root / "runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode:
        raise RuntimeError("model call failed; no retry")
    action, usage = parse_message(output)
    elapsed = time.perf_counter_ns() - started
    total = sum(step["duration_ms"] for step in action["steps"])
    if total > 6000:
        raise ValueError("model duration exceeds controller limit")
    return action, usage, elapsed


def game_crop(source, target):
    """Strip the stable black Xvfb surround while retaining title, viewport and HUD."""
    with Image.open(source) as frame:
        # The private 1280x720 desktop centers the 640x480 game window at this box.
        frame.crop((320, 162, 962, 663)).save(target, optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--seed", type=int, default=990605)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = args.out / "runtime"
    process = subprocess.Popen([sys.executable, str(HERE / "session_map01_v3.py"),
        "--out", str(runtime), "--seed", str(args.seed), "--timeout-seconds", "600"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1)
    incoming = queue.Queue()
    all_events = []
    def reader():
        for line in process.stdout:
            row = json.loads(line); all_events.append(row); incoming.put(row)
    threading.Thread(target=reader, daemon=True).start()
    latest = None
    def wait(predicate, timeout=40):
        nonlocal latest
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            row = incoming.get(timeout=max(.1, end-time.monotonic()))
            if row["event"] == "observation": latest = row
            if predicate(row): return row
        raise TimeoutError()
    wait(lambda r:r["event"] == "ready")
    latest = wait(lambda r:r["event"] == "observation")
    decisions=[]
    for index in range(args.iterations):
        clock_ns=time.perf_counter_ns(); cover=f"cover-{index}"
        # Eight short symmetric pairs keep input live during an approximately
        # eight-second call without intentionally translating to a new area.
        cover_steps=[]
        for _ in range(8):
            cover_steps.extend([
                {"op":"hold","keys":["a","Left"],"duration_ms":625},
                {"op":"hold","keys":["d","Right"],"duration_ms":625}])
        cover_cmd={"op":"submit","id":cover,"expected_sequence":latest["sequence"],
          "valid_until_ns":clock_ns+25_000_000_000,
          "steps":cover_steps}
        process.stdin.write(json.dumps(cover_cmd)+"\n");process.stdin.flush()
        wait(lambda r:r["event"]=="accepted" and r.get("id")==cover)
        model_root=args.out/f"decision-{index}"
        model_root.mkdir()
        source_image=Path(latest["image"])
        image=model_root/"game-window.png"
        game_crop(source_image,image)
        model_started_ns=time.perf_counter_ns()
        history=[{"assessment":row["action"]["assessment"],
                  "steps":row["action"]["steps"]} for row in decisions]
        action,usage,model_ns=model_call(model_root,image,history)
        model_ended_ns=time.perf_counter_ns()
        process.stdin.write(json.dumps({"op":"cancel","id":cover})+"\n");process.stdin.flush()
        wait(lambda r:r["event"]=="terminal" and r.get("id")==cover)
        clock_ns=time.perf_counter_ns(); plan=f"plan-{index}"
        steps=[{"op":"hold","keys":step["keys"],"duration_ms":step["duration_ms"]}
               for step in action["steps"]]+[{"op":"observe"}]
        process.stdin.write(json.dumps({"op":"submit","id":plan,
          "expected_sequence":latest["sequence"],"valid_until_ns":clock_ns+25_000_000_000,
          "steps":steps})+"\n");process.stdin.flush()
        accepted=wait(lambda r:r["event"] in ("accepted","rejected") and
                      (r.get("id")==plan or r["event"]=="rejected"))
        if accepted["event"]!="accepted": raise RuntimeError(accepted)
        terminal=wait(lambda r:r["event"]=="terminal" and r.get("id")==plan)
        decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
          "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
          "action":action,"usage":usage,"model_ns":model_ns,
          "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
          "observation_to_plan_accept_ns":accepted["accepted_ns"]-latest["capture_ns"],
          "cover_terminal_before_plan":True,
          "plan_terminal":terminal["status"]})
    process.stdin.write('{"op":"finish"}\n');process.stdin.flush()
    score=wait(lambda r:r["event"]=="post_control_score")
    process.wait(timeout=20)
    (args.out/"stderr.txt").write_text(process.stderr.read())
    report={"claim":"pre-formal overlapping inference feasibility", "model":"gpt-5.6-luna",
      "effort":"low","iterations":len(decisions),"decisions":decisions,"score":score,
      "game_continued_during_model_calls":True,
      "model_wall_seconds":sum(x["model_ns"] for x in decisions)/1e9}
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"iterations":len(decisions),"score":score,
      "model_wall_seconds":report["model_wall_seconds"]},indent=2))

if __name__ == "__main__": main()
