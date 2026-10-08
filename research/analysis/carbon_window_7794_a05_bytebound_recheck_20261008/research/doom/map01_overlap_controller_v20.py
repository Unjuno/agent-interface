"""Pre-formal Luna-low controller with gameplay continuing during inference."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from PIL import Image, ImageDraw

from map01_stagnation_v1 import descriptor, normalized_mae

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


def model_call(root, image, session_id, effect_memory, model, effort):
    prompt = root / "prompt.txt"
    prompt.write_text("Select the next bounded MAP01 action from the new temporal sheet.\n"
                      + "Previous no-visible-effect actions: " + json.dumps(effect_memory,separators=(",",":")) + "\n")
    output = root / "model"
    command = [WINDOWS_PYTHON, win(HERE / "map01_persistent_model_runner_v2.py"),
               NODE, CLI, win(prompt), win(REPO), win(output), win(image),
               win(HERE / "map01_motor_responder_v6.txt"),
               win(HERE / "map01_cover_policy_schema_v1.json"), session_id or "-", model, effort]
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
    if action["state"] == "active" and not action["next_cover"]:
        raise ValueError("active state requires a next-inference cover policy")
    if action["state"] != "active" and (action["commands"] or action["contingencies"] or action["next_cover"]):
        raise ValueError("terminal state requires empty commands, contingencies, and next_cover")
    indices=[row["after_command"] for row in action["contingencies"]]
    if len(indices)!=len(set(indices)) or any(index>=len(action["commands"]) for index in indices):
        raise ValueError("contingency indices must be unique primary command indices")
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


def compile_cover(commands):
    coast_ms={"pulse":500,"short":1500,"medium":3000,"long":5000}
    if any(command["action"]=="coast" for command in commands):
        if len(commands)!=1 or commands[0]["action"]!="coast":
            raise ValueError("coast must be the only cover command")
        duration=coast_ms[commands[0]["extent"]]
        steps=[];total=0
        while total<10000:
            part=min(duration,10000-total)
            steps.append({"op":"coast","duration_ms":part,"sample_ms":250})
            total+=part
        return steps
    holds=compile_commands(commands)
    repetitions=min(8,16//(len(holds)+1))
    while repetitions>0 and sum(step["duration_ms"] for step in holds)*repetitions>=10000:
        repetitions-=1
    if repetitions<1:
        raise ValueError("cover holds cannot fit the bounded ten-second policy")
    hold_total=sum(step["duration_ms"] for step in holds)*repetitions
    coast_total=10000-hold_total
    base_coast=coast_total//repetitions
    remainder=coast_total%repetitions
    if base_coast<50 or base_coast>5000:
        raise ValueError("cover cycle cannot satisfy coast bounds")
    steps=[]
    for cycle in range(repetitions):
        steps.extend(dict(step) for step in holds)
        duration=base_coast+(1 if cycle<remainder else 0)
        steps.append({"op":"coast","duration_ms":duration,"sample_ms":250})
    if len(steps)>16 or sum(step["duration_ms"] for step in steps)!=10000:
        raise AssertionError("cover compiler bounds")
    return steps


def effect_receipts(commands, before, observations, accepted_ns):
    previous=descriptor(Path(before["image"]));receipts=[]
    for index,command in enumerate(commands):
        samples=[row for row in observations if row["step"]==index]
        if not samples:
            raise RuntimeError(f"hold step {index} produced no effect observation")
        observation=samples[-1]
        current=descriptor(Path(observation["image"]));mae=normalized_mae(previous,current)
        receipts.append({"action":command["action"],"extent":command["extent"],
          "result":"no_visible_effect" if mae<=0.015 else "visible_change",
          "normalized_mae":mae,"no_visible_effect_threshold_lte":0.015,
          "after_sequence":observation["sequence"],
          "effect_observed_ns":observation["capture_ns"],
          "samples":len(samples),
          "plan_accept_to_first_capture_ms":(samples[0]["capture_ns"]-accepted_ns)/1e6,
          "plan_accept_to_last_capture_ms":(observation["capture_ns"]-accepted_ns)/1e6,
          "capture_ms_total":sum(row["capture_ms"] for row in samples),
          "scope":"viewport pixels only"})
        previous=current
    return receipts


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
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", choices=("low","medium","high","xhigh","max","ultra"), required=True)
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
    program_admissions=0
    for index in range(args.iterations):
        if index and index % args.session_span == 0:
            model_session_id=None
        clock_ns=time.perf_counter_ns(); cover=f"cover-{index}"
        if decisions and decisions[-1]["action"]["state"]=="active":
            cover_semantic=decisions[-1]["action"]["next_cover"]
            cover_policy_source_iteration=decisions[-1]["iteration"]
        else:
            cover_semantic=[{"action":"coast","extent":"long"}]
            cover_policy_source_iteration=None
        cover_steps=compile_cover(cover_semantic)
        cover_ids=[];cover_terminals=[];cover_renewal_gaps_ms=[]
        def submit_cover(identifier):
            nonlocal clock_ns
            clock_ns=time.perf_counter_ns()
            command={"op":"submit","id":identifier,"expected_sequence":latest["sequence"],
              "valid_until_ns":clock_ns+25_000_000_000,"steps":cover_steps}
            process.stdin.write(json.dumps(command)+"\n");process.stdin.flush()
            accepted=wait(lambda r:r["event"] in ("accepted","rejected") and
                          (r.get("id")==identifier or r["event"]=="rejected"))
            if accepted["event"]!="accepted":raise RuntimeError(accepted)
            cover_ids.append(identifier);return accepted
        submit_cover(cover)
        model_root=args.out/f"decision-{index}"
        model_root.mkdir()
        source_image=Path(latest["image"])
        prior_receipts=[] if not decisions else decisions[-1].get("effect_receipts",[])
        effect_memory=[row["action"] for row in prior_receipts
                       if row["result"]=="no_visible_effect"]
        image=model_root/"temporal-sheet.png"
        prior=[Path(row["source_image"]) for row in decisions]
        temporal_sheet(prior+[source_image],image)
        model_started_ns=time.perf_counter_ns()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(model_call,model_root,image,model_session_id,effect_memory,
                               args.model,args.effort)
            current_cover=cover
            current_terminal=None
            while not future.done():
                try:
                    current_terminal=wait(lambda r:r["event"]=="terminal" and
                                          r.get("id")==current_cover,timeout=.5)
                except TimeoutError:
                    continue
                cover_terminals.append(current_terminal)
                if future.done():break
                next_cover=f"cover-{index}-renew-{len(cover_ids)}"
                next_accepted=submit_cover(next_cover)
                cover_renewal_gaps_ms.append((next_accepted["accepted_ns"]-
                    current_terminal["terminal_ns"])/1e6)
                current_cover=next_cover;current_terminal=None
            action,usage,model_ns,observed_session_id=future.result()
        if model_session_id is not None and observed_session_id != model_session_id:
            raise RuntimeError("model session identity changed")
        model_session_id=observed_session_id
        model_ended_ns=time.perf_counter_ns()
        if current_terminal is None:
            process.stdin.write(json.dumps({"op":"cancel","id":current_cover})+"\n");process.stdin.flush()
            current_terminal=wait(lambda r:r["event"]=="terminal" and r.get("id")==current_cover)
            cover_terminals.append(current_terminal)
        if action["state"] != "active":
            decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
              "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"action":action,
              "effect_memory":effect_memory,
              "usage":usage,"model_ns":model_ns,"model_session_id":model_session_id,
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
              "cover_renewal_gaps_ms":cover_renewal_gaps_ms,
              "cover_policy":cover_semantic,"cover_policy_source_iteration":cover_policy_source_iteration,
              "terminal_candidate":True})
            break
        grounded_capture_ns=next(row["capture_ns"] for row in reversed(all_events)
                                 if row.get("image")==str(source_image))
        fresh_before_plan=dict(latest)
        trace=[]
        def execute_segment(identifier,commands,role,command_indices):
            nonlocal program_admissions
            before=dict(latest);event_start=len(all_events);clock_ns=time.perf_counter_ns()
            process.stdin.write(json.dumps({"op":"submit","id":identifier,
              "expected_sequence":latest["sequence"],"valid_until_ns":clock_ns+25_000_000_000,
              "steps":compile_commands(commands)})+"\n");process.stdin.flush()
            accepted=wait(lambda r:r["event"] in ("accepted","rejected") and
                          (r.get("id")==identifier or r["event"]=="rejected"))
            if accepted["event"]!="accepted":raise RuntimeError(accepted)
            program_admissions+=1
            terminal=wait(lambda r:r["event"]=="terminal" and r.get("id")==identifier)
            if terminal["status"]!="completed":raise RuntimeError(terminal)
            observations=[row for row in all_events[event_start:]
                          if row.get("event")=="observation" and row.get("id")==identifier]
            receipts=effect_receipts(commands,before,observations,accepted["accepted_ns"])
            records=[]
            for local_index,(command,receipt) in enumerate(zip(commands,receipts)):
                samples=[row for row in observations if row["step"]==local_index]
                record={"id":identifier,"role":role,
                  "command_index":command_indices[local_index],"command":command,
                  "accepted_ns":accepted["accepted_ns"],
                  "terminal_ns":terminal["terminal_ns"],"receipt":receipt,
                  "observation_samples":len(samples),
                  "observation_capture_ms":sum(row["capture_ms"] for row in samples)}
                trace.append(record);records.append(record)
            return records
        contingencies={row["after_command"]:row for row in action["contingencies"]}
        branch=None;first_accepted=None
        boundaries=sorted(contingencies)
        if not boundaries or boundaries[-1] != len(action["commands"])-1:
            boundaries.append(len(action["commands"])-1)
        segment_start=0
        for segment_end in boundaries:
            segment_commands=action["commands"][segment_start:segment_end+1]
            records=execute_segment(f"plan-{index}-primary-{segment_start}-{segment_end}",
                segment_commands,"primary",list(range(segment_start,segment_end+1)))
            if first_accepted is None:first_accepted=records[0]["accepted_ns"]
            contingency=contingencies.get(segment_end)
            trigger=records[-1]
            if trigger["receipt"]["result"]=="no_visible_effect" and contingency:
                branch={"after_command":segment_end,"condition":"no_visible_effect",
                  "skipped_primary_commands":len(action["commands"])-segment_end-1,
                  "fallback_commands":contingency["commands"],"latency_ms":None}
                fallback_records=execute_segment(
                    f"plan-{index}-fallback-{segment_end}",contingency["commands"],
                    "fallback",list(range(len(contingency["commands"]))))
                branch["latency_ms"]=(fallback_records[0]["accepted_ns"]-
                    trigger["receipt"]["effect_observed_ns"])/1e6
                break
            segment_start=segment_end+1
        receipts=[row["receipt"] for row in trace]
        decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
          "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
          "action":action,"usage":usage,"model_ns":model_ns,
          "effect_memory":effect_memory,"effect_receipts":receipts,
          "effect_observation_samples":sum(row["observation_samples"] for row in trace),
          "effect_observation_capture_ms":sum(row["observation_capture_ms"] for row in trace),
          "execution_trace":trace,"contingency_branch":branch,
          "compiled_commands":[row["command"] for row in trace],
          "model_session_id":model_session_id,
          "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
          "model_image_to_plan_accept_ns":first_accepted-grounded_capture_ns,
          "fresh_observation_to_plan_accept_ns":first_accepted-fresh_before_plan["capture_ns"],
          "fresh_sequence_at_plan":fresh_before_plan["sequence"],
          "cover_terminal_before_plan":True,
          "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
          "cover_renewal_gaps_ms":cover_renewal_gaps_ms,
          "cover_policy":cover_semantic,"cover_policy_source_iteration":cover_policy_source_iteration,
          "plan_terminal":"completed"})
    process.stdin.write('{"op":"finish"}\n');process.stdin.flush()
    score=wait(lambda r:r["event"]=="post_control_score")
    process.wait(timeout=20)
    (args.out/"stderr.txt").write_text(process.stderr.read())
    report={"claim":"pre-formal overlapping inference feasibility", "model":args.model,
      "effort":args.effort,"iterations":len(decisions),"decisions":decisions,"score":score,
      "model_session_span":args.session_span,
      "model_session_ids":list(dict.fromkeys(row["model_session_id"] for row in decisions)),
      "motor_contract":"semantic commands compiled to <=450ms turns and <=900ms movement",
      "effect_receipt_contract":"reuse the final exact sample already emitted by each hold; retain full local receipts but expose only no-visible-effect action names to the model",
      "effect_receipt_extra_steps":0,
      "contingency_contract":"preplanned no-visible-effect fallback skips the primary tail and runs without another model call",
      "contingencies_authored":sum(len(x["action"].get("contingencies",[])) for x in decisions),
      "contingency_branches_taken":sum(x.get("contingency_branch") is not None for x in decisions),
      "contingency_branch_latency_ms":[x["contingency_branch"]["latency_ms"] for x in decisions if x.get("contingency_branch")],
      "program_admissions":program_admissions,
      "extra_program_admissions_vs_one_bundle":program_admissions-sum(x["action"]["state"]=="active" for x in decisions),
      "effect_receipt_commands":sum(len(x.get("effect_receipts",[])) for x in decisions),
      "effect_observation_samples":sum(x.get("effect_observation_samples",0) for x in decisions),
      "effect_observation_capture_ms":sum(x.get("effect_observation_capture_ms",0) for x in decisions),
      "game_continued_during_model_calls":True,
      "cover_programs":sum(len(x.get("cover_program_ids",[])) for x in decisions),
      "cover_renewals":sum(x.get("cover_renewals",0) for x in decisions),
      "cover_renewal_gaps_ms":[gap for x in decisions for gap in x.get("cover_renewal_gaps_ms",[])],
      "model_authored_cover_policies":sum(x["action"]["state"]=="active" for x in decisions),
      "model_wall_seconds":sum(x["model_ns"] for x in decisions)/1e9}
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"iterations":len(decisions),"score":score,
      "model_wall_seconds":report["model_wall_seconds"]},indent=2))

if __name__ == "__main__": main()
