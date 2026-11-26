"""Exercise the native comparison verifier using a complete synthetic 17-call block."""

import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from research.live_control.integrated_efficiency_app_server_model_v1 import USAGE_MAP
from research.live_control.integrated_efficiency_protocol_v1 import ARMS, EXPECTED_ROUTES, TASKS
from research.live_control.native_preflight_job_v1 import JOB_KILL_EXIT_CODE
from runtime import native_comparison_audit_v1 as audit
from runtime.test_native_comparison_candidate_v1 import stage_fake_effects


SOURCE = Path(__file__).resolve().parents[1]
SEED = 991035
NATIVE = {"windows_path": r"C:\synthetic\codex.exe", "version": "codex-cli synthetic",
          "executable_sha256": "a" * 64}
WINDOWS_OUT = PureWindowsPath(r"C:\synthetic\allocation")
WINDOWS_REPO = PureWindowsPath(r"C:\synthetic\source")
GROUNDING_PROMPT = "Locate the editable token field and the control that submits this visible form. "
PREFLIGHT_PROMPT = "Schema compatibility probe. Produce any object accepted by the supplied schema."


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8", newline="\n")


def lines(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join((json.dumps(value) + "\n").encode() for value in values))


def usage(tokens):
    return {"input_tokens": tokens, "cached_input_tokens": 4, "cache_write_input_tokens": 0,
            "output_tokens": 9, "reasoning_output_tokens": 3}


def job_receipt(schema, owner, completed):
    return {"schema": schema, "ownership": "create-process-job-list", "job_empty": True,
            "status": "COMPLETED" if completed else "STOP_REQUESTED",
            "exit_code": 0 if completed else JOB_KILL_EXIT_CODE, "active_processes": 0,
            "total_processes": 3, "termination_requested": not completed,
            **{key: owner[key] for key in ("run_nonce", "owner_sha256")}}


def answer_for(contract):
    point = {"point_space": "source_observation_pixels", "point": {"x": 24, "y": 26}}
    if contract == "plain":
        return {"format": "plain-form-points-v1", "field": point, "submit": point}
    point = {**point, "motion_model": "surface_origin_translation"}
    return {"format": "compiled-form-grounding-v1", "field": point, "submit": point,
            "method": {"first_action": "enter_exact_token",
                       "continue_when": "field_pixels_changed_and_submit_revalidated",
                       "second_action": "activate_submit",
                       "complete_when": "submission_pixels_changed_then_independent_score"}}


class SyntheticCapture:
    def __init__(self, root):
        self.repo = root / "source"
        self.out = root / "raw"
        self.registration_path = root / "registration.json"
        for relative in audit.REQUIRED_ASSETS:
            destination = self.repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / relative, destination)
        for command in (["init", "--quiet"], ["add", "--all"],
                        ["-c", "user.email=fixture@example.invalid", "-c", "user.name=Test Fixture",
                         "commit", "--quiet", "-m", "synthetic source"]):
            subprocess.run(["git", "-C", str(self.repo), *command], check=True, capture_output=True, timeout=15)
        self.plan = audit.registration_values(self.repo, self.out, SEED, native=NATIVE,
                    windows_repo=str(WINDOWS_REPO), windows_out=str(WINDOWS_OUT))
        write(self.registration_path, self.plan)
        self.registration_digest = audit.digest(self.registration_path)
        write(self.out / "capture-plan.json",
              audit.capture_plan_values(SEED, self.plan, self.registration_digest))
        write(self.out / "capture.json", {"arms": dict.fromkeys(ARMS, "captured")})

    def exec_arm(self, arm, contract, answer, arm_index):
        preflight = self.out / "preflight" / arm
        name = contract + "-form-grounding"
        gate = preflight / "gate"
        base = gate / name
        raw = base / "model-call"
        pin = self.plan["source"]["files"]
        identity = {"schema_sha256": pin[str(audit.SCHEMAS[contract])],
                    "runner_sha256": pin[str(audit.EXEC_RUNNER)],
                    "instructions_sha256": pin[str(audit.PREFLIGHT_RESPONDER)],
                    "windows_owner_sha256": pin[str(audit.EXEC_OWNER)],
                    "windows_app_server_owner_sha256": pin[str(audit.APP_OWNER)],
                    "requested_model": "gpt-5.6-luna", "requested_effort": "low",
                    "cli_windows_path": NATIVE["windows_path"], "cli_version": NATIVE["version"],
                    "cli_executable_sha256": NATIVE["executable_sha256"],
                    "cli_transport": "windows-native-codex-exe",
                    "request_shape": "target_handle_model_runner_v2.py:handle:no-image:output-schema",
                    "usage_policy": "native-cache-write-optional-v1"}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        owner = {"run_nonce": f"{arm_index + 1:032x}", "owner_sha256": pin[str(audit.EXEC_OWNER)]}
        receipt = job_receipt("native-preflight-windows-job-v1", owner, True)
        result = {"compatibility_key": key, "identity": identity, "cache_hit": False,
                  "model_call_performed": True, "endpoint_status": "ENDPOINT_COMPATIBLE",
                  "windows_job": receipt, "usage": usage(20)}
        write(base / audit.START_RECORD, owner)
        write(base / audit.RECEIPT, receipt)
        write(base / "preflight-result.json", result)
        write(gate / "gate-report.json", {"accepted": True, "model_calls": 1,
                                          "results": [{"name": name, "result": result}]})
        write(preflight / "fresh-cache" / (key + ".json"), {**result, "observed_at_unix_ns": 100})
        write(raw / "process.json", {"exit_code": 0, "mode": "handle",
                                      "requested_model": "gpt-5.6-luna", "requested_effort": "low"})
        (raw / "prompt.txt").write_bytes(PREFLIGHT_PROMPT.encode())
        write(raw / "plan.json", {
            **{key: identity[key] for key in ("requested_model", "requested_effort", "runner_sha256",
                                             "schema_sha256", "instructions_sha256")},
            "args": audit.preflight_argv(self.plan, arm, contract), "mode": "handle",
            "image_sha256": None, "prompt_sha256": hashlib.sha256(PREFLIGHT_PROMPT.encode()).hexdigest(),
        })
        call_id = f"exec-{arm}"
        events = [{"type": "thread.started", "thread_id": call_id}, {"type": "turn.started"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(answer)}},
                  {"type": "turn.completed", "usage": usage(20)}]
        lines(raw / "events.jsonl", events)
        lines(raw / "arrivals.jsonl", [
            {"line": i, "bytes": len(line), "sha256": hashlib.sha256(line).hexdigest()}
            for i, line in enumerate((raw / "events.jsonl").read_bytes().splitlines(keepends=True))
        ])
        write(self.out / "capture-arms" / arm / "preflight-result.json",
              {"call_id": call_id, "stage": "schema_preflight", "model_visible_images": 0,
               "requested_model": "gpt-5.6-luna", "requested_effort": "low", "usage": usage(20)})

    def populate(self, persistent_tokens=20):
        for arm_index, arm in enumerate(ARMS):
            base_ns = arm_index * 100_000
            (self.out / "workspaces" / arm).mkdir(parents=True)
            contract = "plain" if arm == "plain" else "compiled"
            answer = answer_for(contract)
            self.exec_arm(arm, contract, answer, arm_index)
            stage_fake_effects(self.out, arm, SEED)
            runtime = self.out / "arms" / arm / "runtime"
            history = runtime / "submission-history.jsonl"
            lines(history, [{**json.loads(line), "received_ns": base_ns + i * 1000 + 120}
                            for i, line in enumerate(history.read_bytes().splitlines(), start=1)])
            session = self.out / "native-app-server" / arm
            owner = {"run_nonce": f"{arm_index + 11:032x}", "windows_executable": NATIVE["windows_path"],
                     "owner_sha256": self.plan["source"]["files"][str(audit.APP_OWNER)]}
            write(session / audit.APP_SERVER_JOB_START, owner)
            write(session / audit.APP_SERVER_JOB_RECEIPT,
                  job_receipt("native-app-server-windows-job-v1", owner, False))
            stream = [{"direction": "windows_job_owner", "message": owner}]

            def send(method, params, result=None):
                request = {"method": method, "params": params}
                if result is not None:
                    request["id"] = len(stream)
                stream.extend([{"direction": direction, "message": request}
                               for direction in ("send_prepared", "sent")])
                if result is not None:
                    stream.append({"direction": "received", "message": {"id": request["id"], "result": result}})

            send("initialize", {}, {"platformFamily": "windows"})
            send("initialized", {})
            for i, row in enumerate(stream):
                row["observed_ns"] = base_ns + 101 + i
            tasks, details, observations = [], [], []
            ready_tasks = [{"task_id": task, "token": f"t{SEED:06d}-{i}",
                            "layout": "A" if i < 4 else "B",
                            "phase": ("cold" if i == 1 else "warm" if i < 4 else
                                      "invalidation_repair" if i == 4 else "post_repair_warm"),
                            "url": f"http://127.0.0.1:16534/task/{i}"}
                           for i, task in enumerate(TASKS, start=1)]
            observations.append({"event": "ready", "goal": {"tasks": ready_tasks},
                                 "emit_started_ns": base_ns + 150})
            neutral = {"verified": True, "keys_down": [], "buttons_down": []}
            generation = 0
            for i, (task, route) in enumerate(zip(TASKS, EXPECTED_ROUTES[arm], strict=True), start=1):
                calls = []
                repair = route == "repair"
                stamp = base_ns + i * 1000
                source_id, nav_id = f"source-{i}", f"navigation-{i}"
                observation = {"event": "observation", "id": source_id, "sequence": i * 10,
                               "capture_ns": stamp + 20, "image": (runtime / f"{i:03d}.png").as_posix()}
                navigation = [{"op": "chord", "modifier": "Control_L", "key": "l"},
                              {"op": "text", "text": ready_tasks[i - 1]["url"]},
                              {"op": "key", "key": "Return"},
                              {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}]
                observations.extend([
                    {"event": "command", "command": {"op": "submit", "id": nav_id, "steps": navigation}},
                    {"event": "accepted", "id": nav_id, "accepted_ns": stamp + 1},
                    {"event": "terminal", "id": nav_id, "terminal_ns": stamp + 9,
                     "status": "completed", "release": neutral},
                    {"event": "command", "command": {"op": "submit", "id": source_id,
                                                     "steps": [{"op": "observe"}]}},
                    {"event": "accepted", "id": source_id, "accepted_ns": stamp + 10},
                    observation,
                    {"event": "terminal", "id": source_id, "terminal_ns": stamp + 30,
                     "status": "completed", "release": neutral},
                ])
                if route != "reuse":
                    generation += 1
                    slot = self.out / "model-calls" / arm / task / ("repair" if repair else "anchor")
                    attempt = session / "attempts" / f"{generation:02d}"
                    thread, turn = f"thread-{arm}-{i}", f"turn-{arm}-{i}"
                    tokens = usage(persistent_tokens if arm == "persistent" else 20)
                    provider_usage = {"last": {raw: tokens[field] for raw, field in USAGE_MAP.items()}}
                    image = runtime / f"{i:03d}.png"
                    Image.new("RGB", (20, 20), (i * 10, arm_index * 10, 0)).save(image)
                    windows_image = str(WINDOWS_OUT.joinpath(*image.relative_to(self.out).parts))
                    write(slot / "request.json", {"source_image": observation["image"],
                          "provider_image": windows_image, "image_sha256": audit.digest(image)})
                    (slot / "prompt.txt").write_bytes(GROUNDING_PROMPT.encode())
                    write(attempt / "start.json", {"generation": generation, "contract": contract,
                          "started_monotonic_ns": stamp + 40, "result_root": slot.as_posix(),
                          "source_image": observation["image"]})
                    write(attempt / "terminal.json", {"status": "completed", "provider_turn_observed": True,
                          "thread_id": thread, "call_id": turn, "usage": tokens,
                          "result_returned_monotonic_ns": stamp + 54, "finished_monotonic_ns": stamp + 56})
                    write(slot / "result.json", {"raw": answer, "usage": tokens, "provider_usage": provider_usage,
                          "turn_status": "completed", "answer_eligible": True, "requested_model": "gpt-5.6-luna",
                          "requested_effort": "low", "thread_id": thread, "call_id": turn, "turn_id": turn})
                    calls = [{"call_id": turn, "stage": "expanded_model" if repair else "anchor_model",
                              "usage": tokens, "requested_model": "gpt-5.6-luna", "requested_effort": "low"}]
                    first_index = len(stream)
                    send("thread/start", {"model": "gpt-5.6-luna", "cwd": str(WINDOWS_OUT / "workspaces" / arm),
                         "approvalPolicy": "never", "sandbox": "read-only", "ephemeral": True,
                         "threadSource": "exec", "config": {"project_doc_max_bytes": 0,
                                                             "model_reasoning_effort": "low"},
                         "baseInstructions": (self.repo / audit.RESPONDERS[contract]).read_text(encoding="utf-8")},
                         {"thread": {"id": thread, "cwd": str(WINDOWS_OUT / "workspaces" / arm)},
                          "cwd": str(WINDOWS_OUT / "workspaces" / arm), "approvalPolicy": "never",
                          "sandbox": {"type": "readOnly", "networkAccess": False},
                          "model": "gpt-5.6-luna", "reasoningEffort": "low"})
                    send("turn/start", {"threadId": thread, "model": "gpt-5.6-luna", "effort": "low",
                         "outputSchema": audit.read(self.repo / audit.SCHEMAS[contract]),
                         "input": [{"type": "text", "text": GROUNDING_PROMPT, "text_elements": []},
                                   {"type": "localImage", "path": windows_image}]}, {"turn": {"id": turn}})
                    stream.extend([{"direction": "received", "message": {"method": "turn/started",
                                   "params": {"threadId": thread, "turn": {"id": turn, "status": "inProgress"}}}},
                                   {"direction": "received", "message": {"method": "thread/tokenUsage/updated",
                                   "params": {"threadId": thread, "turnId": turn, "tokenUsage": provider_usage}}},
                                   {"direction": "received", "message": {"method": "turn/completed", "params": {
                                       "threadId": thread, "turn": {"id": turn, "status": "completed",
                                       "items": [{"type": "agentMessage", "text": json.dumps(answer)}]}}}}])
                    for j, row in enumerate(stream[first_index:]):
                        row["observed_ns"] = stamp + 41 + j
                row = {"arm": arm, "task_id": task, "layout": "A" if i < 4 else "B", "route": route,
                       "model_calls": calls, "planner_generations": len(calls), "model_visible_images": len(calls),
                       "local_observations": 1, "durable_calls": 1, "pointer_admissions": 2,
                       "old_target_pointer_admissions": 0, "releases_verified": True, "submission_count": 1,
                       "exact_submission": True, "typed_outcome": "completed", "elapsed_ns": i * 1000,
                       "source_to_completion_ns": 100, "input_feedback_ns": [None, None],
                       "repair": {"required": repair, "old_reference_status": "missing" if repair else None,
                                  "old_reference_pointer_admissions": 0, "attempted": repair, "succeeded": repair}}
                tasks.append(row)
                details.append({"trace": row, "source": observation, "program_count": 4 if repair else 3})
                if repair:
                    observations.extend([
                        {"event": "target_handle_checked", "id": "old-check",
                         "handle": "persistent_a_field", "status": "MISSING", "eligible": False,
                         "observation_sequence": i * 10 + 1, "checked_ns": stamp + 35},
                        {"event": "accepted", "id": "different-program", "accepted_ns": stamp + 42},
                        {"event": "terminal", "id": "different-program", "terminal_ns": stamp + 59,
                         "status": "completed", "release": neutral},
                        {"event": "target_handle_minted_from_point", "handle": "persistent_b_field",
                         "status": "VALID", "source_sequence": i * 10, "fresh_sequence": i * 10 + 2,
                         "created_sequence": i * 10 + 2, "minted_ns": stamp + 60, "fresh_patch_exact": True},
                        {"event": "target_handle_minted_from_point", "handle": "persistent_b_submit",
                         "status": "VALID", "source_sequence": i * 10, "fresh_sequence": i * 10 + 3,
                         "created_sequence": i * 10 + 3, "minted_ns": stamp + 70, "fresh_patch_exact": True},
                        {"event": "target_handle_checked", "id": "fresh-check", "handle": "persistent_b_field",
                         "eligible": True, "status": "VALID", "observation_sequence": i * 10 + 4,
                         "checked_ns": stamp + 80},
                    ])
                action_id = f"input-{i}"
                observations.extend([{"event": "accepted", "id": action_id, "accepted_ns": stamp + 91},
                    {"event": "pointer_admission", "id": action_id, "operation": "button_down",
                     "admitted_ns": stamp + 100, "input_ack_ns": stamp + 101},
                    {"event": "pointer_admission", "id": action_id, "operation": "button_down",
                     "admitted_ns": stamp + 110, "input_ack_ns": stamp + 111},
                    {"event": "terminal", "id": action_id, "terminal_ns": stamp + 150,
                     "status": "completed", "release": neutral},
                ])
            for name in ("events.jsonl", "delivered.jsonl"):
                path = runtime / name
                lines(path, observations)
            write(runtime.parent / "task-details.json", details)
            arm_receipts = self.out / "capture-arms" / arm
            write(arm_receipts / "task-results.json",
                  {"tasks": tasks, "independent": {"success": True}})
            write(arm_receipts / "preflight-start.json",
                  {"contract": contract, "started_monotonic_ns": base_ns + 1})
            write(arm_receipts / "arm-timing.json", {
                  "preflight_started_ns": base_ns + 1, "preflight_finished_ns": base_ns + 80,
                  "arm_started_ns": base_ns + 100, "arm_finished_ns": base_ns + 7000})
            write(arm_receipts / "effect-release-audit.json", {"synthetic": True})
            lines(session / "protocol.jsonl", stream)

    def verify(self, seal=None):
        return audit.audit_comparison(self.repo, self.out, self.registration_path,
            registration_sha256=self.registration_digest,
            seal_sha256=audit.seal_capture(self.out) if seal is None else seal)


class NativeComparisonAuditTests(unittest.TestCase):
    def test_complete_native_evidence_uses_observed_usage_for_both_decisions(self):
        for persistent_tokens, expected in ((20, "RETAIN"), (120, "REJECT")):
            with self.subTest(expected=expected), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate(persistent_tokens)
                result = capture.verify()
                self.assertEqual(result["disposition"], expected, result)
                self.assertEqual([r["provider_calls"] for r in result["arms"].values()], [7, 7, 3])
                self.assertEqual(result["arms"]["persistent"]["usage"]["input_tokens"], 20 + 2 * persistent_tokens)

    def test_resealed_wrong_image_extra_send_missing_usage_or_job_do_not_compare(self):
        for flaw in ("image", "extra_send", "unreported_reasoning", "job", "unknown_start",
                     "tool_item", "wrong_thread_ack", "unallocated_session", "detached_observation"):
            with self.subTest(flaw=flaw), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                session = capture.out / "native-app-server" / "ephemeral"
                protocol = session / "protocol.jsonl"
                rows = audit.records(protocol)
                if flaw == "image":
                    for row in rows:
                        if row["message"].get("method") == "turn/start":
                            row["message"]["params"]["input"][1]["path"] = r"C:\other\same-suffix.png"
                elif flaw == "extra_send":
                    rows.append({"direction": "send_prepared", "observed_ns": rows[-1]["observed_ns"] + 1,
                                 "message": {"id": 9999, "method": "turn/start"}})
                elif flaw == "unreported_reasoning":
                    event = next(row for row in rows if row["message"].get("method") == "thread/tokenUsage/updated")
                    del event["message"]["params"]["tokenUsage"]["last"]["reasoningOutputTokens"]
                elif flaw == "job":
                    job = session / audit.APP_SERVER_JOB_RECEIPT
                    write(job, {**audit.read(job), "active_processes": 1})
                elif flaw == "unknown_start":
                    rows.append({"direction": "received", "observed_ns": rows[-1]["observed_ns"] + 1,
                                 "message": {"method": "turn/started",
                                 "params": {"threadId": "outside", "turn": {"id": "unallocated"}}}})
                elif flaw == "tool_item":
                    terminal = next(row for row in rows if row["message"].get("method") == "turn/completed")
                    terminal["message"]["params"]["turn"]["items"].append({"type": "commandExecution"})
                elif flaw == "wrong_thread_ack":
                    ack = next(row["message"]["result"] for row in rows if
                               "thread" in row["message"].get("result", {}))
                    ack["cwd"] = r"C:\other"
                    ack["approvalPolicy"] = "on-request"
                elif flaw == "unallocated_session":
                    lines(capture.out / "workspaces/plain/unallocated-session/protocol.jsonl", rows)
                else:
                    runtime = capture.out / "arms/ephemeral/runtime"
                    for name in ("events.jsonl", "delivered.jsonl"):
                        path = runtime / name
                        events = audit.records(path)
                        first_frame = next(row for row in events if row.get("event") == "observation")
                        events.remove(first_frame)
                        events.append(first_frame)
                        lines(path, events)
                lines(protocol, rows)
                result = capture.verify()
                self.assertEqual(result["disposition"], "HOLD", result)

    def test_confirmed_wrong_effect_or_cross_program_pointer_rejects_but_uncertainty_holds(self):
        for failure, expected in (("wrong_token", "REJECT"), ("pointer", "REJECT"), ("release", "HOLD")):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                runtime = capture.out / "arms/persistent/runtime"
                if failure == "wrong_token":
                    history = runtime / "submission-history.jsonl"
                    events = audit.records(history)
                    events[3]["submitted_values"] = ["wrong"]
                    events[3]["exact"] = False
                    lines(history, events)
                else:
                    for name in ("events.jsonl", "delivered.jsonl"):
                        path = runtime / name
                        events = audit.records(path)
                        if failure == "release":
                            terminal = next(row for row in events if row["event"] == "terminal")
                            terminal["release"]["verified"] = False
                        else:
                            earlier_program = next(i for i, row in enumerate(events)
                                if row.get("event") == "accepted" and row.get("id") == "different-program")
                            events.insert(earlier_program + 1, {"event": "pointer_admission",
                                "operation": "button_down", "id": "different-program",
                                "admitted_ns": events[earlier_program]["accepted_ns"] + 2})
                        lines(path, events)
                report = audit.read(capture.out / "capture.json")
                report["arms"]["persistent"] = "incomplete"
                write(capture.out / "capture.json", report)
                result = capture.verify()
                self.assertEqual(result["disposition"], expected, result)
                if expected == "REJECT":
                    self.assertEqual(result["reason"], "confirmed_persistent_safety_or_effect_failure")

    def test_changed_source_or_changed_raw_after_seal_are_blocked(self):
        for flaw in ("source", "raw"):
            with self.subTest(flaw=flaw), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                seal = audit.seal_capture(capture.out)
                path = capture.repo / audit.EXEC_RUNNER if flaw == "source" else capture.out / "capture.json"
                with path.open("ab") as stream:
                    stream.write(b"\n")
                result = capture.verify(seal)
                self.assertEqual(result["disposition"], "HOLD", result)

    def test_failure_evidence_plan_mismatch_or_exec_tool_item_prevents_retain(self):
        for flaw in ("unallocated_failure", "arm_failure", "unallocated_model_result",
                     "unallocated_arm_receipt", "plan", "exec_tool"):
            with self.subTest(flaw=flaw), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                out = capture.out
                if flaw == "unallocated_failure":
                    write(out / "model-calls/persistent/task-2/anchor/failure.json", {"failed": True})
                elif flaw == "arm_failure":
                    write(out / "capture-arms/persistent/failure.json", {"failed": True})
                elif flaw == "unallocated_model_result":
                    write(out / "model-calls/pilot/task-1/anchor/result.json",
                          {"status": "completed", "usage": usage(20)})
                elif flaw == "unallocated_arm_receipt":
                    write(out / "capture-arms/pilot/task-results.json", {"tasks": []})
                elif flaw == "plan":
                    path = out / "capture-plan.json"
                    write(path, {**audit.read(path), "seed": SEED + 1, "arms": ["persistent"],
                                 "automatic_retry": True, "requested_model": "other"})
                else:
                    home = out / "preflight/plain/gate/plain-form-grounding/model-call"
                    path = home / "events.jsonl"
                    stream = audit.records(path)
                    stream.insert(-1, {"type": "item.completed",
                                       "item": {"type": "command_execution", "command": "synthetic"}})
                    lines(path, stream)
                    lines(home / "arrivals.jsonl", [
                        {"line": i, "bytes": len(line), "sha256": hashlib.sha256(line).hexdigest()}
                        for i, line in enumerate(path.read_bytes().splitlines(keepends=True))])
                result = capture.verify()
                self.assertEqual(result["disposition"], "HOLD", result)
                if flaw == "exec_tool":
                    self.assertIn("unregistered item", result["reason"])

    def test_completed_repair_model_cannot_be_moved_after_its_task_or_next_task(self):
        for shift in (-8, 12, 200, 1500):
            with self.subTest(shift=shift), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                session = capture.out / "native-app-server/persistent"
                protocol = session / "protocol.jsonl"
                stream = audit.records(protocol)
                threads = [i for i, row in enumerate(stream) if row["direction"] == "send_prepared"
                           and row["message"].get("method") == "thread/start"]
                for row in stream[threads[1]:]:
                    row["observed_ns"] += shift
                lines(protocol, stream)
                start = session / "attempts/02/start.json"
                plan = audit.read(start)
                plan["started_monotonic_ns"] += shift
                write(start, plan)
                terminal = session / "attempts/02/terminal.json"
                settled = audit.read(terminal)
                for key in ("result_returned_monotonic_ns", "finished_monotonic_ns"):
                    settled[key] += shift
                write(terminal, settled)
                result = capture.verify()
                self.assertEqual(result["disposition"], "HOLD", result)

    def test_late_usage_cannot_replace_observation_at_return(self):
        for mode, expected in (("moved", "HOLD"), ("changed", "HOLD"), ("identical", "RETAIN")):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                path = capture.out / "native-app-server/persistent/protocol.jsonl"
                stream = audit.records(path)
                first = next(row for row in stream
                             if row["message"].get("method") == "thread/tokenUsage/updated")
                late = json.loads(json.dumps(first))
                late["observed_ns"] = stream[-1]["observed_ns"] + 100
                if mode == "moved":
                    stream.remove(first)
                elif mode == "changed":
                    late["message"]["params"]["tokenUsage"]["last"]["reasoningOutputTokens"] += 1
                lines(path, [*stream, late])
                result = capture.verify()
                self.assertEqual(result["disposition"], expected, result)
                if expected == "HOLD":
                    self.assertIn("unavailable at return or later changed", result["reason"])

    def test_missing_or_crossed_effect_and_arm_clocks_hold(self):
        for flaw in ("missing_receipt_clock", "receipt_before_submit", "overlapping_arms"):
            with self.subTest(flaw=flaw), TemporaryDirectory() as directory:
                capture = SyntheticCapture(Path(directory))
                capture.populate()
                if flaw == "overlapping_arms":
                    receipts = capture.out / "capture-arms" / "ephemeral"
                    path = receipts / "arm-timing.json"
                    write(path, {**audit.read(path), "preflight_started_ns": 6000})
                    path = receipts / "preflight-start.json"
                    write(path, {**audit.read(path), "started_monotonic_ns": 6000})
                else:
                    path = capture.out / "arms/plain/runtime/submission-history.jsonl"
                    history = audit.records(path)
                    if flaw == "missing_receipt_clock":
                        history[0].pop("received_ns")
                    else:
                        history[0]["received_ns"] = 1105
                    lines(path, history)
                self.assertEqual(capture.verify()["disposition"], "HOLD")


if __name__ == "__main__":
    unittest.main()
