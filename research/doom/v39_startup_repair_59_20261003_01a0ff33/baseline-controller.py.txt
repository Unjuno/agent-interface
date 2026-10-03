"""MAP01 controller with unauthored-coast liveness after rejected action."""
import argparse
import atexit
from collections import Counter
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
from doom_hud_signal_v3 import DoomStatusNumberReader
from doom_typed_observation_v1 import (
    build_action_snapshot as build_typed_action_snapshot,
    reconcile_artifact)
from doom_action_validity_contract_v1 import build_contract as build_action_contract
from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor
from codex_app_server_client_v2 import CodexAppServerClient
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
from final_action_admission_v2 import (
    decide_final_admission, record_controller_no_input,
    record_action_validity, record_executor_admission)
from action_validity_admission_v1 import SNAPSHOT_FORMAT, evaluate_action_validity
from running_action_guard_v1 import (
    ACTIVE as RUNNING_ACTIVE, BETWEEN as RUNNING_BETWEEN,
    CANCEL as RUNNING_CANCEL, COMPLETED as RUNNING_COMPLETED,
    READY as RUNNING_READY, REJECTED as RUNNING_REJECTED,
    REVOKED as RUNNING_REVOKED, RunningActionGuard)
from running_action_guard_v2 import RunningActionGuardV2
from running_action_guard_v3 import RunningActionGuardV3
from doom_action_snapshot_v1 import build_action_snapshot
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


class UnauthoredCoastMonitor:
    """No policy can become invalid when coast grants no action authority.

    Exact observations still update latest and fresh immediate action validity
    still gates any model answer before input. This suppresses only a redundant
    planner interruption caused by damage to an empty runtime fallback.
    """
    event_types = frozenset()
    soft_event_count = 0
    latest_soft_event = None

    def observe(self, observation):
        raise AssertionError("unauthored coast must not evaluate a policy")


def select_cover_monitor(monitor, admission, commands, source_iteration):
    if source_iteration is None and not commands and admission["authored"] is None:
        admission = dict(admission)
        admission["monitor_mode"] = "unauthored_coast_no_policy"
        return UnauthoredCoastMonitor(), admission
    admission = dict(admission)
    admission["monitor_mode"] = "authored_policy_guard"
    return monitor, admission


def guard_spec(validity, source_signal, index):
    critical = source_signal["value"] if validity is None else validity["critical_health_minimum"]
    maximum_loss = 0 if validity is None else validity["maximum_health_loss"]
    return {
        "op": "observable_signal_guard",
        "guard_id": f"map01-{index}",
        "source_sequence": source_signal["sequence"],
        "signal_id": "health",
        "source_value": source_signal["value"],
        "hard_minimum": max(critical, source_signal["value"] - maximum_loss),
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
        expected = {"signal_id", "critical_health_minimum", "maximum_health_loss",
                    "max_source_age_ms"}
        if (type(authored_validity) is not dict or set(authored_validity) != expected or
                authored_validity["signal_id"] != "health" or
                type(authored_validity["critical_health_minimum"]) is not int or
                not 1 <= authored_validity["critical_health_minimum"] <= 200 or
                type(authored_validity["maximum_health_loss"]) is not int or
                not 0 <= authored_validity["maximum_health_loss"] <= MAX_AUTHORED_HEALTH_LOSS or
                type(authored_validity["max_source_age_ms"]) is not int or
                not 100 <= authored_validity["max_source_age_ms"] <= 30000):
            raise ValueError("exact typed health validity required")
    if authored_validity is None:
        admission_status = "admitted"
    elif authored_validity["critical_health_minimum"] > source_signal["value"]:
        admission_status = "rejected_source_below_hard_minimum"
    else:
        admission_status = "admitted"
    admitted = admission_status == "admitted"
    effective = authored_validity if admitted else None
    spec = guard_spec(effective, source_signal, index)
    guard = ObservableSignalGuard(spec, source_signal, source_signal["binding"])
    receipt = {
        "status": admission_status,
        "authored": authored_validity,
        "effective": {"signal_id": "health",
                      "critical_health_minimum": source_signal["value"] if effective is None else
                          effective["critical_health_minimum"],
                      "maximum_health_loss": 0 if effective is None else
                          effective["maximum_health_loss"],
                      "hard_minimum": spec["hard_minimum"],
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


def latest_soft_event_summary(decisions):
    """Return bounded semantic evidence from the immediately preceding interval."""
    if not decisions:
        return None
    decision = decisions[-1]
    count = decision.get("cover_validity_soft_events", 0)
    event = decision.get("cover_validity_latest_soft_event")
    if count == 0 and event is None:
        return None
    if type(count) is not int or count < 1 or type(event) is not dict:
        raise RuntimeError("inconsistent prior soft-event evidence")
    outcome = event.get("outcome")
    signal = event.get("signal")
    iteration = decision.get("iteration")
    source_iteration = decision.get("cover_policy_source_iteration")
    if (type(outcome) is not dict or type(signal) is not dict or
            signal.get("signal_id") != "health" or
            outcome.get("signal_id") != "health" or
            outcome.get("status") != "SOFT_CHANGED" or
            outcome.get("reason") != "within_validity_envelope" or
            outcome.get("keep_existing_policy") is not True or
            outcome.get("requires_new_decision") is not False or
            outcome.get("grants_input_authority") is not False or
            outcome.get("may_only_preserve_or_reduce_existing_authority") is not True or
            type(outcome.get("source_value")) is not int or
            type(outcome.get("current_value")) is not int or
            type(outcome.get("hard_minimum")) is not int or
            type(event.get("sequence")) is not int or event.get("sequence") < 1 or
            type(iteration) is not int or iteration < 0 or
            type(source_iteration) is not int or source_iteration < 0 or
            event.get("sequence") != signal.get("sequence") or
            outcome.get("current_value") != signal.get("value") or
            outcome.get("current_value") < outcome.get("hard_minimum")):
        raise RuntimeError("invalid prior soft-event evidence")
    return {
        "signal_id": "health",
        "source_value": outcome["source_value"],
        "current_value": outcome["current_value"],
        "hard_minimum": outcome["hard_minimum"],
        "soft_event_count": count,
        "sequence": event["sequence"],
        "observed_during_iteration": iteration,
        "cover_policy_source_iteration": source_iteration,
        "effect": "prior_cover_preserved",
        "grants_input_authority": False,
    }


def final_admission_from_planner_result(planner_result, terminal_observed_ns,
                                        policy_invalidation, decided_ns):
    return decide_final_admission({
        "turn_id": planner_result.handle.turn_id,
        "status": planner_result.status,
        "answer_eligible": planner_result.answer_eligible,
        "terminal_observed_ns": terminal_observed_ns,
    }, policy_invalidation, decided_ns)


def bind_first_plan_acceptance(receipt, record):
    expected = {"id", "accepted_ns"}
    if type(record) is not dict or not expected.issubset(record):
        raise ValueError("first execution record lacks admission evidence")
    return record_executor_admission(receipt, {
        "event": "accepted", "id": record["id"],
        "accepted_ns": record["accepted_ns"]})


def prepare_action_admission(receipt, action, authored, source_health,
                             source_ammo, current_health, current_ammo,
                             decided_ns):
    """Bind planner semantics to exact signals and re-evaluate at final admission."""
    contract = build_action_contract(
        action["commands"], authored, source_health, source_ammo)
    required = contract["source"]["signals"]
    current = {"health": {"status": current_health["status"],
                          "value": current_health["value"]}}
    if "ammo" in required:
        if (current_ammo["sequence"] != current_health["sequence"] or
                current_ammo["capture_ns"] != current_health["capture_ns"] or
                current_ammo["binding"] != current_health["binding"]):
            raise ValueError("current health and ammo must share one observation epoch")
        current["ammo"] = {"status": current_ammo["status"],
                           "value": current_ammo["value"]}
    snapshot = {"format": SNAPSHOT_FORMAT,
                "sequence": current_health["sequence"],
                "capture_ns": current_health["capture_ns"],
                "binding": current_health["binding"], "signals": current}
    validity = evaluate_action_validity(
        action["commands"], contract, snapshot, decided_ns)
    return record_action_validity(receipt, action["commands"], validity)


class DoomRunningActionMonitor:
    """Adapt exact session observations to one no-input running guard."""

    event_name = "running_action_invalidation"
    event_types = {"typed_observation"}

    def __init__(self, guard, health_reader, ammo_reader):
        self.guard = guard
        contract = guard.guard.contract if isinstance(guard, RunningActionGuardV2) else guard.contract
        required = set(contract["source"]["signals"])
        self.contract = contract
        readers = {"health": health_reader, "ammo": ammo_reader}
        self.readers = {name: readers[name] for name in required}
        self.last_receipt = guard.receipt()

    def observe(self, observation, decided_ns=None):
        snapshot = (build_typed_action_snapshot(observation, self.contract)
                    if observation.get("event") == "typed_observation"
                    else build_action_snapshot(observation, self.contract, self.readers))
        decided_ns = time.perf_counter_ns() if decided_ns is None else decided_ns
        self.last_receipt = self.guard.check_current(snapshot, decided_ns)
        if self.last_receipt["state"] in (RUNNING_CANCEL, RUNNING_REJECTED):
            result = {"event": self.event_name,
                      "running_action_guard": self.last_receipt}
            if observation.get("event") == "typed_observation":
                result["source_event"] = {key: observation[key] for key in (
                        "schema", "id", "step", "sequence", "capture_ns",
                        "pointer_binding", "signals", "frame_rgb_sha256",
                        "typed_ready_ns", "emit_ns")}
            return result
        return None


def persist_running_invalidation(root, identifier, boundary):
    """Persist the exact decision before terminal validation can fail."""
    guard = boundary.get("running_action_guard") if type(boundary) is dict else None
    source = boundary.get("source_event") if type(boundary) is dict else None
    if (boundary.get("event") != "running_action_invalidation" or
            type(guard) is not dict or guard.get("state") not in
            (RUNNING_CANCEL, RUNNING_REJECTED) or
            type(source) is not dict or source.get("schema") !=
            "doom-typed-observation-v1" or
            guard.get("invalidation", {}).get("result", {}).get(
                "snapshot", {}).get("capture_ns") != source.get("capture_ns")):
        raise ValueError("exact typed running invalidation required")
    path = Path(root) / f"running-invalidation-{identifier}.json"
    path.write_text(json.dumps(boundary, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return path


def cancel_invalidated_action(process, wait, identifier, guard):
    """Publish physical release first, then require terminal lifecycle closure."""
    process.stdin.write(json.dumps({"op": "cancel", "id": identifier}) + "\n")
    process.stdin.flush()
    event = wait(lambda row: row.get("event") == "cancel_requested" and
                 row.get("id") == identifier)
    guard.record_cancel_requested({
        "event": "cancel_requested", "id": event["id"],
        "matched": event["matched"], "requested_ns": event["requested_ns"]})
    released = wait(lambda row: row.get("event") == "input_released" and
                    row.get("id") == identifier)
    release_receipt = guard.record_input_released({key: released[key] for key in (
        "event", "id", "intent_token", "owner_release", "published_ns",
        "program_terminal_pending", "grants_input_authority")})
    terminal = wait(lambda row: row.get("event") == "terminal" and
                    row.get("id") == identifier)
    receipt = guard.record_cancelled_terminal(terminal)
    return event, released, release_receipt, terminal, receipt


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
    return [sys.executable, str(HERE / "session_map01_v12.py"),
            "--out", str(runtime), "--seed", str(args.seed),
            "--timeout-seconds", "600", "--skill", "1",
            "--load-fixture-manifest", str(args.load_fixture_manifest.resolve())]


def validate_action(action):
    if action["state"] == "active" and not action["commands"]:
        raise ValueError("active state requires a motor command")
    if action["state"] == "active" and len(action["next_cover_validity"]) != 1:
        raise ValueError("active state requires one next_cover_validity")
    if action["state"] == "active" and len(action["action_validity"]) != 1:
        raise ValueError("active state requires one immediate action_validity")
    if action["state"] != "active" and (action["commands"] or action["contingencies"] or
            action["next_cover"] or action["next_cover_validity"] or
            action["action_validity"]):
        raise ValueError("terminal state requires empty commands, contingencies, cover and validity")
    indices=[row["after_command"] for row in action["contingencies"]]
    if len(indices)!=len(set(indices)) or any(index>=len(action["commands"]) for index in indices):
        raise ValueError("contingency indices must be unique primary command indices")


def begin_model_turn(planner, root, image, effect_memory, source_health, source_ammo,
                     prior_soft_event_summary, output_schema):
    prompt_text = ("Select the next bounded MAP01 action from the new temporal sheet.\n"
                   + f"Current locally verified health: {source_health}.\n"
                   + f"Current locally verified ammo: {source_ammo}.\n"
                   + "Newest typed soft event from the preceding control interval: "
                   + json.dumps(prior_soft_event_summary, separators=(",", ":")) + "\n"
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
        base_instructions=(HERE / "map01_motor_responder_v10.txt").read_text())
    planner.start_session()
    output_schema = json.loads((HERE / "map01_cover_policy_schema_v6.json").read_text())
    signal_reader = DoomStatusNumberReader(WAD, signal_id="health")
    ammo_reader = DoomStatusNumberReader(WAD, signal_id="ammo")
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
            event_types = (getattr(observation_monitor, "event_types", {"observation"})
                           if observation_monitor is not None else set())
            if row["event"] in event_types:
                invalidation = observation_monitor.observe(row)
                if invalidation is not None:
                    if invalidation.get("event") == "running_action_invalidation":
                        return invalidation
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
        validity_monitor, validity_admission = select_cover_monitor(
            validity_monitor, validity_admission, cover_semantic,
            cover_policy_source_iteration)
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
        action_source_observation=dict(latest)
        source_health_signal=signal_reader.read(action_source_observation)
        source_ammo_signal=ammo_reader.read(action_source_observation)
        if (source_health_signal["status"] != "observed" or
                source_ammo_signal["status"] != "observed"):
            raise RuntimeError("action source health/ammo unavailable")
        source_image=Path(action_source_observation["image"])
        invalidation_monitor=validity_monitor
        invalidation=None
        prior_receipts=[] if not decisions else decisions[-1].get("effect_receipts",[])
        effect_memory=[row["action"] for row in prior_receipts
                       if row["result"]=="no_visible_effect"]
        prior_soft_event_summary=latest_soft_event_summary(decisions)
        image=model_root/"temporal-sheet.png"
        prior=[Path(row["source_image"]) for row in decisions]
        temporal_sheet(prior+[source_image],image)
        model_started_ns=time.perf_counter_ns()
        planner_handle=begin_model_turn(
            planner,model_root,image,effect_memory,
            source_health_signal["value"],source_ammo_signal["value"],
            prior_soft_event_summary,output_schema)
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
            planner_terminal_observed_ns=time.perf_counter_ns()
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
        final_action_admission=final_admission_from_planner_result(
            planner_result,planner_terminal_observed_ns,
            invalidation,time.perf_counter_ns())
        if invalidation is not None:
            decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
              "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"action":action,
              "effect_memory":effect_memory,"usage":usage,"model_ns":model_ns,
              "prior_soft_event_summary":prior_soft_event_summary,
              "model_session_id":model_session_id,
              "planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,
              "planner_answer_eligible":planner_result.answer_eligible,
              "planner_terminal_observed_ns":planner_terminal_observed_ns,
              "final_action_admission":final_action_admission,
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
            decisions.append({"iteration":index,"source_image":str(source_image),
              "model_image":str(image),"model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
              "action":action,"effect_memory":effect_memory,"usage":usage,"model_ns":model_ns,
              "prior_soft_event_summary":prior_soft_event_summary,
              "model_session_id":model_session_id,"planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,
              "planner_answer_eligible":planner_result.answer_eligible,
              "planner_terminal_observed_ns":planner_terminal_observed_ns,
              "final_action_admission":final_action_admission,
              "planner_cancellation_requested":planner_result.cancellation_requested,
              "planner_interrupt":planner_interrupt,"planner_error":planner_result.error,
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
              "cover_renewal_gaps_ms":cover_renewal_gaps_ms,"cover_policy":cover_semantic,
              "cover_policy_source_iteration":cover_policy_source_iteration,
              "cover_validity_admission":validity_admission,
              "cover_validity_soft_events":invalidation_monitor.soft_event_count,
              "cover_validity_latest_soft_event":invalidation_monitor.latest_soft_event,
              "model_action_discarded":True,"discard_reason":"planner_answer_ineligible",
              "cover_terminal_before_plan":True,"plan_terminal":"not_admitted"})
            continue
        try:
            validate_action(action)
            if action["state"] == "active":
                build_action_contract(
                    action["commands"], action["action_validity"][0],
                    source_health_signal, source_ammo_signal)
        except ValueError as error:
            final_action_admission=record_controller_no_input(
                final_action_admission,"controller_validation_failed")
            decisions.append({"iteration":index,"source_image":str(source_image),
              "model_image":str(image),"model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
              "action":action,"effect_memory":effect_memory,"usage":usage,"model_ns":model_ns,
              "prior_soft_event_summary":prior_soft_event_summary,
              "model_session_id":model_session_id,"planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,"planner_answer_eligible":True,
              "planner_terminal_observed_ns":planner_terminal_observed_ns,
              "final_action_admission":final_action_admission,
              "planner_cancellation_requested":planner_result.cancellation_requested,
              "planner_interrupt":planner_interrupt,"controller_validation_error":str(error),
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
              "cover_renewal_gaps_ms":cover_renewal_gaps_ms,"cover_policy":cover_semantic,
              "cover_policy_source_iteration":cover_policy_source_iteration,
              "cover_validity_admission":validity_admission,
              "cover_validity_soft_events":invalidation_monitor.soft_event_count,
              "cover_validity_latest_soft_event":invalidation_monitor.latest_soft_event,
              "model_action_discarded":True,"discard_reason":"controller_validation_failed",
              "cover_terminal_before_plan":True,"plan_terminal":"not_admitted"})
            continue
        if action["state"] != "active":
            final_action_admission=record_controller_no_input(
                final_action_admission,"terminal_model_state")
            decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
              "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"action":action,
              "effect_memory":effect_memory,
              "usage":usage,"model_ns":model_ns,"model_session_id":model_session_id,
              "planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,
              "planner_answer_eligible":planner_result.answer_eligible,
              "planner_terminal_observed_ns":planner_terminal_observed_ns,
              "final_action_admission":final_action_admission,
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
        fresh_before_plan=dict(latest)
        current_health_signal=signal_reader.read(fresh_before_plan)
        current_ammo_signal=ammo_reader.read(fresh_before_plan)
        final_action_admission=prepare_action_admission(
            final_action_admission,action,action["action_validity"][0],
            source_health_signal,source_ammo_signal,
            current_health_signal,current_ammo_signal,time.perf_counter_ns())
        if final_action_admission["status"] != "READY_FOR_FRESH_EXECUTOR_ADMISSION":
            decisions.append({"iteration":index,"source_image":str(source_image),
              "model_image":str(image),"model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
              "action":action,"effect_memory":effect_memory,"usage":usage,"model_ns":model_ns,
              "prior_soft_event_summary":prior_soft_event_summary,
              "model_session_id":model_session_id,"planner_turn_id":planner_handle.turn_id,
              "planner_turn_status":planner_result.status,"planner_answer_eligible":True,
              "planner_terminal_observed_ns":planner_terminal_observed_ns,
              "final_action_admission":final_action_admission,
              "action_source_signals":{"health":source_health_signal,"ammo":source_ammo_signal},
              "action_current_signals":{"health":current_health_signal,"ammo":current_ammo_signal},
              "planner_cancellation_requested":planner_result.cancellation_requested,
              "planner_interrupt":planner_interrupt,
              "controller_model_started_ns":model_started_ns,"controller_model_ended_ns":model_ended_ns,
              "cover_program_ids":cover_ids,"cover_renewals":len(cover_ids)-1,
              "cover_renewal_gaps_ms":cover_renewal_gaps_ms,"cover_policy":cover_semantic,
              "cover_policy_source_iteration":cover_policy_source_iteration,
              "cover_validity_admission":validity_admission,
              "cover_validity_soft_events":invalidation_monitor.soft_event_count,
              "cover_validity_latest_soft_event":invalidation_monitor.latest_soft_event,
              "model_action_discarded":True,"discard_reason":"action_not_current",
              "cover_terminal_before_plan":True,"plan_terminal":"not_admitted"})
            continue
        grounded_capture_ns=source_health_signal["capture_ns"]
        trace=[]
        running_guard=RunningActionGuardV3(
            action,final_action_admission,compile_commands,
            "map01_overlap_controller_v38.compile_commands")
        action_monitor=DoomRunningActionMonitor(
            running_guard,signal_reader,ammo_reader)
        first_accepted=None
        running_invalidation=None
        partial_execution=None
        refresh_program_ids=[]
        def execute_segment(identifier,commands,role,command_indices,
                            contingency_after=None,branch_evidence=None):
            nonlocal program_admissions,first_accepted,final_action_admission
            before=dict(latest);event_start=len(all_events);clock_ns=time.perf_counter_ns()
            steps=compile_commands(commands)
            submit_command={"op":"submit","id":identifier,
              "expected_sequence":latest["sequence"],"valid_until_ns":clock_ns+25_000_000_000,
              "steps":steps}
            process.stdin.write(json.dumps(submit_command)+"\n");process.stdin.flush()
            accepted=wait(lambda r:r["event"] in ("accepted","rejected") and
                          (r.get("id")==identifier or r["event"]=="rejected"))
            if accepted["event"]!="accepted":raise RuntimeError(accepted)
            program_admissions+=1
            guard_acceptance={"event":"accepted","id":identifier,
                              "steps":accepted["steps"],
                              "program_sha256":accepted["program_sha256"],
                              "intent_token":accepted["intent_token"],
                              "accepted_ns":accepted["accepted_ns"]}
            program_binding={"role":role,"semantic_commands":commands,
              "command_indices":command_indices,"contingency_after":contingency_after,
              "compiled_steps":steps}
            running_guard.admit_program(
                program_binding,{"command":submit_command,"sent_ns":clock_ns},
                guard_acceptance,branch_evidence=branch_evidence)
            final_action_admission=running_guard.final_admission
            if first_accepted is None:
                first_accepted=accepted["accepted_ns"]
            boundary=wait(lambda r:r["event"]=="terminal" and r.get("id")==identifier,
                          observation_monitor=action_monitor)
            invalidated=boundary["event"]=="running_action_invalidation"
            cancel_event=None
            physical_release_event=None
            release_pending_receipt=None
            if invalidated:
                persist_running_invalidation(args.out,identifier,boundary)
                (cancel_event,physical_release_event,release_pending_receipt,
                 terminal,guard_receipt)=cancel_invalidated_action(
                    process,wait,identifier,running_guard)
            else:
                terminal=boundary
                if terminal["status"]!="completed":raise RuntimeError(terminal)
                guard_receipt=running_guard.record_completed_terminal(
                    terminal,final=False)
            observations=[row for row in all_events[event_start:]
                           if row.get("event")=="observation" and row.get("id")==identifier]
            completed=len(commands) if not invalidated else terminal["steps_completed"]
            receipts=(effect_receipts(commands[:completed],before,observations,
                                      accepted["accepted_ns"])
                      if completed else [])
            records=[]
            for local_index,(command,receipt) in enumerate(zip(commands[:completed],receipts)):
                samples=[row for row in observations if row["step"]==local_index]
                record={"id":identifier,"role":role,
                  "command_index":command_indices[local_index],"command":command,
                  "accepted_ns":accepted["accepted_ns"],
                  "terminal_ns":terminal["terminal_ns"],"receipt":receipt,
                  "observation_samples":len(samples),
                  "observation_capture_ms":sum(row["capture_ms"] for row in samples)}
                trace.append(record);records.append(record)
            partial=None
            if invalidated and completed < len(commands):
                samples=[row for row in observations if row["step"]==completed]
                partial={"id":identifier,"role":role,
                  "command_index":command_indices[completed],
                  "command":commands[completed],"accepted_ns":accepted["accepted_ns"],
                  "terminal_ns":terminal["terminal_ns"],"receipt":None,
                  "observation_samples":len(samples),
                  "observation_capture_ms":sum(row["capture_ms"] for row in samples),
                  "status":"cancelled_action_not_current"}
            return {"records":records,"invalidated":invalidated,
                    "partial":partial,"cancel_event":cancel_event,
                    "physical_release_event":physical_release_event,
                    "release_pending_guard":release_pending_receipt,
                    "terminal":terminal,"guard":guard_receipt}
        def refresh_between_segments(identifier):
            nonlocal program_admissions
            clock_ns=time.perf_counter_ns()
            process.stdin.write(json.dumps({"op":"submit","id":identifier,
              "expected_sequence":latest["sequence"],"valid_until_ns":clock_ns+5_000_000_000,
              "steps":[{"op":"observe"}]})+"\n");process.stdin.flush()
            accepted=wait(lambda r:r["event"] in ("accepted","rejected") and
                          (r.get("id")==identifier or r["event"]=="rejected"))
            if accepted["event"]!="accepted":raise RuntimeError(accepted)
            program_admissions+=1;refresh_program_ids.append(identifier)
            boundary=wait(lambda r:r["event"]=="terminal" and r.get("id")==identifier,
                          observation_monitor=action_monitor)
            if boundary["event"]=="running_action_invalidation":
                persist_running_invalidation(args.out,identifier,boundary)
                terminal=wait(lambda r:r["event"]=="terminal" and r.get("id")==identifier)
                release=terminal.get("release",{})
                if (terminal.get("status")!="completed" or release.get("verified") is not True or
                        release.get("keys_down")!=[] or release.get("buttons_down")!=[]):
                    raise RuntimeError("passive refresh did not verify empty release")
                return False
            terminal=boundary;release=terminal.get("release",{})
            if (terminal.get("status")!="completed" or release.get("verified") is not True or
                    release.get("keys_down")!=[] or release.get("buttons_down")!=[] or
                    running_guard.receipt()["state"]!=RUNNING_READY):
                raise RuntimeError("passive refresh did not establish current action")
            return True
        contingencies={row["after_command"]:row for row in action["contingencies"]}
        branch=None
        boundaries=sorted(contingencies)
        if not boundaries or boundaries[-1] != len(action["commands"])-1:
            boundaries.append(len(action["commands"])-1)
        segment_start=0
        for segment_end in boundaries:
            segment_commands=action["commands"][segment_start:segment_end+1]
            result=execute_segment(f"plan-{index}-primary-{segment_start}-{segment_end}",
                segment_commands,"primary",list(range(segment_start,segment_end+1)))
            records=result["records"]
            if result["invalidated"]:
                running_invalidation=result["guard"]["invalidation"]
                partial_execution=result["partial"]
                break
            contingency=contingencies.get(segment_end)
            trigger=records[-1]
            if trigger["receipt"]["result"]=="no_visible_effect" and contingency:
                branch={"after_command":segment_end,"condition":"no_visible_effect",
                  "skipped_primary_commands":len(action["commands"])-segment_end-1,
                  "fallback_commands":contingency["commands"],"latency_ms":None}
                if not refresh_between_segments(
                        f"plan-{index}-refresh-after-{segment_end}"):
                    running_invalidation=running_guard.receipt()["invalidation"]
                    break
                fallback_result=execute_segment(
                    f"plan-{index}-fallback-{segment_end}",contingency["commands"],
                    "fallback",list(range(len(contingency["commands"]))),segment_end,
                    {"after_command":segment_end,"condition":"no_visible_effect",
                     "primary_program_id":result["terminal"]["id"],
                     "command_index":segment_end,
                     "semantic_command":trigger["command"],
                     "effect_receipt":trigger["receipt"]})
                fallback_records=fallback_result["records"]
                if fallback_result["invalidated"]:
                    running_invalidation=fallback_result["guard"]["invalidation"]
                    partial_execution=fallback_result["partial"]
                    break
                branch["latency_ms"]=(fallback_records[0]["accepted_ns"]-
                    trigger["receipt"]["effect_observed_ns"])/1e6
                break
            segment_start=segment_end+1
            if segment_start<len(action["commands"]) and not refresh_between_segments(
                    f"plan-{index}-refresh-after-{segment_end}"):
                running_invalidation=running_guard.receipt()["invalidation"]
                break
        if running_guard.receipt()["state"]==RUNNING_BETWEEN:
            running_guard.record_action_complete()
        running_action_receipt=running_guard.receipt()
        if running_action_receipt["state"] not in (
                RUNNING_COMPLETED,RUNNING_REVOKED,RUNNING_REJECTED):
            raise RuntimeError("running action ended without a closed guard state")
        receipts=[row["receipt"] for row in trace]
        decisions.append({"iteration":index,"source_image":str(source_image),"model_image":str(image),
          "model_image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
          "action":action,"usage":usage,"model_ns":model_ns,
          "prior_soft_event_summary":prior_soft_event_summary,
          "effect_memory":effect_memory,"effect_receipts":receipts,
          "effect_observation_samples":sum(row["observation_samples"] for row in trace),
          "effect_observation_capture_ms":sum(row["observation_capture_ms"] for row in trace),
          "execution_trace":trace,"contingency_branch":branch,
          "compiled_commands":[row["command"] for row in trace],
          "model_session_id":model_session_id,
          "planner_turn_id":planner_handle.turn_id,
          "planner_turn_status":planner_result.status,
          "planner_answer_eligible":planner_result.answer_eligible,
           "planner_terminal_observed_ns":planner_terminal_observed_ns,
           "final_action_admission":final_action_admission,
           "running_action_guard":running_action_receipt,
           "running_action_invalidation":running_invalidation,
           "partial_execution":partial_execution,
           "action_refresh_program_ids":refresh_program_ids,
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
           "plan_terminal":("completed" if running_action_receipt["state"]==RUNNING_COMPLETED
                            else "stopped_action_not_current"),
           "model_action_discarded":False,
           "remaining_action_discarded":running_action_receipt["state"]!=RUNNING_COMPLETED})
    process.stdin.write('{"op":"finish"}\n');process.stdin.flush()
    score=wait(lambda r:r["event"]=="post_control_score")
    process.wait(timeout=20)
    planner_client.close()
    atexit.unregister(planner_client.close)
    (args.out/"stderr.txt").write_text(process.stderr.read())
    typed_events = {row["sequence"]:row for row in all_events
                    if row.get("event")=="typed_observation"}
    full_events = {row["sequence"]:row for row in all_events
                   if row.get("event")=="observation"}
    typed_reconciliations=[]
    for sequence,typed in sorted(typed_events.items()):
        full=full_events.get(sequence)
        if full is None:
            typed_reconciliations.append({
                "schema":"doom-typed-artifact-reconciliation-v1",
                "matched":False,"sequence":sequence,
                "checks":{"full_observation":False}})
        else:
            reconciliation=reconcile_artifact(
                typed,full,{"health":signal_reader,"ammo":ammo_reader})
            reconciliation["sequence"]=sequence
            typed_reconciliations.append(reconciliation)
    report={"claim":"persistent typed planner plus immediate and running action invalidation from a fixed real-MAP01 threat state", "model":args.model,
      "effort":args.effort,"iterations":len(decisions),"decisions":decisions,"score":score,
      "model_session_span":args.session_span,
      "model_session_ids":list(dict.fromkeys(row["model_session_id"] for row in decisions)),
      "motor_contract":"semantic commands compiled to <=450ms turns and <=900ms movement",
      "effect_receipt_contract":"reuse the final exact sample already emitted by each hold; retain full local receipts but expose only no-visible-effect action names to the model",
      "soft_event_context_contract":"expose only the newest validated typed soft event from the preceding control interval in the already-required next planner turn; add no image, model call, input authority or mid-turn boundary",
      "final_action_admission_contract":"historical transition receipt only after running guard creation: planner eligibility, controller policy/validation decision and first fresh Executor acceptance remain retained; it is not current authority",
      "running_action_contract":"the root running-action-v3 receipt is authoritative after guard creation; every primary/fallback semantic slice is deterministically recompiled and bound to the exact submitted steps, Executor program SHA-256 and lease token; invalidation requires a matched cancel, then exposes independently verified empty physical release while terminal closure remains pending; inter-segment input still requires a fresh passive observation",
      "typed_observation_contract":"health/ammo and RGB SHA-256 are extracted from the captured in-memory frame and emitted before transport/artifact publication; every retained full observation must later match epoch, binding, RGB hash and both signal values",
      "typed_observations":len(typed_events),
      "typed_artifact_reconciliations":typed_reconciliations,
      "typed_artifact_reconciled":sum(row["matched"] for row in typed_reconciliations),
      "typed_artifact_reconciliation_failures":sum(not row["matched"] for row in typed_reconciliations),
      "typed_capture_to_ready_ms":[row["capture_to_typed_ready_ms"]
                                   for row in typed_events.values()],
      "typed_ready_to_emit_ms":[(row["emit_ns"]-row["typed_ready_ns"])/1e6
                                for row in typed_events.values()],
      "typed_capture_to_artifact_ready_ms":[
          row["capture_to_artifact_ready_ms"] for row in full_events.values()],
      "typed_emit_to_artifact_ready_ms":[
          (full_events[sequence]["artifact_ready_ns"]-typed["emit_ns"])/1e6
          for sequence,typed in typed_events.items() if sequence in full_events],
      "effect_receipt_extra_steps":0,
      "contingency_contract":"preplanned no-visible-effect fallback skips the primary tail and runs without another model call",
      "contingencies_authored":sum(len(x["action"].get("contingencies",[]))
                                   for x in decisions if isinstance(x.get("action"),dict)),
      "contingency_branches_taken":sum(x.get("contingency_branch") is not None for x in decisions),
      "contingency_branch_latency_ms":[x["contingency_branch"]["latency_ms"] for x in decisions if x.get("contingency_branch")],
      "program_admissions":program_admissions,
      "action_refresh_programs":sum(len(x.get("action_refresh_program_ids",[])) for x in decisions),
      "running_action_invalidations":sum(x.get("running_action_invalidation") is not None for x in decisions),
      "running_action_revocations":sum(x.get("running_action_guard",{}).get("state")==RUNNING_REVOKED for x in decisions),
      "running_action_intersegment_rejections":sum(x.get("running_action_guard",{}).get("state")==RUNNING_REJECTED for x in decisions),
      "running_action_program_bindings":sum(
          len(x.get("running_action_guard",{}).get("program_bindings",[]))
          for x in decisions),
      "historical_first_executor_admissions":sum(
          x.get("running_action_guard",{}).get("historical_first_admission") is not None
          for x in decisions),
      "current_input_authority_true_at_decision_close":sum(
          x.get("running_action_guard",{}).get("current_input_authority") is True
          for x in decisions),
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
      "policy_invalidation_contract":"authored cover health floor is max(critical_health_minimum, fresh source health - schema-bounded maximum_health_loss); soft change may only preserve admitted cover; hard, unknown, expired or binding-mismatched evidence cancels cover and discards the dependent model action; unauthored empty coast has no policy to invalidate and does not interrupt a pending answer on damage; exact observations and fresh immediate action validity remain mandatory; this never grants input authority or proves success",
      "policy_invalidations":sum(x.get("policy_invalidation") is not None for x in decisions),
      "cover_validity_soft_events":sum(x.get("cover_validity_soft_events",0) for x in decisions),
      "cover_validity_admission_rejections":sum(
          x.get("cover_validity_admission",{}).get("status") != "admitted" for x in decisions),
      "model_actions_discarded":sum(x.get("model_action_discarded",False) for x in decisions),
      "historical_final_action_admission_statuses":dict(Counter(
          x["final_action_admission"]["status"] for x in decisions)),
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

