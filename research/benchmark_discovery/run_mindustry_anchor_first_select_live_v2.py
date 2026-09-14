"""Select Mindustry Conveyor through one verified active semantic receipt."""
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from anchor_evidence_contract_v1 import validate as validate_anchor
from compact_hover_sheet_v2 import build as build_compact
from uncertain_target_contract_v1 import validate as validate_uncertain
from unix_json_deadline import exchange
import run_openttd_active_evidence_pair_v1 as model_runtime

from mindustry_conveyor_selection_oracle_v1 import score as score_selection
from mindustry_palette_hover_receipt_v1 import verify as verify_hover
from mindustry_palette_slots_v1 import discover, nearest


OUT = HERE / "results/mindustry-anchor-first-select-live-02"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
model_runtime.WORKSPACE = OUT / "empty-workspace"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    assert model_runtime.sha(HERE / plan["prior_failure"]) == plan["prior_failure_sha256"]
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("live_control/") else HERE / name
        assert model_runtime.sha(path) == digest, name
    assert model_runtime.sha(HERE / plan["reference_image"]) == plan["reference_sha256"]
    root = OUT / "live-fixed-palette"
    root.mkdir()
    stderr = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "mindustry_socket_v2.py"), "serve", "--",
        "--root", LINUX_ROOT, "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    cursor = 0
    calls = []

    def query(events, command=None, timeout=30):
        nonlocal cursor
        request = {"after": cursor, "events": events, "timeout": timeout}
        if command is not None:
            request.update(command=command, request_id=uuid.uuid4().hex)
        begin = time.perf_counter_ns()
        reply = exchange(endpoint["socket"], request, timeout=timeout + 3)
        calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(),
                      "request": request, "reply": reply})
        cursor = reply.get("cursor", cursor)
        dump(root / "calls.json", calls)
        return reply

    def submit(identifier, steps, lifetime_ns=20_000_000_000):
        clock_reply = query(["clock"], {"op": "clock"}, timeout=3)
        clock = next(row for row in clock_reply["records"] if row.get("event") == "clock")
        return query(["terminal"], {"op": "submit", "id": identifier,
            "expected_sequence": clock["sequence"],
            "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
            "steps": steps}, timeout=20)

    try:
        endpoint = json.loads(process.stdout.readline())
        dump(root / "endpoint.json", endpoint)
        initial_reply = query(["observation"], timeout=30)
        source = next(row for row in initial_reply["records"]
                      if row.get("event") == "observation")
        source_path = root / "runtime" / Path(source["image"]).name
        decision_start_ns = time.perf_counter_ns()
        candidate_model = model_runtime.model_call(
            root, "model-candidate", plan["task"] +
            " Identify the visible palette target or request active hover evidence.",
            source_path, "../benchmark_discovery/mindustry_palette_target_responder_v1.txt",
            "uncertain_target_contract_schema_v1.json")
        with Image.open(source_path) as image:
            width, height = image.size
        candidate = validate_uncertain(candidate_model["typed"], width, height)
        if candidate["op"] == "target_reference":
            raw = candidate_model["typed"]["point"]
            coarse = [raw["x"], raw["y"]]
            anchor_basis = "model direct point"
        else:
            coarse = candidate["points"][0]
            anchor_basis = "model first-ranked probe point"
        detect_start_ns = time.perf_counter_ns()
        structure = discover(source_path)
        detection_ms = (time.perf_counter_ns() - detect_start_ns) / 1e6
        normalized = nearest(coarse, structure["slots"])
        anchor_point = normalized["point"]
        anchor_steps = [{"op": "pointer_move", "x": anchor_point[0], "y": anchor_point[1]},
                        {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                        {"op": "observe"}]
        hover_begin_ns = time.perf_counter_ns()
        hover_reply = submit("hover-anchor", anchor_steps)
        hover_return_ns = time.perf_counter_ns()
        readiness = verify_hover(hover_reply["records"], anchor_steps, anchor_point,
                                 structure["tooltip_box"], root / "runtime", source_path)
        receipt_ready_ns = time.perf_counter_ns()
        hover_observations = [row for row in hover_reply["records"]
                              if row.get("event") == "observation" and row.get("step") == 1]
        accepted = next(row for row in hover_reply["records"] if row.get("event") == "accepted")
        first_useful = hover_observations[0]
        anchor_image = root / "anchor-presentation.png"
        manifest = build_compact(readiness, root / "runtime", anchor_image)
        anchor_model = model_runtime.model_call(
            root, "model-anchor-evidence", plan["task"] +
            " Determine whether this verified hover receipt identifies Conveyor.",
            anchor_image, "anchor_evidence_responder_v1.txt",
            "anchor_evidence_contract_schema_v1.json")
        decision = validate_anchor(anchor_model["typed"], readiness)
        selection_ns = time.perf_counter_ns()
        if decision["status"] != "EVIDENCE_BOUND":
            raise ValueError("fresh Mindustry anchor requires expansion; no click issued")
        pre_click_image = root / "runtime" / Path(
            next(row for row in reversed(hover_reply["records"])
                 if row.get("event") == "observation")["image"]).name
        pre_click_oracle = score_selection(pre_click_image)
        if pre_click_oracle["success"]:
            raise ValueError("hover-only state unexpectedly scores as selected")
        x, y = decision["point"]
        click_steps = [{"op": "pointer_click", "x": x, "y": y, "duration_ms": 40},
                       {"op": "pointer_move", "x": 640, "y": 400},
                       {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                       {"op": "observe"}]
        click_reply = submit("select-conveyor", click_steps)
        final = next(row for row in reversed(click_reply["records"])
                     if row.get("event") == "observation")
        final_path = root / "runtime" / Path(final["image"]).name
        oracle = score_selection(final_path)
        evaluation_ns = time.perf_counter_ns()
        finish = query(["independent_evaluation"], {"op": "finish"}, timeout=30)
        code = process.wait(timeout=30)
        runtime_events = [json.loads(line) for line in
                          (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
        button_downs = [row for row in runtime_events if row.get("event") == "pointer_admission"
                        and row.get("operation") == "button_down"]
        result = {"source": source, "candidate_model": candidate_model,
                  "candidate_decision": candidate, "anchor_basis": anchor_basis,
                  "coarse_point": coarse, "palette_structure": structure,
                  "normalization": normalized, "anchor_steps": anchor_steps,
                  "hover_reply": hover_reply, "anchor_readiness": readiness,
                  "anchor_manifest": manifest, "anchor_model": anchor_model,
                  "anchor_decision": decision, "pre_click_oracle": pre_click_oracle,
                  "click_steps": click_steps, "click_reply": click_reply,
                  "final_observation": final, "selection_oracle": oracle,
                  "all_button_down_admissions": button_downs,
                  "driver_evaluation": next(row for row in finish["records"]
                                             if row.get("event") == "independent_evaluation"),
                  "bridge_exit_code": code, "socket_exchanges": len(calls),
                  "timing_ms": {"palette_detection": detection_ms,
                    "hover_submit_to_return": (hover_return_ns - hover_begin_ns) / 1e6,
                    "hover_accept_to_first_useful_image_ready":
                        (first_useful["image_ready_ns"] - accepted["accepted_ns"]) / 1e6,
                    "decision_start_to_receipt_ready":
                        (receipt_ready_ns - decision_start_ns) / 1e6,
                    "decision_start_to_semantic_selection":
                        (selection_ns - decision_start_ns) / 1e6,
                    "decision_start_to_selection_oracle":
                        (evaluation_ns - decision_start_ns) / 1e6}}
        gate = {"one_verified_anchor": len(readiness["receipts"]) == 1,
                "strict_evidence_bound": decision["status"] == "EVIDENCE_BOUND",
                "hover_only_not_selected": pre_click_oracle["success"] is False,
                "one_final_button_down": len(button_downs) == 1 and
                    button_downs[0]["id"] == "select-conveyor",
                "released_click": next(row for row in click_reply["records"]
                    if row.get("event") == "terminal")["release"]["verified"] is True,
                "independent_selection_oracle": oracle["success"] is True,
                "bridge_exit_zero": code == 0}
        gate["passed"] = all(gate.values())
        report = {"result": result, "promotion_gate": gate,
                  "reported_input_tokens": {
                      "candidate": candidate_model["usage"]["input_tokens"],
                      "anchor_evidence": anchor_model["usage"]["input_tokens"]},
                  "decision": ("RETAIN_MINDUSTRY_ANCHOR_TRANSFER" if gate["passed"]
                               else "HOLD_MINDUSTRY_ANCHOR_TRANSFER"),
                  "scope": plan["scope"]}
        dump(root / "result.json", result)
        dump(OUT / "report.json", report)
        print(json.dumps(report, indent=2))
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        stderr.close()


if __name__ == "__main__":
    main()
