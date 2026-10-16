"""V3 Chromium pair: add field-border texture after preserved v2 refusal."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from adaptive_acquisition_caller_v1 import run as run_adaptive
from append_checkpoint_v1 import load
from compiled_form_grounding_v1 import validate as validate_grounding
from compiled_gui_interface_v1 import run as run_compiled
from coordinate_frame_transform_v1 import translation
from durable_submit_v4 import initialize, run
from model_point_target_v1 import patch
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from schema_preflight_gate_v1 import require_compatible


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/compiled-gui-interface-live-03"
SEED = 991023
WINDOWS_PYTHON = Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
SCHEMA = HERE / "compiled_form_grounding_schema_v1.json"
INSTRUCTIONS = HERE / "compiled_form_grounding_responder_v1.txt"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          capture_output=True, text=True, check=True).stdout.strip()


def parse_model(output):
    events = [json.loads(line) for line in
              (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    threads = [row["thread_id"] for row in events if row.get("type") == "thread.started"]
    if len(messages) != 1 or len(turns) != 1 or len(threads) != 1:
        raise ValueError("one model thread, message and completed turn required")
    raw = json.loads(messages[0])
    grounding = validate_grounding(raw)
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"raw": raw, "grounding": grounding, "usage": turns[0]["usage"],
            "call_id": threads[0],
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6,
            "requested_model": process["requested_model"],
            "requested_effort": process["requested_effort"], "cost": None}


def model_call(root, prompt, image):
    prompt_path = root / "grounding-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "grounding-model"
    command = [str(WINDOWS_PYTHON), windows_path(HERE / "target_handle_model_runner_v2.py"),
        NODE, CLI, windows_path(prompt_path), windows_path(OUT / "empty-workspace"),
        windows_path(output), "coordinate", windows_path(image),
        windows_path(INSTRUCTIONS), windows_path(SCHEMA)]
    completed = subprocess.run(command, capture_output=True, timeout=90)
    (root / "grounding-runner-stdout.txt").write_bytes(completed.stdout)
    (root / "grounding-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError("grounding model call failed; no retry")
    result = parse_model(output)
    dump(root / "grounding-result.json", result)
    return result


def compiled_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "chromium-private-form-v1",
        "session_scope": "live-chromium-seed991023",
        "surface": "chromium-private-form",
        "predicates": ["field_pixels_changed", "field_target_present",
                       "submit_target_present", "submission_pixels_changed"],
        "symbols": {
            "value_field": {"kind": "target_reference",
                "target_reference": "form_field",
                "identity_predicate": "field_target_present",
                "dependencies": ["field_target_present", "field_pixels_changed"]},
            "submit_control": {"kind": "target_reference",
                "target_reference": "submit_control",
                "identity_predicate": "submit_target_present",
                "dependencies": ["submit_target_present", "field_pixels_changed"]},
        },
        "actions": {
            "enter_token": {"target_symbol": "value_field",
                "operation": "enter_exact_token",
                "expected_effect": {"field_pixels_changed": True}},
            "submit_form": {"target_symbol": "submit_control",
                "operation": "activate_submit",
                "expected_effect": {"submission_pixels_changed": True}},
        },
        "method": {"name": "enter_then_submit", "version": "1",
            "initial_state": "empty", "max_transitions": 2,
            "max_runtime_ms": 10000,
            "states": {
                "empty": {"branches": [{"when": {"field_pixels_changed": False,
                    "field_target_present": True}, "outcome": "action",
                    "action": "enter_token", "next_state": "filled", "reason": None}]},
                "filled": {"branches": [{"when": {"field_pixels_changed": True,
                    "submit_target_present": True}, "outcome": "action",
                    "action": "submit_form", "next_state": "submitted", "reason": None}]},
                "submitted": {"branches": [{"when": {
                    "submission_pixels_changed": True}, "outcome": "complete",
                    "action": None, "next_state": None, "reason": None}]},
            }},
    }


def run_case(index, name, changed_after_first):
    case_started_ns = time.perf_counter_ns()
    root = OUT / f"{index}-{name}"
    root.mkdir()
    errors = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "target_handle_chromium_socket_v5.py"),
        "chromium-point-target-v1", "serve", "--", "--app", "chromium",
        "--seed", str(SEED), "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=errors, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-compiled-form-")
    journal = Path(temporary.name) / "journal.jsonl"
    calls = []
    runtime_events = []
    raw_evidence = []
    intervention = None
    evaluation = None
    actual = {}
    try:
        endpoint = json.loads(process.stdout.readline())
        dump(root / "endpoint.json", endpoint)
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        goal = first(initial["reply"]["records"], "ready")["goal"]
        initialize(journal, initial["continuation"])

        def call(spec):
            begin = time.perf_counter_ns()
            result = run(journal, spec)
            calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(),
                          "result": result})
            dump(root / "calls.json", calls)
            assert result["state"]["pending"] is None
            shutil.copy2(journal, root / "journal.jsonl")
            return result

        def clock():
            result = call({"command": {"op": "clock"}, "timeout": 3})
            return result["state"]["last_resolution"]["clock"]

        def submit(steps, timeout=8, expected_sequence=None, valid_until_ns=None):
            current = clock()
            sequence = current["sequence"] if expected_sequence is None else expected_sequence
            deadline = (current["runtime_ns"] + 10_000_000_000
                        if valid_until_ns is None else valid_until_ns)
            return call({"command": {"op": "submit", "expected_sequence": sequence,
                "valid_until_ns": deadline, "steps": steps}, "timeout": timeout})

        navigate = submit([{"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": goal["url"]}, {"op": "key", "key": "Return"},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        source_result = submit([{"op": "observe"}])
        source = first(source_result["reply"]["records"], "observation")
        source_image = root / "runtime" / Path(source["image"]).name
        prompt = (
            "The attached current 1280x800 screenshot is a private Chromium form for "
            f"the authorized task of submitting the exact token {goal['token']}. "
            "Identify one point inside the visible text Value field and one point inside "
            "the visible Save/submit button. Put the field point in the empty right half "
            "of the field, away from its blinking left-edge caret. Declare the fixed bounded method exactly as "
            "required by the schema: enter the exact token, continue only after the field "
            "pixels changed and Submit revalidated, then activate Submit, with final "
            "success decided by changed submission pixels followed by independent scoring."
        )
        model_record = None
        mint_report = None
        runtime_receipt = None
        action_records = []
        last_check = {}
        authorizations = {}
        pre_submit_digest = None
        field_baseline = None

        def observe_source(payload):
            return {"observation": source, "image": source["image"],
                    "target": payload["target"]}

        def acquire_anchor(payload):
            return {"source": copy.deepcopy(source), "prompt": prompt}

        def anchor_model(payload):
            nonlocal model_record
            model_record = model_call(root, payload["prompt"], source_image)
            target = {"interface": compiled_interface(),
                      "grounding": model_record["grounding"],
                      "source_sequence": source["sequence"],
                      "authority": "reference_only"}
            return {"call_id": model_record["call_id"],
                    "output": {"status": "target_reference", "target": target},
                    "usage": model_record["usage"],
                    "requested_model": model_record["requested_model"],
                    "requested_effort": model_record["requested_effort"], "cost": None}

        def final_revalidate(target):
            nonlocal mint_report
            grounding = target["grounding"]
            steps = []
            for alias, point in (("form_field", grounding["field_point"]),
                                 ("submit_control", grounding["submit_point"])):
                region_size = [24, 22] if alias == "form_field" else [24, 14]
                steps.append({"op": "target_handle_mint_from_point", "name": alias,
                    "coordinate_frame": "window_content",
                    "source_sequence": target["source_sequence"], "point": point,
                    "region_size": region_size, "ttl_ms": 60000,
                    "freshness_ms": 1500, "search_radius": 0,
                    "allowed_transformations": ["window_translation"]})
            programs = []
            minted = []
            refusals = []
            for step in steps:
                result = submit([step])
                records = result["reply"]["records"]
                terminal = first(records, "terminal")
                program = {"step": step, "terminal": terminal,
                           "minted": [row for row in records if row.get("event") ==
                                      "target_handle_minted_from_point"],
                           "refusals": [row for row in records if row.get("event") ==
                                        "target_handle_mint_from_point_refused"]}
                programs.append(program)
                minted.extend(program["minted"])
                refusals.extend(program["refusals"])
                if terminal["status"] != "completed":
                    break
            mint_report = {"steps": steps, "programs": programs, "minted": minted,
                           "terminal": programs[-1]["terminal"], "refusals": refusals}
            if (len(programs) == 2 and len(minted) == 2 and all(
                    row["terminal"]["status"] == "completed"
                    and row["terminal"]["release"]["verified"] is True
                    for row in programs)):
                return {"status": "revalidated"}
            return {"status": "unavailable"}

        source_bytes = source_image.read_bytes()
        source_frame_digest = hashlib.sha256(source_bytes).hexdigest()

        def translated_region(box, observation):
            with Image.open(source_image) as original, Image.open(
                    root / "runtime" / Path(observation["image"]).name) as current:
                delta = translation("window_content",
                    source["pointer_binding"]["geometry"],
                    observation["pointer_binding"]["geometry"])
                current_box = [box[0] + delta[0], box[1] + delta[1], box[2], box[3]]
                return patch(original.convert("RGB"), box), patch(current.convert("RGB"), current_box)

        def local_observe(payload):
            nonlocal pre_submit_digest, field_baseline
            state = payload["state"]
            if state == "empty":
                query = submit([{"op": "observe_target_handle",
                                 "target_handle": "form_field", "offset": [12, 11]}])
                target_name = "form_field"
            elif state == "filled":
                query = submit([{"op": "observe_target_handle",
                                 "target_handle": "submit_control", "offset": [12, 7]}])
                target_name = "submit_control"
            else:
                query = submit([{"op": "observe"}])
                target_name = None
            records = query["reply"]["records"]
            observation = first(records, "observation")
            check = next((row for row in records
                          if row.get("event") == "target_handle_checked"), None)
            server_clock = clock()
            assert server_clock["sequence"] == observation["sequence"]
            image_path = root / "runtime" / Path(observation["image"]).name
            image_digest = sha(image_path)
            try:
                _, field_now = translated_region([62, 233, 185, 21], observation)
                if state == "empty":
                    field_baseline = field_now
                    field_changed_pixels = 0
                elif field_baseline is None:
                    field_changed_pixels = None
                else:
                    field_changed_pixels = sum(
                        field_baseline[offset:offset + 3] != field_now[offset:offset + 3]
                        for offset in range(0, len(field_now), 3))
                field_changed = ("unknown" if field_changed_pixels is None
                                 else field_changed_pixels >= 40)
            except ValueError:
                field_changed = "unknown"
                field_changed_pixels = None
            predicates = {
                "field_pixels_changed": field_changed,
                "field_target_present": bool(target_name == "form_field" and check
                    and check.get("status") == "REVALIDATED"),
                "submit_target_present": bool(target_name == "submit_control" and check
                    and check.get("status") == "REVALIDATED"),
                "submission_pixels_changed": ("unknown" if pre_submit_digest is None
                    else image_digest != pre_submit_digest),
            }
            if state == "filled":
                pre_submit_digest = image_digest
            evidence_digest = hashlib.sha256((image_digest + json.dumps(
                predicates, sort_keys=True)).encode()).hexdigest()
            normalized = {"sequence": observation["sequence"],
                "captured_ns": observation["capture_ns"],
                "surface": "chromium-private-form", "predicates": predicates,
                "evidence_ref": "runtime/" + image_path.name,
                "evidence_digest": evidence_digest}
            last_check[observation["sequence"]] = {
                "target": target_name, "check": check, "clock": server_clock,
                "observation": observation}
            raw_evidence.append({"state": state, "normalized": normalized,
                                 "image_sha256": image_digest, "target_check": check,
                                 "field_changed_pixels": field_changed_pixels,
                                 "field_change_threshold": 40})
            return normalized

        def admit(payload):
            expected_target = {"enter_token": "form_field",
                               "submit_form": "submit_control"}[payload["action"]]
            row = last_check.get(payload["observation"]["sequence"])
            check = None if row is None else row["check"]
            eligible = bool(row and row["target"] == expected_target and check
                            and check.get("status") == "REVALIDATED")
            if not eligible:
                status = "missing" if check is None or check.get("status") == "MISSING" else "stale"
                return {"eligible": False, "status": status, "authorization": None,
                        "expected_sequence": payload["observation"]["sequence"],
                        "valid_until_ns": 0}
            token = hashlib.sha256((name + payload["action"] + str(
                payload["observation"]["sequence"])).encode()).hexdigest()
            authorizations[token] = {"action": payload["action"],
                "target": expected_target, "sequence": row["clock"]["sequence"],
                "valid_until_ns": row["clock"]["runtime_ns"] + 3_000_000_000,
                "used": False}
            return {"eligible": True, "status": "revalidated", "authorization": token,
                    "expected_sequence": row["clock"]["sequence"],
                    "valid_until_ns": authorizations[token]["valid_until_ns"]}

        def local_execute(payload):
            nonlocal intervention
            authorization = authorizations.get(payload["authorization"])
            if (authorization is None or authorization["used"] or
                    authorization["action"] != payload["action"] or
                    authorization["sequence"] != payload["expected_sequence"]):
                raise ValueError("unknown, used or mismatched local authorization")
            authorization["used"] = True
            if payload["action"] == "enter_token":
                steps = [{"op": "pointer_click_target", "target_handle": "form_field",
                          "offset": [12, 11], "button": 1, "duration_ms": 80},
                         {"op": "chord", "modifier": "Control_L", "key": "a"},
                         {"op": "text", "text": goal["token"]},
                         {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}]
            else:
                steps = [{"op": "pointer_click_target", "target_handle": "submit_control",
                          "offset": [12, 7], "button": 1, "duration_ms": 80},
                         {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}]
            result = submit(steps, expected_sequence=payload["expected_sequence"],
                            valid_until_ns=payload["valid_until_ns"])
            records = result["reply"]["records"]
            terminal = first(records, "terminal")
            action_records.append({"action": payload["action"], "steps": steps,
                                   "terminal": terminal,
                                   "revalidations": [row for row in records if row.get("event") ==
                                                     "target_handle_revalidated"],
                                   "pointer_admissions": [row for row in records if row.get("event") ==
                                                          "pointer_admission"]})
            if changed_after_first and payload["action"] == "enter_token":
                mutation = submit([{"op": "chord", "modifier": "Control_L", "key": "l"},
                    {"op": "text", "text": "about:blank"},
                    {"op": "key", "key": "Return"},
                    {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
                intervention = {"kind": "navigate_about_blank_after_first_action",
                                "terminal": first(mutation["reply"]["records"], "terminal")}
            release = terminal["release"]
            return {"status": terminal["status"], "action_id": terminal["id"],
                    "effect_ref": "terminal:" + terminal["id"],
                    "release": {"verified": release["verified"],
                                "keys_down": release["keys_down"],
                                "buttons_down": release["buttons_down"]}}

        def local_effect(payload):
            return {"status": "succeeded", "evidence_ref":
                    payload["observation"]["evidence_ref"]}

        def execute_target(payload):
            nonlocal runtime_receipt
            runtime_receipt = run_compiled(payload["target"]["interface"], {
                "observe": local_observe, "admit": admit, "execute": local_execute,
                "verify_effect": local_effect, "cancelled": lambda: False,
                "journal": runtime_events.append})
            return {"status": "completed" if runtime_receipt["outcome"] == "TASK_SUCCEEDED"
                    else "failed"}

        adaptive_spec = {"target": "submit exact token in private Chromium form",
            "route": "cold", "coarse_origin": "caller_provided",
            "provided_coarse": {"source_sequence": source["sequence"]},
            "cached_target": None, "repair_on": [], "session_id": name}
        adaptive_started_ns = time.perf_counter_ns()
        adaptive = run_adaptive(adaptive_spec, {
            "observe_source": observe_source, "acquire_anchor": acquire_anchor,
            "anchor_model": anchor_model, "final_revalidate": final_revalidate,
            "execute": execute_target,
            "verify_effect": lambda payload: {"status": "succeeded"},
            "journal": lambda event: None}, id_factory=lambda: "attempt:" + name)
        adaptive_ended_ns = time.perf_counter_ns()

        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": "finish-" + name})
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        submitted = root / "runtime/submitted.txt"
        actual = parse_qs(submitted.read_text()) if submitted.exists() else {}
        feedback_timings = []
        for action_index, action in enumerate(action_records):
            downs = [row["input_ack_ns"] for row in action["pointer_admissions"]
                     if row.get("operation") == "button_down"]
            later_evidence = raw_evidence[action_index + 1]
            feedback_timings.append({"action": action["action"],
                "input_ack_ns": downs[0] if downs else None,
                "feedback_capture_ns": later_evidence["normalized"]["captured_ns"],
                "action_to_first_useful_feedback_ms": (None if not downs else
                    (later_evidence["normalized"]["captured_ns"] - downs[0]) / 1e6)})
        first_action_ack = feedback_timings[0]["input_ack_ns"] if feedback_timings else None
        timings = {"case_started_ns": case_started_ns,
            "adaptive_started_ns": adaptive_started_ns,
            "adaptive_ended_ns": adaptive_ended_ns,
            "adaptive_elapsed_ms": (adaptive_ended_ns - adaptive_started_ns) / 1e6,
            "grounding_model_wait_ms": model_record["runner_ms"],
            "local_runtime_elapsed_ms": (None if runtime_receipt is None else
                runtime_receipt["elapsed_ns"] / 1e6),
            "actions": feedback_timings,
            "first_action_to_independent_semantic_completion_ms": (
                None if first_action_ack is None else
                (evaluation["known_ns"] - first_action_ack) / 1e6),
            "source_observation_to_independent_completion_ms":
                (evaluation["known_ns"] - source["capture_ns"]) / 1e6,
            "agent_wait_definition": "grounding model process plus synchronous local runtime; overlap none"}
        result = {"index": index, "name": name,
            "changed_after_first": changed_after_first, "seed": SEED, "goal": goal,
            "navigate_terminal": first(navigate["reply"]["records"], "terminal"),
            "source_observation": source, "source_image_sha256": source_frame_digest,
            "grounding_model": model_record, "mint": mint_report,
            "adaptive": adaptive, "compiled_runtime": runtime_receipt,
            "runtime_events": runtime_events, "raw_evidence": raw_evidence,
            "action_records": action_records, "intervention": intervention,
            "independent_evaluation": evaluation, "actual": actual,
            "bridge_exit_code": code, "durable_calls": len(calls),
            "planner_boundaries": 1, "model_visible_images": 1,
            "local_observation_presentations": len(raw_evidence),
            "timings": timings,
            "raw_evidence_retention_verified": all(
                (root / row["normalized"]["evidence_ref"]).exists()
                and sha(root / row["normalized"]["evidence_ref"]) == row["image_sha256"]
                for row in raw_evidence)}
        dump(root / "result.json", result)
        return result
    except Exception as error:
        dump(root / "error.json", {"type": type(error).__name__,
                                    "detail": str(error), "retry": False})
        raise
    finally:
        if journal.exists():
            shutil.copy2(journal, root / "journal.jsonl")
        if process.poll() is None:
            process.terminate(); process.wait(timeout=10)
        errors.close(); temporary.cleanup()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    preflight = require_compatible(
        [{"name": "compiled-form-grounding", "schema": SCHEMA}],
        HERE / "results/schema-preflight-cache-v1", OUT / "preflight",
        OUT / "empty-workspace")
    cases = [run_case(index, **allocation)
             for index, allocation in enumerate(plan["execution_order"], 1)]
    by_name = {row["name"]: row for row in cases}
    changed, positive = by_name["changed-target"], by_name["positive"]
    field_box = [135, 233, 105, 21]
    submit_box = [248, 232, 48, 23]

    def inside(point, box):
        return (box[0] <= point[0] < box[0] + box[2]
                and box[1] <= point[1] < box[1] + box[3])

    positive_runtime = positive.get("compiled_runtime") or {}
    changed_runtime = changed.get("compiled_runtime") or {}
    gates = {
        "schema_preflight": preflight["accepted"] is True,
        "one_grounding_attempt_each": all(
            row["adaptive"]["accounting"]["attempted_calls"] == 1 for row in cases),
        "semantic_points_2_of_2": all(
            inside(row["grounding_model"]["grounding"]["field_point"], field_box)
            and inside(row["grounding_model"]["grounding"]["submit_point"], submit_box)
            for row in cases),
        "positive_two_local_transitions": (
            positive_runtime.get("outcome") == "TASK_SUCCEEDED"
            and positive_runtime.get("completed_transitions") == 2
            and positive_runtime.get("frontier_model_resumptions") == 0
            and [row["action"] for row in positive["action_records"]] ==
                ["enter_token", "submit_form"]
            and positive["independent_evaluation"]["success"] is True
            and positive["actual"] == {"value": [positive["goal"]["token"]]}),
        "changed_stops_second_target_input": (
            changed_runtime.get("outcome") == "SAFE_YIELD"
            and changed_runtime.get("completed_transitions") == 1
            and [row["action"] for row in changed["action_records"]] == ["enter_token"]
            and changed["independent_evaluation"]["success"] is False
            and changed["actual"] == {}),
        "release_and_raw_evidence": (all(
            all(action["terminal"]["release"]["verified"] is True
                for action in row["action_records"]) for row in cases)
            and all(row["raw_evidence_retention_verified"] for row in cases)),
        "no_retry_exit_clean": all(row["bridge_exit_code"] == 0 for row in cases),
    }
    gates["passed"] = all(gates.values())
    usage = {row["name"]: row["grounding_model"]["usage"] for row in cases}
    preflight_result = preflight["results"][0]["result"]
    attempt_ledger = [{"kind": "schema_preflight",
        "performed": preflight_result["model_call_performed"],
        "usage": preflight_result["usage"],
        "cached_first_observation": preflight_result.get("cached_first_observation")}] + [
        {"kind": "grounding", "case": row["name"], "performed": True,
         "call_id": row["grounding_model"]["call_id"],
         "usage": row["grounding_model"]["usage"]} for row in cases]
    performed = [row for row in attempt_ledger if row["performed"]]
    usage_fields = ["input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "output_tokens", "reasoning_output_tokens"]
    actual_usage_totals = {field: (sum(row["usage"][field] for row in performed)
        if all(row["usage"] is not None and field in row["usage"] for row in performed)
        else None) for field in usage_fields}
    report = {"passed": gates["passed"], "promotion_gates": gates,
              "preflight": preflight, "cases": cases,
              "grounding_usage": usage, "all_model_attempt_ledger": attempt_ledger,
              "actual_performed_model_usage_totals": actual_usage_totals,
              "independent_point_boxes": {"field": field_box, "submit": submit_box},
              "field_effect_crop": [62, 233, 185, 21],
              "field_changed_pixel_threshold": 40,
              "decision": ("ADVANCE_TO_MATCHED_EFFICIENCY_COMPARISON" if gates["passed"]
                           else "HOLD_COMPILED_INTERFACE_AND_PRESERVE_FAILURE"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps({"passed": report["passed"], "decision": report["decision"],
                      "grounding_usage": usage,
                      "actual_performed_model_usage_totals": actual_usage_totals}, indent=2))


if __name__ == "__main__":
    main()
