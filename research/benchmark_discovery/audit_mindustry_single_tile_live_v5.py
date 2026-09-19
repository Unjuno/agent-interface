"""Independently reconstruct the retained v5 changed-geometry placement."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent; LIVE = HERE.parent / "live_control"; sys.path.insert(0, str(LIVE))
from anchor_evidence_contract_v1 import validate as validate_anchor
from audit_local_visual_barrier_v1 import Decoder, Frame
from bounded_visual_target_contract_v3 import validate as validate_candidate
from compact_hover_sheet_v2 import build as build_palette
from compact_world_receipt_v1 import build as build_world
from mindustry_conveyor_selection_oracle_v1 import score as score_selection
from mindustry_palette_binding_v2 import bind
from mindustry_palette_hover_receipt_v1 import verify as verify_palette
from mindustry_palette_slots_v1 import discover
from mindustry_single_tile_score_v1 import score
from mindustry_world_hover_receipt_v1 import verify as verify_world
from mindustry_world_target_contract_v3 import validate as validate_world

OUT = HERE / "results/mindustry-single-tile-live-05"; ROOT = OUT / "live-changed-geometry"; RUNTIME = ROOT / "runtime"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image: return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("live_control/") else HERE / name


def audit_model(name):
    result = read(ROOT / f"{name}-result.json"); plan = read(ROOT / name / "plan.json"); process = read(ROOT / name / "process.json")
    raw = [json.loads(line) for line in (ROOT / name / "events.jsonl").read_text().splitlines()]
    turns = [row for row in raw if row.get("type") == "turn.completed"]
    messages = [row for row in raw if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1 and turns[0]["usage"] == result["usage"]
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert process["exit_code"] == 0 and plan["requested_model"] == "gpt-5.6-luna" and plan["requested_effort"] == "low"
    bindings = {
        "model-palette-candidate": (HERE / "mindustry_palette_candidate_responder_v3.txt", LIVE / "bounded_visual_target_contract_schema_v3.json"),
        "model-palette-receipt": (LIVE / "anchor_evidence_responder_v1.txt", LIVE / "anchor_evidence_contract_schema_v1.json"),
        "model-world-candidate": (HERE / "mindustry_world_candidate_responder_v3.txt", LIVE / "bounded_visual_target_contract_schema_v3.json"),
        "model-world-receipt": (HERE / "mindustry_world_target_responder_v3.txt", HERE / "mindustry_world_target_contract_schema_v3.json")}
    instructions, schema = bindings[name]
    assert plan["instructions_sha256"] == sha(instructions) and plan["schema_sha256"] == sha(schema)
    prompt = (ROOT / f"{name}-prompt.txt").read_bytes(); assert plan["prompt_sha256"] == hashlib.sha256(prompt).hexdigest()
    return result


def main():
    prereg = read(OUT / "preregistration.json"); report = read(OUT / "report.json"); result = report["result"]
    assert sha(HERE / prereg["reference_image"]) == prereg["reference_sha256"]
    assert sha(HERE / prereg["prior_failure"]) == prereg["prior_failure_sha256"]
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    calls = read(ROOT / "calls.json"); assert len(calls) == result["socket_exchanges"] == 14
    initial = next(row for row in calls[0]["reply"]["records"] if row.get("event") == "observation")
    initial_path = RUNTIME / Path(initial["image"]).name
    models = {name: audit_model(name) for name in ("model-palette-candidate", "model-palette-receipt", "model-world-candidate", "model-world-receipt")}
    assert read(ROOT / "model-palette-candidate/plan.json")["image_sha256"] == sha(initial_path)
    palette_candidate = validate_candidate(models["model-palette-candidate"]["typed"], 1280, 800)
    structure = discover(initial_path); binding = bind(palette_candidate["points"][0], structure["slots"])
    assert binding == result["palette_binding"] and binding["status"] == "BOUND"
    palette_call = calls[2]; palette_steps = palette_call["request"]["command"]["steps"]
    palette_ready = verify_palette(palette_call["reply"]["records"], palette_steps, binding["point"], structure["tooltip_box"], RUNTIME, initial_path)
    with tempfile.TemporaryDirectory() as temporary:
        rebuilt = Path(temporary) / "palette.png"; build_palette(palette_ready, RUNTIME, rebuilt)
        assert pixel_sha(rebuilt) == pixel_sha(ROOT / "palette-receipt.png")
    assert validate_anchor(models["model-palette-receipt"]["typed"], palette_ready)["status"] == "EVIDENCE_BOUND"
    selected_call = calls[4]["reply"]; selected = next(row for row in reversed(selected_call["records"]) if row.get("event") == "observation")
    selected_path = RUNTIME / Path(selected["image"]).name; assert score_selection(selected_path)["success"] is True
    assert read(ROOT / "model-palette-receipt/plan.json")["image_sha256"] == sha(ROOT / "palette-receipt.png")
    assert read(ROOT / "model-world-candidate/plan.json")["image_sha256"] == sha(selected_path)
    assert read(ROOT / "model-world-receipt/plan.json")["image_sha256"] == sha(ROOT / "world-receipt.png")
    world_candidate = validate_candidate(models["model-world-candidate"]["typed"], 1280, 800)
    assert world_candidate["points"] == [result["world_point"]]
    point = result["world_point"]; box = [max(0, point[0]-48), max(0, point[1]-54), min(1280, point[0]+48), min(800, point[1]+56)]
    world_call = calls[6]; world_steps = world_call["request"]["command"]["steps"]
    world_ready = verify_world(world_call["reply"]["records"], world_steps, point, box, RUNTIME, selected_path)
    with tempfile.TemporaryDirectory() as temporary:
        rebuilt = Path(temporary) / "world.png"; build_world(world_ready, RUNTIME, rebuilt)
        assert pixel_sha(rebuilt) == pixel_sha(ROOT / "world-receipt.png")
    world_decision = validate_world(models["model-world-receipt"]["typed"], world_ready)
    assert world_decision == result["world_decision"] and world_decision["status"] == "EVIDENCE_BOUND"
    events = [json.loads(line) for line in (RUNTIME / "events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]; decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((RUNTIME / f"{index:03d}.ait").read_bytes())
        with Image.open(RUNTIME / Path(observation["image"]).name) as opened: image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    buttons = [row for row in events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
    assert [row["id"] for row in buttons] == ["select-conveyor", "place-one-conveyor"]
    assert all(row["release"]["verified"] is True for row in events if row.get("event") == "terminal")
    terminals = [row for row in events if row.get("event") == "terminal"]
    assert all(row["status"] == "completed" for row in terminals)
    before, after, plan = read(RUNTIME / "before.json"), read(RUNTIME / "after.json"), read(HERE / "mindustry_single_tile_plan_v1.json")
    evaluation = score(before, after, plan); assert evaluation == read(RUNTIME / "evaluation.json")
    assert evaluation["contract_satisfied"] is True and evaluation == {k: v for k, v in result["driver_evaluation"].items() if k not in ("event", "emitted_ns")}
    controls = {}
    wrong = copy.deepcopy(after); next(row for row in wrong["tiles"] if [row["x"], row["y"]] == plan["target"])["rotation"] = 0
    controls["wrong_rotation"] = score(before, wrong, plan)["status"]
    collateral = copy.deepcopy(after); next(row for row in collateral["tiles"] if (row["x"], row["y"]) == (138,52)).update(block="conveyor", team=1, rotation=1)
    controls["collateral"] = score(before, collateral, plan)["status"]
    wrong_cost = copy.deepcopy(after); wrong_cost["copper"] = before["copper"]
    controls["wrong_cost"] = score(before, wrong_cost, plan)["status"]
    pending = copy.deepcopy(after); pending["unit"]["plans"] = 1
    controls["pending_plan"] = score(before, pending, plan)["status"]
    malformed = copy.deepcopy(plan); malformed["target"] = [137]
    controls["malformed_target"] = score(before, after, malformed)["status"]
    assert controls == {"wrong_rotation": "CONTRADICTED", "collateral": "CONTRADICTED", "wrong_cost": "CONTRADICTED", "pending_plan": "CONTRADICTED", "malformed_target": "UNKNOWN"}
    ledger = result["model_usage_ledger"]; assert ledger == read(ROOT / "model-usage-ledger.json") and len(ledger) == 4
    fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
    totals = {key: sum(row["usage"].get(key, 0) for row in ledger) for key in fields}; assert totals == result["model_usage_total"]
    assert report["promotion_gate"]["passed"] is True and report["decision"] == "RETAIN_SINGLE_TILE_PLACEMENT"
    cleanup = read(RUNTIME / "cleanup.json"); assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
    audit = {"passed": True, "decision": report["decision"], "model_calls": 4, "model_usage_total": totals,
        "world_point": point, "world_receipt_frames": len(world_ready["receipts"][0]["dwell_sequences"]),
        "button_down_ids": [row["id"] for row in buttons], "exact_frames": len(observations),
        "terminal_count": len(terminals), "independent_evaluation": evaluation, "controls": controls,
        "timing_ms": result["timing_ms"], "cleanup": cleanup}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n"); print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
