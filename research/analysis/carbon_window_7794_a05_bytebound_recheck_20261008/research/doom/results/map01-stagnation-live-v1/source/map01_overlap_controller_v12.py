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

from map01_stagnation_v1 import descriptor, find_revisit, sustained_revisit

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
    threads = [row["thread_id"] for row in events if row.get("type") == "thread.started"]
    if len(messages) != 1 or len(turns) != 1 or len(threads) != 1:
        raise RuntimeError("one model message and completed turn required")
    return json.loads(messages[0]), turns[0]["usage"], threads[0]


def model_call(root, image, session_id, visual_memory):
    prompt = root / "prompt.txt"
    prompt.write_text("Select the next bounded MAP01 action from the new temporal sheet.\n"
                      + "Local visual memory: " + json.dumps(visual_memory,separators=(",",":")) + "\n")
    output = root / "model"
    command = [WINDOWS_PYTHON, win(HERE / "map01_persistent_model_runner_v1.py"),
               NODE, CLI, win(prompt), win(REPO), win(output), win(image),
               win(HERE / "map01_motor_responder_v2.txt"),
               win(HERE / "map01_motor_schema_v1.json"), session_id or "-"]
    started = time.perf_counter_ns()
    completed = subprocess.run(command, capture_output=True, timeout=90)
    (root / "runner-stdout.txt").write_bytes(completed.stdout)
    (root / "runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode:
        raise RuntimeError("model call failed; no retry")
    action, usage, observed_session_id = parse_message(output)
    elapsed = time.perf_counter_ns() - started
    if action["state"] == "active" and not action["commands"]:
        raise ValueError("active state requires a motor command")
    return action, usage, elapsed, observed_session_id


def compile_commands(commands):
    extents={"pulse":0,"short":1,"medium":2,"long":3}
    table={
      "turn_left":(["Left"],[100,180,300,450]),"turn_right":(["Right"],[100,180,300,450]),
      "forward":(["Up","Shift_L"],[180,350,600,900]),"backward":(["Down"],[180,300,500,750]),
      "strafe_left":(["a"],[180,350,600,850]),"strafe_right":(["d"],[180,350,600,850]),
      "use":(["e"],[80,120,180,250]),"fire":(["space"],[100,180,300,450]),
      "advance_fire":(["Up","Shift_L","space"],[180,350,600,900]),
      "retreat_fire":(["Down","space"],[180,300,500,750])}
    steps=[]
    for command in commands:
        keys,durations=table[command["action"]]
        steps.append({"op":"hold","keys":keys,"duration_ms":durations[extents[command["extent"]]]})
    return steps


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
    parser.add_argument("--session-span", type=int, default=4)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = args.out / "runtime"
    process = subprocess.Popen([sys.executable, str(HERE / "session_map01_v6.py"),
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
            try:
                row = incoming.get(timeout=min(.25,max(.1,end-time.monotonic())))
            except queue.Empty:
                if process.poll() is not None:
                    detail=process.stderr.read().strip()
                    raise RuntimeError(f"session exited before expected event: {detail}")
                continue
            if row["event"] == "observation": latest = row
            if predicate(row): return row
        raise TimeoutError()
    wait(lambda r:r["event"] == "ready")
    latest = wait(lambda r:r["event"] == "observation")
    decisions=[];model_session_id=None
    visual_history=[];revisit_flags=[]
    for index in range(args.iterations):
        if index and index % args.session_span == 0:
            model_session_id=None
        clock_ns=time.perf_counter_ns(); cover=f"cover-{index}"
        prior_actions=[] if not decisions else [command["action"] for command in decisions[-1]["action"]["commands"]]
        prior_assessment="" if not decisions else decisions[-1]["action"]["assessment"].lower()
        if "retreat_fire" in prior_actions:
            cover_steps=[]
            for _ in range(5):cover_steps.extend([
              {"op":"hold","keys":["Down","space"],"duration_ms":500},
              {"op":"coast","duration_ms":1500,"sample_ms":250}])
        elif "advance_fire" in prior_actions or "fire" in prior_actions:
            cover_steps=[]
            for i in range(5):cover_steps.extend([
              {"op":"hold","keys":["a" if i%2==0 else "d","space"],"duration_ms":500},
              {"op":"coast","duration_ms":1500,"sample_ms":250}])
        elif any(word in prior_assessment for word in ("critical","heavy damage","health is low")):
            cover_steps=[]
            for _ in range(5):cover_steps.extend([
              {"op":"hold","keys":["Down"],"duration_ms":500},
              {"op":"coast","duration_ms":1500,"sample_ms":250}])
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
        current_descriptor=descriptor(source_image)
        visual_revisit=find_revisit(current_descriptor,visual_history)
        visual_history.append(current_descriptor)
        revisit_flags.append(bool(visual_revisit))
        rolling_count=sum(revisit_flags[-5:])
        recent_actions=[command["action"] for row in decisions[-4:]
                        for command in row["action"]["commands"]]
        if sustained_revisit(revisit_flags):
            visual_memory={"status":"sustained_revisit",
              "matched_iteration":visual_revisit["prior_iteration"],
              "revisits_in_last_5":rolling_count,
              "recent_actions":recent_actions[-12:],
              "instruction":"choose a bounded route change that does not repeat this action cycle"}
        elif visual_revisit:
            visual_memory={"status":"isolated_revisit",
              "matched_iteration":visual_revisit["prior_iteration"],
              "revisits_in_last_5":rolling_count}
        else:
            visual_memory={"status":"no_sustained_revisit",
              "revisits_in_last_5":rolling_count}
        image=model_root/"temporal-sheet.png"
        prior=[Path(row["source_image"]) for row in decisions]
        temporal_sheet(prior+[source_image],image)
        model_started_ns=time.perf_counter_ns()
        action,usage,model_ns,observed_session_id=model_call(
            model_root,image,model_session_id,visual_memory)
        if model_session_id is not None and observed_session_id != model_session_id:
            raise RuntimeError("model session identity changed")
        model_session_id=observed_session_id
        model_ended_ns=time.perf_counter_ns()
        process.stdin.write(json.dumps({"op":"cancel","id":cover})+"\n");process.stdin.flush()
        wait(lambda r:r["event"]=="terminal" and r.get("id")==cover)
        if action["state"] != "active":
            decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
              "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"action":action,
              "visual_revisit":visual_revisit,"visual_memory":visual_memory,
              "usage":usage,"model_ns":model_ns,"model_session_id":model_session_id,
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "terminal_candidate":True})
            break
        grounded_capture_ns=next(row["capture_ns"] for row in reversed(all_events)
                                 if row.get("image")==str(source_image))
        fresh_before_plan=dict(latest)
        clock_ns=time.perf_counter_ns(); plan=f"plan-{index}"
        steps=compile_commands(action["commands"])+[{"op":"observe"}]
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
          "visual_revisit":visual_revisit,"visual_memory":visual_memory,
          "compiled_commands":action["commands"],
          "model_session_id":model_session_id,
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
      "model_session_span":args.session_span,
      "model_session_ids":list(dict.fromkeys(row["model_session_id"] for row in decisions)),
      "motor_contract":"semantic commands compiled to <=450ms turns and <=900ms movement",
      "visual_memory_contract":"no forced motor override; planner receives advisory only after >=3 visual revisits in the last 5 decisions",
      "sustained_revisit_advisories":sum(x.get("visual_memory",{}).get("status")=="sustained_revisit" for x in decisions),
      "game_continued_during_model_calls":True,
      "model_wall_seconds":sum(x["model_ns"] for x in decisions)/1e9}
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"iterations":len(decisions),"score":score,
      "model_wall_seconds":report["model_wall_seconds"]},indent=2))

if __name__ == "__main__": main()
