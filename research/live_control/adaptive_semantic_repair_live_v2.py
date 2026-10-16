"""Two-case live integration of adaptive acquisition caller v3."""
import contextlib
import json
import shutil
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from adaptive_acquisition_caller_v3 import ModelFailure, run as run_adaptive


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-semantic-repair-live-02"


def wait_terminal(events, identifier):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        row = next((item for item in reversed(events)
                    if item.get("event") == "terminal" and item.get("id") == identifier), None)
        if row is not None:
            return row
        time.sleep(.001)
    raise RuntimeError("terminal missing: " + identifier)


def inside(point, box):
    return box[0] <= point[0] < box[2] and box[1] <= point[1] < box[3]


def run_case(plan, root, ordinal, mode):
    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from post_model_target_revalidation_v1 import receipt as post_model_receipt
    from release_event_socket_v3 import ReleaseEventSocket
    from scoped_target_handle_v1 import TargetHandleStore
    from semantic_grounding_admission_v1 import admit as admit_grounding
    from semantic_probe_backend_v3 import Backend, suite
    from semantic_repair_model_v2 import invoke as invoke_model
    from target_handle_semantic_binding_v1 import derive_contract, repair_contract
    from target_relative_crop_semantic_probe_v1 import score_path
    from unix_json_deadline import exchange
    from Xlib import display

    case = root / f"case-{ordinal + 1:02d}-{mode}"
    case.mkdir(); (case / "empty-workspace").mkdir()
    events, actions, model_outcomes = [], [], []
    client = {"feedback": [], "exchanges": []}
    delivery = ReleaseEventSocket(); threads = []
    session = backend = executor = controller = output = app_server = None
    original_geometry = None
    active_store = None
    mutation = None
    submit_action = None

    def emit(row):
        row["runtime_emit_ns"] = time.perf_counter_ns()
        events.append(row); delivery.append(row)

    def exchange_record(request):
        result = {"request": request, "client_started_ns": time.perf_counter_ns()}
        reply = exchange(delivery.path, request, timeout=request["timeout"] + 1)
        result.update(reply=reply, client_returned_ns=time.perf_counter_ns(),
                      response_bytes=len((json.dumps(reply) + "\n").encode()))
        return result

    def receive(action_id):
        after = 0
        for index in range(plan["max_positive_exchanges"]):
            row = exchange_record({"after": after, "events": ["semantic_probe", "terminal"],
                "timeout": 4, "action_id": action_id,
                "request_id": f"adaptive-{ordinal + 1}-{mode}-{index}"})
            client["exchanges"].append(row)
            boundary = row["reply"]["records"][-1]
            if boundary["event"] == "terminal": break
            client["feedback"].append(boundary)
            if boundary["score"]["success"]: break
            after = row["reply"]["cursor"]
        client["completed_ns"] = time.perf_counter_ns()

    def submit(identifier, program):
        submitted_ns = time.perf_counter_ns()
        executor.submit(identifier, program, backend.sequence,
                        time.perf_counter_ns() + 8_000_000_000)
        accepted = next(row for row in events if row.get("event") == "accepted"
                        and row.get("id") == identifier)
        record = {"id": identifier, "program": program, "submitted_ns": submitted_ns,
                  "accepted": accepted, "terminal": wait_terminal(events, identifier)}
        actions.append(record)
        return record

    def prompt():
        return ("The attached current 1280x800 screenshot is a private Chromium form. "
            "Identify one point inside the visible text Value field and the center of "
            "the visible Save button. Declare the fixed bounded method exactly as "
            "required by the schema. Return references only; runtime validation controls input.")

    def ground(label, image):
        outcome = invoke_model(case / label, prompt(), image, case / "empty-workspace")
        admission = admit_grounding(outcome)
        model_outcomes.append({"label": label, "outcome": outcome, "admission": admission})
        return outcome, admission

    def checked_grounding(outcome, admission):
        if not admission["task_mutation_eligible"]:
            raise ModelFailure(admission["reason"],
                visible_images_submitted=outcome.get("visible_images_submitted"),
                wait_ns=(None if outcome.get("caller_elapsed_ms") is None else
                         round(outcome["caller_elapsed_ms"] * 1_000_000)),
                typed_status=outcome["status"])
        grounding = outcome["result"]["grounding"]
        if not inside(grounding["field_point"], plan["field_box"]):
            raise RuntimeError("model field point outside independent box")
        if not inside(grounding["submit_point"], plan["submit_box"]):
            raise RuntimeError("model submit point outside independent box")
        return grounding

    def mint_reference(store, grounding, observation, image, handle_id):
        point = grounding["submit_point"]
        box = [point[0] - 20, point[1] - 9, 42, 18]
        mint = store.mint("save_form", "window_content", box, observation, image,
            time.perf_counter_ns(), ttl_ms=60000, freshness_ms=3000,
            search_radius=0, allowed_transformations=("window_translation",))
        relation = {"schema": "target-semantic-region-relation-v1",
            "anchor": "target_box_origin",
            "offset": [plan["semantic_screen_box"][0] - box[0],
                       plan["semantic_screen_box"][1] - box[1]],
            "size": [plan["semantic_screen_box"][2] - plan["semantic_screen_box"][0],
                     plan["semantic_screen_box"][3] - plan["semantic_screen_box"][1]]}
        return mint, relation

    def resolve(store, mint, observation, image):
        return store.resolve_point(mint["handle"], [20, 9], observation, image,
                                   time.perf_counter_ns())

    report = {"schema": "adaptive-semantic-repair-live-case-v2",
              "ordinal": ordinal, "mode": mode, "seed": plan["seed"],
              "status": "STARTED", "retry_count": 0}
    try:
        with (case / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, app_server = suite.prepare(session, "chromium", plan["seed"],
                                                      plan["chromium"])
            backend = Backend(session, case, emit)
            controller = display.Display(session.name)
        executor = Executor(backend, emit)
        backend.snapshot("initial", 0)
        navigate = submit(f"adaptive-nav-{ordinal + 1}", [
            {"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": goal["url"]}, {"op": "key", "key": "Return"},
            {"op": "wait_title", "contains": "AI FORM READY", "timeout_ms": 1500}])
        backend.snapshot("adaptive-pre-entry", 0); pre_entry = events[-1]
        original_geometry = list(pre_entry["pointer_binding"]["geometry"])
        pre_entry_path = case / Path(pre_entry["image"]).name
        initial_outcome, initial_admission = ground("initial-model", pre_entry_path)
        report.update(initial_outcome=initial_outcome, initial_admission=initial_admission,
                      task_mutation_started=False)
        if not initial_admission["task_mutation_eligible"]:
            report.update(status=initial_admission["status"], passed=False,
                          allocation_eligible=False)
            return report
        initial_model = initial_outcome["result"]
        initial_grounding = checked_grounding(initial_outcome, initial_admission)
        fill = submit(f"adaptive-fill-{ordinal + 1}", [
            {"op": "pointer_click", "x": initial_grounding["field_point"][0],
             "y": initial_grounding["field_point"][1], "duration_ms": 80},
            {"op": "chord", "modifier": "Control_L", "key": "a"},
            {"op": "text", "text": goal["token"]}, {"op": "observe"}])
        report["task_mutation_started"] = True
        backend.snapshot("adaptive-source", 0); source = events[-1]
        source_path = case / Path(source["image"]).name
        with Image.open(source_path) as opened: source_image = opened.convert("RGB")
        active_store = TargetHandleStore(f"adaptive-{ordinal + 1}",
                                         lambda: f"initial-save-{ordinal + 1}")
        mint, relation = mint_reference(active_store, initial_grounding, source, source_image,
                                        f"initial-save-{ordinal + 1}")
        initial_resolution = resolve(active_store, mint, source, source_image)
        if not initial_resolution["eligible"]: raise RuntimeError("initial handle did not resolve")
        initial_binding = derive_contract(f"adaptive_completion_{ordinal + 1}",
            "submission_heading", mint, initial_resolution, source, relation,
            plan["expected_crop_sha256"], "submission_title_exactly_visible")
        cached = {"handle": mint["handle"], "mint": mint, "relation": relation,
                  "contract": initial_binding["contract"],
                  "point": initial_resolution["point"], "source_sequence": source["sequence"]}

        if mode == "local":
            window = controller.create_resource_object("window", source["pointer_binding"]["surface"])
            window.configure(width=original_geometry[2] + plan["resize_width_delta"])
            controller.sync()
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                binding = backend.binding()
                if binding.get("geometry", [0, 0, 0])[2] == original_geometry[2] + plan["resize_width_delta"]:
                    break
                time.sleep(.01)
            else: raise RuntimeError("resize missing")
            emit({"event": "test_surface_resized", "before": source["pointer_binding"],
                  "after": binding, "grants_input_authority": False})
        else:
            hover = submit(f"adaptive-hover-{ordinal + 1}", [
                {"op": "pointer_move", "x": initial_resolution["point"][0],
                 "y": initial_resolution["point"][1]},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 700}, {"op": "observe"}])
            if hover["terminal"]["status"] != "completed": raise RuntimeError("hover mutation failed")
        backend.snapshot("adaptive-mutated", 0); mutation = events[-1]
        mutation_path = case / Path(mutation["image"]).name
        with Image.open(mutation_path) as opened: mutation_image = opened.convert("RGB")
        old_score = score_path(initial_binding["contract"], mutation_path,
                               mutation["pointer_binding"])
        if old_score["success"]: raise RuntimeError("mutation did not invalidate old contract")
        recovery_started_ns = time.perf_counter_ns()

        def reuse_revalidate(_target):
            return {"status": "association_changed", "old_reason": old_score["reason"]}

        def local_repair(payload):
            current_resolution = resolve(active_store, payload["target"]["mint"],
                                         mutation, mutation_image)
            if not current_resolution["eligible"]:
                status = str(current_resolution["status"]).lower()
                return {"status": status if status in ("missing", "ambiguous")
                        else "association_changed"}
            repaired = repair_contract(payload["target"]["contract"],
                payload["target"]["mint"], current_resolution, mutation,
                payload["target"]["relation"])
            target = {**payload["target"], "contract": repaired["contract"],
                      "point": current_resolution["point"],
                      "source_sequence": mutation["sequence"]}
            return {"status": "repaired", "target": target,
                    "receipt": repaired["receipt"], "model_calls": 0,
                    "grants_semantic_authority": False,
                    "grants_input_authority": False}

        def expanded_model(_payload):
            outcome, admission = ground("repair-model", mutation_path)
            grounding = checked_grounding(outcome, admission)
            result = outcome["result"]
            target = {"grounding": grounding, "model_source_sequence": mutation["sequence"]}
            return {"call_id": result["call_id"],
                    "output": {"status": "target_reference", "target": target},
                    "usage": result["usage"], "requested_model": result["requested_model"],
                    "requested_effort": result["requested_effort"], "cost": None,
                    "visible_images_submitted": outcome["visible_images_submitted"],
                    "wait_ns": round(outcome["caller_elapsed_ms"] * 1_000_000)}

        def post_model_observe(_payload):
            backend.snapshot("adaptive-post-model-current", 0)
            return events[-1]

        def post_model_revalidate(payload):
            nonlocal active_store
            current = payload["current_observation"]
            current_path = case / Path(current["image"]).name
            with Image.open(current_path) as opened: current_image = opened.convert("RGB")
            new_store = TargetHandleStore(f"adaptive-reacquired-{ordinal + 1}",
                                          lambda: f"reacquired-save-{ordinal + 1}")
            new_mint, new_relation = mint_reference(new_store, payload["target"]["grounding"],
                                                    mutation, mutation_image,
                                                    f"reacquired-save-{ordinal + 1}")
            current_resolution = resolve(new_store, new_mint, current, current_image)
            if not current_resolution["eligible"]:
                status = str(current_resolution["status"]).lower()
                return {"status": status if status in ("missing", "ambiguous")
                        else "association_changed"}
            receipt = post_model_receipt(new_mint, current_resolution, mutation, current,
                                         payload["model_call_id"])
            derived = derive_contract(f"adaptive_completion_{ordinal + 1}",
                "submission_heading", new_mint, current_resolution, current, new_relation,
                plan["expected_crop_sha256"], "submission_title_exactly_visible")
            active_store = new_store
            target = {"handle": new_mint["handle"], "mint": new_mint,
                      "relation": new_relation, "contract": derived["contract"],
                      "point": current_resolution["point"],
                      "source_sequence": current["sequence"]}
            return {"status": "current_patch_match", "target": target,
                    "receipt": receipt, "model_call_id": payload["model_call_id"],
                    "grants_semantic_authority": False,
                    "grants_input_authority": False}

        def final_revalidate(target):
            backend.snapshot("adaptive-final-current", 0); current = events[-1]
            current_path = case / Path(current["image"]).name
            with Image.open(current_path) as opened: current_image = opened.convert("RGB")
            current_resolution = resolve(active_store, target["mint"], current, current_image)
            if not current_resolution["eligible"]:
                status = str(current_resolution["status"]).lower()
                return {"status": status if status in ("missing", "ambiguous")
                        else "association_changed"}
            score = score_path(target["contract"], current_path, current["pointer_binding"])
            if (score["success"] or score["reason"] != "expected_crop_missing" or
                    score["binding_status"] not in ("CURRENT_EXACT", "CURRENT_TRANSLATED") or
                    score["observed_crop_sha256"] is None):
                return {"status": "association_changed"}
            return {"status": "revalidated", "target": {**target,
                    "point": current_resolution["point"],
                    "source_sequence": current["sequence"],
                    "pre_action_score": score}}

        def execute(payload):
            nonlocal submit_action
            action_id = f"adaptive-submit-{ordinal + 1}-{mode}"
            backend.register_semantic_probe(action_id, payload["target"]["contract"])
            before = len(delivery.request_receipts())
            thread = threading.Thread(target=receive, args=(action_id,)); threads.append(thread)
            thread.start()
            if not delivery.wait_requests(before + 1): raise RuntimeError("semantic client missing")
            submit_action = submit(action_id, [
                {"op": "pointer_click", "x": payload["target"]["point"][0],
                 "y": payload["target"]["point"][1], "duration_ms": 80},
                {"op": "wait_title", "contains": "AI FORM SAVED", "timeout_ms": 1500},
                {"op": "observe"}])
            thread.join(4)
            if thread.is_alive(): raise RuntimeError("semantic client timed out")
            return {"status": "completed" if submit_action["terminal"]["status"] == "completed"
                    else "failed"}

        def verify_effect(_payload):
            actual = parse_qs(output.read_text()) if output.exists() else {}
            useful = next((row for row in client["feedback"] if row["score"]["success"]), None)
            return {"status": "succeeded" if actual == {"value": [goal["token"]]}
                    and useful is not None else "failed"}

        adaptive = run_adaptive({"target": "submit the exact task token", "route": "reuse",
            "coarse_origin": "caller_provided", "provided_coarse": None,
            "cached_target": cached, "local_repair_on": ["association_changed"],
            "repair_on": ["missing", "ambiguous", "association_changed"],
            "session_id": f"adaptive-live-{ordinal + 1}"}, {
            "reuse_revalidate": reuse_revalidate, "local_repair": local_repair,
            "acquire_expansion": lambda payload: {"observation": mutation,
                                                    "image": mutation["image"]},
            "expanded_model": expanded_model, "post_model_observe": post_model_observe,
            "post_model_revalidate": post_model_revalidate,
            "final_revalidate": final_revalidate, "execute": execute,
            "verify_effect": verify_effect})
        recovery_completed_ns = time.perf_counter_ns()
        actual = parse_qs(output.read_text()) if output.exists() else {}
        useful = next((row for row in client["feedback"] if row["score"]["success"]), None)
        reconciliations = [row for row in events if row.get("event") == "semantic_probe_reconciled"]
        completed_model_records = [initial_model] + [row for row in adaptive["model_call_ledger"]]
        total_input = sum(row["usage"]["input_tokens"] for row in completed_model_records)
        expected_path = "local" if mode == "local" else "model_reacquisition"
        checks = {
            "old_contract_invalid": old_score["success"] is False,
            "expected_repair_path": adaptive["repair_path"] == expected_path,
            "expected_calls": len(completed_model_records) == plan["expected_model_calls"][mode],
            "correct": adaptive["outcome"] == "TASK_SUCCEEDED" and
                       actual == {"value": [goal["token"]]},
            "useful_feedback": useful is not None,
            "reconciled": useful is not None and any(row["sequence"] == useful["sequence"]
                                                      for row in reconciliations),
            "released": all(row["terminal"]["release"]["verified"] is True and
                row["terminal"]["release"]["keys_down"] == [] and
                row["terminal"]["release"]["buttons_down"] == [] for row in actions),
            "programs_attested": all(row["accepted"]["program_sha256"] ==
                                      program_sha256(row["program"]) for row in actions),
            "no_retry": report["retry_count"] == 0,
            "accounted_images": adaptive["accounting"]["visible_image_coverage"] ==
                                adaptive["accounting"]["attempted_calls"],
            "accounted_wait": adaptive["accounting"]["model_wait_coverage"] ==
                              adaptive["accounting"]["attempted_calls"]}
        metrics = {"mutation_capture_to_caller_return_ms":
                   (recovery_completed_ns - mutation["capture_ns"]) / 1e6,
                   "adaptive_model_wait_ms": (adaptive["accounting"]["model_wait_ns"] or 0) / 1e6,
                   "total_input_tokens": total_input,
                   "total_model_calls": len(completed_model_records),
                   "model_visible_images": initial_outcome["visible_images_submitted"] +
                       (adaptive["accounting"]["visible_images_submitted"] or 0),
                   "client_exchanges": len(client["exchanges"])}
        report.update(status="COMPLETED", passed=all(checks.values()), checks=checks,
            goal=goal, source_observation=source, mutation_observation=mutation,
            mutation_kind="window_resize" if mode == "local" else "button_hover",
            old_contract_score=old_score, initial_mint=mint,
            initial_resolution=initial_resolution, adaptive=adaptive,
            model_outcomes=model_outcomes, actual=actual, actions=actions,
            client=client, reconciliations=reconciliations, metrics=metrics,
            retry_count=0, allocation_eligible=True)
        return report
    except Exception as error:
        report.update(status="FAILED", passed=False, error=repr(error))
        return report
    finally:
        for thread in threads:
            if thread.is_alive(): thread.join(1)
        if executor is not None: executor.close()
        if controller is not None and original_geometry is not None:
            try:
                binding = backend.binding()
                window = controller.create_resource_object("window", binding["surface"])
                window.configure(x=original_geometry[0], y=original_geometry[1],
                    width=original_geometry[2], height=original_geometry[3]); controller.sync()
            except Exception: pass
            controller.close()
        if backend is not None:
            try: backend.close()
            finally: (case / "owner-events.json").write_text(
                json.dumps(backend.owner.records, indent=2) + "\n")
        if output is not None and output.exists(): shutil.copy2(output, case / output.name)
        if app_server is not None: app_server.shutdown(); app_server.server_close()
        if session is not None: session.close(); shutil.rmtree(session.tmp)
        delivery.close()
        (case / "events.json").write_text(json.dumps(events, indent=2) + "\n")
        (case / "report.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    if OUT.exists(): raise RuntimeError("formal output already exists")
    plan = json.loads((HERE / "adaptive_semantic_repair_live_v2_prereg.json").read_text())
    OUT.mkdir(parents=True)
    results = []
    for ordinal, mode in enumerate(plan["order"]):
        result = run_case(plan, OUT, ordinal, mode); results.append(result)
        if result.get("status") != "COMPLETED" or result.get("passed") is not True: break
    report = {"schema": "adaptive-semantic-repair-live-report-v2",
              "passed": len(results) == len(plan["order"]) and all(r["passed"] for r in results),
              "results": results,
              "scope": plan["scope"]}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"],
        "cases": [(row["mode"], row["status"], row.get("passed")) for row in results]}, indent=2))


if __name__ == "__main__": main()
