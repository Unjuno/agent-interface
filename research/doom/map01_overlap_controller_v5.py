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
from PIL import Image, ImageDraw

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
               win(HERE / "map01_action_responder_v2.txt"), win(HERE / "map01_action_schema_v1.json")]
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


def temporal_sheet(sources, target):
    """Pack four recent game windows into the same 642x502 model-image extent."""
    chosen = ([sources[0]] * (4-len(sources)) + sources)[-4:]
    sheet = Image.new("RGB", (642, 502), "black")
    draw = ImageDraw.Draw(sheet)
    for index, source in enumerate(chosen):
        with Image.open(source) as frame:
            crop = frame.crop((320, 162, 962, 663)).resize((320, 250))
        x=(index%2)*321; y=(index//2)*251
        sheet.paste(crop,(x,y))
        draw.text((x+4,y+4),str(index+1),fill="white",stroke_width=1,stroke_fill="black")
    sheet.save(target,optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--seed", type=int, default=990605)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = args.out / "runtime"
    process = subprocess.Popen([sys.executable, str(HERE / "session_map01_v4.py"),
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
        prior_attacked=bool(decisions and any("space" in step["keys"]
                            for step in decisions[-1]["action"]["steps"]))
        if prior_attacked:
            cover_steps=[{"op":"hold","keys":["space"],"duration_ms":1000},
                         {"op":"coast","duration_ms":4000,"sample_ms":250},
                         {"op":"hold","keys":["space"],"duration_ms":1000},
                         {"op":"coast","duration_ms":4000,"sample_ms":250}]
        else:
            cover_steps=[{"op":"coast","duration_ms":5000,"sample_ms":250},
                         {"op":"coast","duration_ms":5000,"sample_ms":250}]
        cover_cmd={"op":"submit","id":cover,"expected_sequence":latest["sequence"],
          "valid_until_ns":clock_ns+25_000_000_000,
          "steps":cover_steps}
        process.stdin.write(json.dumps(cover_cmd)+"\n");process.stdin.flush()
        wait(lambda r:r["event"]=="accepted" and r.get("id")==cover)
        model_root=args.out/f"decision-{index}"
        model_root.mkdir()
        source_image=Path(latest["image"])
        image=model_root/"temporal-sheet.png"
        prior=[Path(row["source_image"]) for row in decisions]
        temporal_sheet(prior+[source_image],image)
        model_started_ns=time.perf_counter_ns()
        history=[{"assessment":row["action"]["assessment"],
                  "steps":row["action"]["steps"]} for row in decisions]
        action,usage,model_ns=model_call(model_root,image,history)
        model_ended_ns=time.perf_counter_ns()
        process.stdin.write(json.dumps({"op":"cancel","id":cover})+"\n");process.stdin.flush()
        wait(lambda r:r["event"]=="terminal" and r.get("id")==cover)
        grounded_capture_ns=next(row["capture_ns"] for row in reversed(all_events)
                                 if row.get("image")==str(source_image))
        fresh_before_plan=dict(latest)
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
          "model_image_to_plan_accept_ns":accepted["accepted_ns"]-grounded_capture_ns,
          "fresh_observation_to_plan_accept_ns":accepted["accepted_ns"]-fresh_before_plan["capture_ns"],
          "fresh_sequence_at_plan":fresh_before_plan["sequence"],
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
