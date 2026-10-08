"""MAP01 controller with planner-authored typed cover validity."""
import argparse
import atexit
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
sys.path.insert(0, str(HERE.parent / "live_control"))
from doom_hud_signal_v1 import DoomStatusNumberReader
from observable_signal_guard_v1 import ObservableSignalGuard, ObservableSignalPolicyMonitor
from codex_app_server_client_v2 import CodexAppServerClient
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
NODE = "/mnt/c/Program Files/nodejs/node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
DISABLED_FEATURES = [
    "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
    "computer_use", "in_app_browser", "code_mode", "code_mode_host",
]
DISABLED_MCPS = ["blender", "chrome-devtools", "node_repl", "playwright", "puppeteer"]
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
MAX_AUTHORED_HEALTH_LOSS = 20


def reusable_cover(decisions):
    if (decisions and not decisions[-1].get("model_action_discarded") and
            decisions[-1]["action"]["state"] == "active"):
        validity = decisions[-1]["action"]["next_cover_validity"]
        return (decisions[-1]["action"]["next_cover"], validity[0],
                decisions[-1]["iteration"])
    return [], None, None


def guard_spec(validity, source_signal, index):
    return {
        "op": "observable_signal_guard",
        "guard_id": f"map01-{index}",
        "source_sequence": source_signal["sequence"],
        "signal_id": "health",
        "source_value": source_signal["value"],
        "hard_minimum": source_signal["value"] if validity is None else validity["hard_minimum"],
        "max_source_age_ms": 30000 if validity is None else validity["max_source_age_ms"],
        "on_soft_change": "preserve_existing_policy",
        "on_hard_change": "needs_decision",
        "on_unknown": "needs_decision",
    }


def build_cover_monitor(reader, source_observation, authored_validity, index):
    source_signal = reader.read(source_observation)
    if source_signal["status"] != "observed" or source_signal["value"] < 1:
        raise RuntimeError("cover validity source health unavailable")
    if authored_validity is not None:
        expected = {"signal_id", "hard_minimum", "max_source_age_ms"}
        if (type(authored_validity) is not dict or set(authored_validity) != expected or
                authored_validity["signal_id"] != "health" or
                type(authored_validity["hard_minimum"]) is not int or
                not 1 <= authored_validity["hard_minimum"] <= 200 or
                type(authored_validity["max_source_age_ms"]) is not int or
                not 100 <= authored_validity["max_source_age_ms"] <= 30000):
            raise ValueError("exact typed health validity required")
    if authored_validity is None:
        admission_status = "admitted"
    elif authored_validity["hard_minimum"] > source_signal["value"]:
        admission_status = "rejected_source_below_hard_minimum"
    elif authored_validity["hard_minimum"] < max(
            1, source_signal["value"] - MAX_AUTHORED_HEALTH_LOSS):
        admission_status = "rejected_health_loss_envelope_too_wide"
    else:
        admission_status = "admitted"
    admitted = admission_status == "admitted"
    effective = authored_validity if admitted else None
    spec = guard_spec(effective, source_signal, index)
    guard = ObservableSignalGuard(spec, source_signal, source_signal["binding"])
    receipt = {
        "status": admission_status,
        "authored": authored_validity,
        "effective": {"signal_id": "health", "hard_minimum": spec["hard_minimum"],
                      "max_source_age_ms": spec["max_source_age_ms"]},
        "source_signal": source_signal,
        "grants_input_authority": False,
    }
    return ObservableSignalPolicyMonitor(guard, reader), receipt


def cancel_invalidated_cover(planner, planner_handle, process, wait, cover_id):
    planner_interrupt = planner.interrupt(planner_handle)
    process.stdin.write(json.dumps({"op": "cancel", "id": cover_id}) + "\n")
    process.stdin.flush()
    terminal = wait(lambda row: row["event"] == "terminal" and row.get("id") == cover_id)
    release = terminal.get("release", {})
    if (terminal.get("status") != "cancelled" or release.get("verified") is not True or
            release.get("buttons_down") != [] or release.get("keys_down") != []):
        raise RuntimeError("invalidated cover did not verify empty release")
    return planner_interrupt, terminal


def admitted_cover_commands(commands, validity_admission):
    if validity_admission.get("status") != "admitted":
        return []
    return list(commands)


def win(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          check=True, capture_output=True, text=True).stdout.strip()


def app_server_command():
    command = [NODE, CLI, "app-server", "--stdio"]
    for feature in DISABLED_FEATURES:
        command += ["--disable", feature]
    for name in DISABLED_MCPS:
        command += ["-c", f"mcp_servers.{name}.enabled=false"]
    return command


def session_command(args, runtime):
    return [sys.executable, str(HERE / "session_map01_v7.py"),
            "--out", str(runtime), "--seed", str(args.seed),
            "--timeout-seconds", "600", "--skill", "1",
            "--load-fixture-manifest", str(args.load_fixture_manifest.resolve())]


def validate_action(action):
    if action["state"] == "active" and not action["commands"]:
        raise ValueError("active state requires a motor command")
    if action["state"] == "active" and len(action["next_cover_validity"]) != 1:
        raise ValueError("active state requires one next_cover_validity")
    if action["state"] != "active" and (action["commands"] or action["contingencies"] or
            action["next_cover"] or action["next_cover_validity"]):
        raise ValueError("terminal state requires empty commands, contingencies, cover and validity")
    indices=[row["after_command"] for row in action["contingencies"]]
    if len(indices)!=len(set(indices)) or any(index>=len(action["commands"]) for index in indices):
        raise ValueError("contingency indices must be unique primary command indices")


def begin_model_turn(planner, root, image, effect_memory, source_health, output_schema):
    prompt_text = ("Select the next bounded MAP01 action from the new temporal sheet.\n"
                   + f"Current locally verified health: {source_health}.\n"
                   + "Previous no-visible-effect actions: "
                   + json.dumps(effect_memory, separators=(",", ":")) + "\n")
    (root / "prompt.txt").write_text(prompt_text)
    return planner.begin_turn(prompt_text, output_schema=output_schema,
                              image_path=win(image))


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
    if not commands:
        return [{"op":"coast","duration_ms":5000,"sample_ms":250},
                {"op":"coast","duration_ms":5000,"sample_ms":250}]
    holds=compile_commands(commands)
    repetitions=min(8,16//(len(holds)+1))
    while repetitions>0:
        candidate_hold=sum(step["duration_ms"] for step in holds)*repetitions
        candidate_coast=(10000-candidate_hold)//repetitions
        if candidate_hold<10000 and 50<=candidate_coast<=5000:
            break
        repetitions-=1
    if repetitions<1:
        raise ValueError("cover holds cannot fit the bounded ten-second policy")
    hold_total=sum(step["duration_ms"] for step in holds)*repetitions
    coast_total=10000-hold_total
    base_coast=coast_total//repetitions
    remainder=coast_total%repetitions
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
    parser.add_argument("--load-fixture-manifest", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    planner_client = CodexAppServerClient(
        app_server_command(), cwd=REPO,
        journal_path=args.out / "planner-protocol.jsonl")
    atexit.register(planner_client.close)
    planner_client.initialize()
    planner = PersistentPlannerAdapter(
        planner_client, model=args.model, effort=args.effort, cwd=win(REPO),
        base_instructions=(HERE / "map01_motor_responder_v8.txt").read_text())
    planner.start_session()
    output_schema = json.loads((HERE / "map01_cover_policy_schema_v4.json").read_text())
    signal_reader = DoomStatusNumberReader(WAD)
    runtime = args.out / "runtime"
    process = subprocess.Popen(session_command(args, runtime),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1)
    incoming = queue.Queue()
    all_events = []
    def reader():
        for line in process.stdout:
            row = json.loads(line); all_events.append(row); incoming.put(row)
    threading.Thread(target=reader, daemon=True).start()
    latest = None
    def wait(predicate, timeout=40, observation_monitor=None):
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
            if row["event"] == "observation":
                latest = row
                if observation_monitor is not None:
                    invalidation = observation_monitor.observe(row)
                    if invalidation is not None:
                        return {"event":"policy_invalidation",
                                "invalidation":invalidation}
            if predicate(row): return row
        raise TimeoutError()
    ready = wait(lambda r:r["event"] == "ready")
    runtime_fixture = ready.get("fixture")
    if runtime_fixture is None:
        raise RuntimeError("v28 requires a loaded fixture receipt")
    latest = wait(lambda r:r["event"] == "observation")
    decisions=[];model_session_id=planner.thread_id
    program_admissions=0
    for index in range(args.iterations):
        if index and index % args.session_span == 0:
            planner.start_session()
            model_session_id=planner.thread_id
        clock_ns=time.perf_counter_ns(); cover=f"cover-{index}"
        cover_semantic, cover_validity_semantic, cover_policy_source_iteration = reusable_cover(decisions)
        validity_monitor, validity_admission = build_cover_monitor(
            signal_reader, latest, cover_validity_semantic, index)
        cover_semantic = admitted_cover_commands(cover_semantic, validity_admission)
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
        invalidation_monitor=validity_monitor
        invalidation=None
        prior_receipts=[] if not decisions else decisions[-1].get("effect_receipts",[])
        effect_memory=[row["action"] for row in prior_receipts
                       if row["result"]=="no_visible_effect"]
        image=model_root/"temporal-sheet.png"
        prior=[Path(row["source_image"]) for row in decisions]
        temporal_sheet(prior+[source_image],image)
        model_started_ns=time.perf_counter_ns()
        planner_handle=begin_model_turn(
            planner,model_root,image,effect_memory,
            validity_admission["source_signal"]["value"],output_schema)
        planner_interrupt=None
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(planner.await_turn,planner_handle,90)
            current_cover=cover
            current_terminal=None
            while not future.done():
                try:
                    boundary=wait(lambda r:r["event"]=="terminal" and
                                  r.get("id")==current_cover,timeout=.1,
                                  observation_monitor=invalidation_monitor)
                except TimeoutError:
                    continue
                if boundary["event"] == "policy_invalidation":
                    invalidation=boundary["invalidation"]
                    planner_interrupt,current_terminal=cancel_invalidated_cover(
                        planner,planner_handle,process,wait,current_cover)
                    cover_terminals.append(current_terminal)
                    break
                current_terminal=boundary
                cover_terminals.append(current_terminal)
                if future.done():break
                next_cover=f"cover-{index}-renew-{len(cover_ids)}"
                next_accepted=submit_cover(next_cover)
                cover_renewal_gaps_ms.append((next_accepted["accepted_ns"]-
                    current_terminal["terminal_ns"])/1e6)
                current_cover=next_cover;current_terminal=None
            planner_result=future.result()
        model_ended_ns=time.perf_counter_ns()
        model_ns=model_ended_ns-model_started_ns
        action=planner_result.answer
        usage=planner_result.usage
        observed_session_id=planner_result.handle.thread_id
        if model_session_id is not None and observed_session_id != model_session_id:
            raise RuntimeError("model session identity changed")
        model_session_id=observed_session_id
        if current_terminal is None:
            process.stdin.write(json.dumps({"op":"cancel","id":current_cover})+"\n");process.stdin.flush()
            while current_terminal is None:
                boundary=wait(lambda r:r["event"]=="terminal" and r.get("id")==current_cover,
                              observation_monitor=None if invalidation else invalidation_monitor)
                if boundary["event"] == "policy_invalidation":
                    invalidation=boundary["invalidation"]
                    planner_interrupt=planner.interrupt(planner_handle)
                else:
                    current_terminal=boundary
            cover_terminals.append(current_terminal)
        if invalidation is not None:
            decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
              "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"action":action,
              "effect_memory":effect_memory,"usage":usage,"model_ns":model_ns,
              "model_session_id":model_session_id,
              "planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,
              "planner_answer_eligible":planner_result.answer_eligible,
              "planner_cancellation_requested":planner_result.cancellation_requested,
              "planner_interrupt":planner_interrupt,
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
              "cover_renewal_gaps_ms":cover_renewal_gaps_ms,
              "cover_policy":cover_semantic,"cover_policy_source_iteration":cover_policy_source_iteration,
              "cover_validity_admission":validity_admission,
              "cover_validity_soft_events":invalidation_monitor.soft_event_count,
              "cover_validity_latest_soft_event":invalidation_monitor.latest_soft_event,
              "policy_invalidation":invalidation,"model_action_discarded":True,
              "discard_reason":"policy_dependency_invalidated",
              "cover_terminal_before_plan":True,"plan_terminal":"not_admitted"})
            continue
        if not planner_result.answer_eligible:
            raise RuntimeError(f"planner answer ineligible: {planner_result.error}")
        validate_action(action)
        if action["state"] != "active":
            decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
              "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"action":action,
              "effect_memory":effect_memory,
              "usage":usage,"model_ns":model_ns,"model_session_id":model_session_id,
              "planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,
              "planner_answer_eligible":planner_result.answer_eligible,
              "planner_cancellation_requested":planner_result.cancellation_requested,
              "planner_interrupt":planner_interrupt,
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
              "cover_renewal_gaps_ms":cover_renewal_gaps_ms,
              "cover_policy":cover_semantic,"cover_policy_source_iteration":cover_policy_source_iteration,
              "cover_validity_admission":validity_admission,
              "cover_validity_soft_events":invalidation_monitor.soft_event_count,
              "cover_validity_latest_soft_event":invalidation_monitor.latest_soft_event,
              "terminal_candidate":True,"model_action_discarded":False})
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
          "planner_turn_id":planner_handle.turn_id,
          "planner_turn_status":planner_result.status,
          "planner_answer_eligible":planner_result.answer_eligible,
          "planner_cancellation_requested":planner_result.cancellation_requested,
          "planner_interrupt":planner_interrupt,
          "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
          "model_image_to_plan_accept_ns":first_accepted-grounded_capture_ns,
          "fresh_observation_to_plan_accept_ns":first_accepted-fresh_before_plan["capture_ns"],
          "fresh_sequence_at_plan":fresh_before_plan["sequence"],
          "cover_terminal_before_plan":True,
          "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
          "cover_renewal_gaps_ms":cover_renewal_gaps_ms,
          "cover_policy":cover_semantic,"cover_policy_source_iteration":cover_policy_source_iteration,
          "cover_validity_admission":validity_admission,
          "cover_validity_soft_events":invalidation_monitor.soft_event_count,
          "cover_validity_latest_soft_event":invalidation_monitor.latest_soft_event,
          "plan_terminal":"completed","model_action_discarded":False})
    process.stdin.write('{"op":"finish"}\n');process.stdin.flush()
    score=wait(lambda r:r["event"]=="post_control_score")
    process.wait(timeout=20)
    planner_client.close()
    atexit.unregister(planner_client.close)
    (args.out/"stderr.txt").write_text(process.stderr.read())
    report={"claim":"persistent typed planner invalidation from a fixed real-MAP01 threat state", "model":args.model,
      "effort":args.effort,"iterations":len(decisions),"decisions":decisions,"score":score,
      "model_session_span":args.session_span,
      "model_session_ids":list(dict.fromkeys(row["model_session_id"] for row in decisions)),
      "motor_contract":"semantic commands compiled to <=450ms turns and <=900ms movement",
      "effect_receipt_contract":"reuse the final exact sample already emitted by each hold; retain full local receipts but expose only no-visible-effect action names to the model",
      "effect_receipt_extra_steps":0,
      "contingency_contract":"preplanned no-visible-effect fallback skips the primary tail and runs without another model call",
      "contingencies_authored":sum(len(x["action"].get("contingencies",[]))
                                   for x in decisions if isinstance(x.get("action"),dict)),
      "contingency_branches_taken":sum(x.get("contingency_branch") is not None for x in decisions),
      "contingency_branch_latency_ms":[x["contingency_branch"]["latency_ms"] for x in decisions if x.get("contingency_branch")],
      "program_admissions":program_admissions,
      "extra_program_admissions_vs_one_bundle":program_admissions-sum(
          isinstance(x.get("action"),dict) and x["action"]["state"]=="active" and
          not x.get("model_action_discarded",False)
          for x in decisions),
      "effect_receipt_commands":sum(len(x.get("effect_receipts",[])) for x in decisions),
      "effect_observation_samples":sum(x.get("effect_observation_samples",0) for x in decisions),
      "effect_observation_capture_ms":sum(x.get("effect_observation_capture_ms",0) for x in decisions),
      "game_continued_during_model_calls":True,
      "runtime_fixture":runtime_fixture,
      "fixture_contract":"hash/IWAD/engine/map/skill checked before load; measured control begins after load; fixture grants no action authority",
      "planner_contract":"one capability-minimized app-server process; stable typed thread/turn ownership; invalidation interrupts the matching turn and no cancelled or stale answer is admitted",
      "planner_turns":len(decisions),
      "planner_interruption_requests":sum(x.get("planner_interrupt") is not None for x in decisions),
      "planner_interrupted_completions":sum(x.get("planner_turn_status")=="interrupted" for x in decisions),
      "planner_ineligible_answers":sum(not x.get("planner_answer_eligible",False) for x in decisions),
      "policy_invalidation_contract":"a planner-authored typed health envelope may only preserve already admitted cover through soft change; hard, unknown, expired or binding-mismatched evidence cancels cover and discards the dependent model action; it never grants input authority or proves success",
      "policy_invalidations":sum(x.get("policy_invalidation") is not None for x in decisions),
      "cover_validity_soft_events":sum(x.get("cover_validity_soft_events",0) for x in decisions),
      "cover_validity_admission_rejections":sum(
          x.get("cover_validity_admission",{}).get("status") != "admitted" for x in decisions),
      "model_actions_discarded":sum(x.get("model_action_discarded",False) for x in decisions),
      "cover_programs":sum(len(x.get("cover_program_ids",[])) for x in decisions),
      "cover_renewals":sum(x.get("cover_renewals",0) for x in decisions),
      "cover_renewal_gaps_ms":[gap for x in decisions for gap in x.get("cover_renewal_gaps_ms",[])],
      "model_authored_cover_policies":sum(isinstance(x.get("action"),dict) and
          x["action"]["state"]=="active" and not x.get("model_action_discarded",False)
          for x in decisions),
      "model_authored_cover_validity_envelopes":sum(isinstance(x.get("action"),dict) and
          x["action"]["state"]=="active" and len(x["action"].get("next_cover_validity",[]))==1 and
          not x.get("model_action_discarded",False) for x in decisions),
      "model_wall_seconds":sum(x["model_ns"] for x in decisions)/1e9}
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"iterations":len(decisions),"score":score,
      "model_wall_seconds":report["model_wall_seconds"]},indent=2))

if __name__ == "__main__": main()
