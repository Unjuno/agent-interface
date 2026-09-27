"""Run one preregistered palette-to-world Mindustry placement allocation."""
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
from compact_hover_sheet_v2 import build as build_palette_sheet
from bounded_visual_target_contract_v2 import validate as validate_candidate
from unix_json_deadline import exchange
import run_openttd_active_evidence_pair_v1 as model_runtime

from compact_world_receipt_v1 import build as build_world_sheet
from mindustry_conveyor_selection_oracle_v1 import score as score_selection
from mindustry_palette_hover_receipt_v1 import verify as verify_palette
from mindustry_palette_slots_v1 import discover
from mindustry_palette_binding_v2 import bind as bind_palette
from mindustry_world_hover_receipt_v1 import verify as verify_world
from mindustry_world_target_contract_v1 import validate as validate_world

OUT = HERE / "results/mindustry-single-tile-live-02"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
model_runtime.WORKSPACE = OUT / "empty-workspace"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    assert model_runtime.sha(HERE / plan["reference_image"]) == plan["reference_sha256"]
    assert model_runtime.sha(HERE / plan["prior_failure"]) == plan["prior_failure_sha256"]
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("live_control/") else HERE / name
        assert model_runtime.sha(path) == digest, name
    root = OUT / "live-changed-geometry"; root.mkdir()
    stderr = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([sys.executable, "-u", str(HERE / "mindustry_single_tile_socket_v1.py"),
        "serve", "--", "--root", LINUX_ROOT, "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    cursor = 0; calls = []; model_ledger = []; endpoint = None

    def query(events, command=None, timeout=30):
        nonlocal cursor
        request = {"after": cursor, "events": events, "timeout": timeout}
        if command is not None: request.update(command=command, request_id=uuid.uuid4().hex)
        begin = time.perf_counter_ns(); reply = exchange(endpoint["socket"], request, timeout=timeout + 3)
        calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(), "request": request, "reply": reply})
        cursor = reply.get("cursor", cursor); dump(root / "calls.json", calls); return reply

    def submit(identifier, steps, lifetime_ns=20_000_000_000):
        clock_reply = query(["clock"], {"op": "clock"}, 3)
        clock = next(row for row in clock_reply["records"] if row.get("event") == "clock")
        return query(["terminal"], {"op": "submit", "id": identifier,
            "expected_sequence": clock["sequence"], "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
            "steps": steps}, 20)

    def model(stage, prompt, image, instructions, schema):
        result = model_runtime.model_call(root, stage, prompt, image, instructions, schema)
        model_ledger.append({"stage": stage, "usage": result["usage"],
            "runner_ms": result["runner_ms"], "parent_elapsed_ms": result["parent_elapsed_ms"]})
        dump(root / "model-usage-ledger.json", model_ledger); return result

    try:
        endpoint = json.loads(process.stdout.readline()); dump(root / "endpoint.json", endpoint)
        initial_reply = query(["observation"], timeout=30)
        source = next(row for row in initial_reply["records"] if row.get("event") == "observation")
        source_path = root / "runtime" / Path(source["image"]).name
        decision_start_ns = time.perf_counter_ns()

        palette_candidate_model = model("model-palette-candidate",
            "Current subtask: identify the Conveyor control in the visible lower-right Mindustry build palette. World placement is handled later.",
            source_path, "../benchmark_discovery/mindustry_palette_candidate_responder_v2.txt",
            "bounded_visual_target_contract_schema_v2.json")
        with Image.open(source_path) as image: width, height = image.size
        palette_candidate = validate_candidate(palette_candidate_model["typed"], width, height)
        if palette_candidate["status"] == "NEEDS_DECISION":
            raise ValueError("palette candidate returned a coordinate-free bounded stop")
        coarse = palette_candidate["points"][0]
        structure = discover(source_path); palette_binding = bind_palette(coarse, structure["slots"])
        if palette_binding["status"] != "BOUND":
            raise ValueError("coarse palette point lies outside the bounded palette neighbourhood")
        palette_point = palette_binding["point"]
        palette_steps = [{"op": "pointer_move", "x": palette_point[0], "y": palette_point[1]},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200}, {"op": "observe"}]
        palette_hover = submit("hover-palette", palette_steps)
        palette_readiness = verify_palette(palette_hover["records"], palette_steps, palette_point,
            structure["tooltip_box"], root / "runtime", source_path)
        palette_sheet = root / "palette-receipt.png"
        palette_manifest = build_palette_sheet(palette_readiness, root / "runtime", palette_sheet)
        palette_anchor_model = model("model-palette-receipt", plan["task"] +
            " Decide whether this verified palette receipt identifies Conveyor.", palette_sheet,
            "anchor_evidence_responder_v1.txt", "anchor_evidence_contract_schema_v1.json")
        palette_decision = validate_anchor(palette_anchor_model["typed"], palette_readiness)
        if palette_decision["status"] != "EVIDENCE_BOUND":
            raise ValueError("palette evidence unresolved; no click issued")
        pre_select = root / "runtime" / Path(next(row for row in reversed(palette_hover["records"])
            if row.get("event") == "observation")["image"]).name
        if score_selection(pre_select)["success"]: raise ValueError("hover-only palette state scored selected")
        px, py = palette_decision["point"]
        select_steps = [{"op": "pointer_click", "x": px, "y": py, "duration_ms": 40},
            {"op": "pointer_move", "x": 640, "y": 400},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200}, {"op": "observe"}]
        select_reply = submit("select-conveyor", select_steps)
        selected = next(row for row in reversed(select_reply["records"]) if row.get("event") == "observation")
        selected_path = root / "runtime" / Path(selected["image"]).name
        selected_oracle = score_selection(selected_path)
        if not selected_oracle["success"]: raise ValueError("Conveyor selection oracle failed")

        world_candidate_model = model("model-world-candidate",
            "Current subtask: locate the center of the empty world tile directly above the small copper item source. The Conveyor palette selection is already verified.",
            selected_path, "../benchmark_discovery/mindustry_world_candidate_responder_v2.txt",
            "bounded_visual_target_contract_schema_v2.json")
        world_candidate = validate_candidate(world_candidate_model["typed"], width, height)
        if world_candidate["status"] == "NEEDS_DECISION":
            raise ValueError("world candidate returned a coordinate-free bounded stop before probing")
        world_point = world_candidate["points"][0]
        box = [max(0, world_point[0] - 48), max(0, world_point[1] - 54),
               min(width, world_point[0] + 48), min(height, world_point[1] + 56)]
        world_steps = [{"op": "pointer_move", "x": world_point[0], "y": world_point[1]},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200}, {"op": "observe"}]
        world_hover_begin_ns = time.perf_counter_ns(); world_hover = submit("hover-world", world_steps)
        world_hover_return_ns = time.perf_counter_ns()
        world_readiness = verify_world(world_hover["records"], world_steps, world_point, box,
                                       root / "runtime", selected_path)
        world_receipt_ready_ns = time.perf_counter_ns()
        world_sheet = root / "world-receipt.png"; world_manifest = build_world_sheet(world_readiness, root / "runtime", world_sheet)
        world_receipt_model = model("model-world-receipt", plan["task"] +
            " Decide whether this verified world receipt establishes the requested relative tile.", world_sheet,
            "../benchmark_discovery/mindustry_world_target_responder_v1.txt",
            "../benchmark_discovery/mindustry_world_target_contract_schema_v1.json")
        world_decision = validate_world(world_receipt_model["typed"], world_readiness)
        semantic_target_ns = time.perf_counter_ns(); placement_reply = resume_reply = pause_reply = None
        if world_decision["status"] == "EVIDENCE_BOUND":
            wx, wy = world_decision["point"]
            place_steps = [{"op": "pointer_click", "x": wx, "y": wy, "duration_ms": 40},
                {"op": "pointer_move", "x": 900, "y": 400}, {"op": "observe"}]
            placement_reply = submit("place-one-conveyor", place_steps)
            resume_reply = submit("resume-build", [{"op": "hold", "keys": ["space"], "duration_ms": 100},
                {"op": "observe"}])
            build_wait_begin_ns = time.perf_counter_ns(); time.sleep(3); build_wait_end_ns = time.perf_counter_ns()
            pause_reply = submit("pause-review", [{"op": "hold", "keys": ["space"], "duration_ms": 100},
                {"op": "pointer_move", "x": 900, "y": 400}, {"op": "observe"}])
        else:
            build_wait_begin_ns = build_wait_end_ns = None
        finish = query(["independent_evaluation"], {"op": "finish"}, 20)
        code = process.wait(timeout=30); evaluation_ns = time.perf_counter_ns()
        driver_evaluation = next(row for row in finish["records"] if row.get("event") == "independent_evaluation")
        runtime_events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
        button_downs = [row for row in runtime_events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
        usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
        usage_total = {key: sum(row["usage"].get(key, 0) for row in model_ledger) for key in usage_fields}
        result = {"source": source, "palette_candidate_model": palette_candidate_model,
            "palette_candidate": palette_candidate, "palette_structure": structure, "palette_binding": palette_binding,
            "palette_steps": palette_steps, "palette_hover": palette_hover, "palette_readiness": palette_readiness,
            "palette_manifest": palette_manifest, "palette_anchor_model": palette_anchor_model,
            "palette_decision": palette_decision, "selection_oracle": selected_oracle,
            "world_candidate_model": world_candidate_model, "world_candidate": world_candidate,
            "world_point": world_point, "world_steps": world_steps, "world_hover": world_hover,
            "world_readiness": world_readiness, "world_manifest": world_manifest,
            "world_receipt_model": world_receipt_model, "world_decision": world_decision,
            "placement_reply": placement_reply, "resume_reply": resume_reply, "pause_reply": pause_reply,
            "all_button_down_admissions": button_downs, "driver_evaluation": driver_evaluation,
            "bridge_exit_code": code, "socket_exchanges": len(calls), "model_usage_ledger": model_ledger,
            "model_usage_total": usage_total,
            "timing_ms": {"world_hover_submit_to_return": (world_hover_return_ns - world_hover_begin_ns) / 1e6,
                "decision_start_to_world_receipt_ready": (world_receipt_ready_ns - decision_start_ns) / 1e6,
                "decision_start_to_semantic_world_target": (semantic_target_ns - decision_start_ns) / 1e6,
                "fixed_build_wait": None if build_wait_begin_ns is None else (build_wait_end_ns - build_wait_begin_ns) / 1e6,
                "decision_start_to_independent_evaluation": (evaluation_ns - decision_start_ns) / 1e6}}
        positive = world_decision["status"] == "EVIDENCE_BOUND"
        gate = {"palette_evidence_bound": palette_decision["status"] == "EVIDENCE_BOUND",
            "selection_oracle": selected_oracle["success"] is True,
            "world_receipt_ready": world_readiness["status"] == "READY",
            "typed_world_result": world_decision["status"] in ("EVIDENCE_BOUND", "NEEDS_DECISION"),
            "button_policy": (len(button_downs) == 2 and [row["id"] for row in button_downs] == ["select-conveyor", "place-one-conveyor"])
                if positive else (len(button_downs) == 1 and button_downs[0]["id"] == "select-conveyor"),
            "task_completion": driver_evaluation["contract_satisfied"] is True if positive else driver_evaluation["contract_satisfied"] is False,
            "all_calls_accounted": len(model_ledger) == 4 and usage_total["input_tokens"] == sum(row["usage"]["input_tokens"] for row in model_ledger),
            "bridge_exit_zero": code == 0}
        gate["passed"] = all(gate.values())
        report = {"result": result, "promotion_gate": gate,
            "decision": ("RETAIN_SINGLE_TILE_PLACEMENT" if gate["passed"] and positive else
                         "RETAIN_TYPED_SAFE_STOP" if gate["passed"] else "HOLD_SINGLE_TILE_PLACEMENT"),
            "scope": plan["scope"]}
        dump(root / "result.json", result); dump(OUT / "report.json", report); print(json.dumps(report, indent=2))
    except Exception as error:
        dump(OUT / "failure.json", {"error": repr(error), "model_usage_ledger": model_ledger,
            "socket_exchanges": len(calls), "policy": "retained first allocation; no retry"})
        raise
    finally:
        if process.poll() is None: process.terminate(); process.wait(timeout=10)
        stderr.close()


if __name__ == "__main__": main()
