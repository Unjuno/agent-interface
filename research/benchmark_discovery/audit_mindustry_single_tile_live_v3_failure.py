"""Audit the retained world-receipt-schema failure after verified probing."""
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
from mindustry_conveyor_selection_oracle_v1 import score as score_selection
from mindustry_palette_binding_v2 import bind
from mindustry_palette_hover_receipt_v1 import verify as verify_palette
from mindustry_palette_slots_v1 import discover
from mindustry_world_hover_receipt_v1 import verify as verify_world
from compact_world_receipt_v1 import build as build_world

OUT = HERE / "results/mindustry-single-tile-live-03"; ROOT = OUT / "live-changed-geometry"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image: return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("live_control/") else HERE / name


def audit_model(name):
    result = read(ROOT / f"{name}-result.json")
    raw = [json.loads(line) for line in (ROOT / name / "events.jsonl").read_text().splitlines()]
    turns = [row for row in raw if row.get("type") == "turn.completed"]
    messages = [row for row in raw if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1 and turns[0]["usage"] == result["usage"]
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    return result


def main():
    prereg = read(OUT / "preregistration.json"); failure = read(OUT / "failure.json")
    assert sha(HERE / prereg["reference_image"]) == prereg["reference_sha256"]
    assert sha(HERE / prereg["prior_failure"]) == prereg["prior_failure_sha256"]
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    calls = read(ROOT / "calls.json"); runtime = ROOT / "runtime"
    initial = next(row for row in calls[0]["reply"]["records"] if row.get("event") == "observation")
    initial_path = runtime / Path(initial["image"]).name
    palette_candidate = audit_model("model-palette-candidate")
    candidate = validate_candidate(palette_candidate["typed"], 1280, 800)
    structure = discover(initial_path); binding = bind(candidate["points"][0], structure["slots"]); assert binding["status"] == "BOUND"
    palette_call = calls[2]["reply"]; palette_steps = calls[2]["request"]["command"]["steps"]
    palette_ready = verify_palette(palette_call["records"], palette_steps, binding["point"], structure["tooltip_box"], runtime, initial_path)
    with tempfile.TemporaryDirectory() as temporary:
        palette_sheet = Path(temporary) / "palette.png"; build_palette(palette_ready, runtime, palette_sheet)
        assert pixel_sha(palette_sheet) == pixel_sha(ROOT / "palette-receipt.png")
    palette_receipt = audit_model("model-palette-receipt"); decision = validate_anchor(palette_receipt["typed"], palette_ready)
    assert decision["status"] == "EVIDENCE_BOUND"
    selected_call = calls[4]["reply"]; selected = next(row for row in reversed(selected_call["records"]) if row.get("event") == "observation")
    selected_path = runtime / Path(selected["image"]).name; assert score_selection(selected_path)["success"] is True
    world_candidate = audit_model("model-world-candidate"); world = validate_candidate(world_candidate["typed"], 1280, 800)
    assert world["points"] == [[368, 392]]
    point = world["points"][0]; box = [point[0]-48, point[1]-54, point[0]+48, point[1]+56]
    world_call = calls[6]["reply"]; world_steps = calls[6]["request"]["command"]["steps"]
    world_ready = verify_world(world_call["records"], world_steps, point, box, runtime, selected_path)
    with tempfile.TemporaryDirectory() as temporary:
        world_sheet = Path(temporary) / "world.png"; build_world(world_ready, runtime, world_sheet)
        assert pixel_sha(world_sheet) == pixel_sha(ROOT / "world-receipt.png")
    failed_raw = [json.loads(line) for line in (ROOT / "model-world-receipt/events.jsonl").read_text().splitlines()]
    assert any("'oneOf' is not permitted" in json.dumps(row) for row in failed_raw)
    assert not [row for row in failed_raw if row.get("type") == "turn.completed"]
    ledger = read(ROOT / "model-usage-ledger.json"); assert ledger == failure["model_usage_ledger"] and len(ledger) == 3
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
    decoder = Decoder("live-control"); observations = [row for row in events if row.get("event") == "observation"]
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((runtime / f"{index:03d}.ait").read_bytes())
        with Image.open(runtime / Path(observation["image"]).name) as opened: image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    buttons = [row for row in events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
    assert len(buttons) == 1 and buttons[0]["id"] == "select-conveyor"
    assert all(row["release"]["verified"] is True for row in events if row.get("event") == "terminal")
    cleanup = read(runtime / "cleanup.json"); assert cleanup["all_owned_processes_exited"] and cleanup["save_unchanged"]
    audit = {"passed": True, "decision": "RETAIN_VERIFIED_WORLD_PROBE_UNSUPPORTED_RECEIPT_SCHEMA",
        "completed_model_calls": 3, "input_tokens": sum(row["usage"]["input_tokens"] for row in ledger),
        "world_point": point, "world_receipt_frames": len(world_ready["receipts"][0]["dwell_sequences"]),
        "button_down_ids": [row["id"] for row in buttons], "placement_button_down": 0,
        "exact_frames": len(observations), "cleanup": cleanup}
    (OUT / "failure-audit.json").write_text(json.dumps(audit, indent=2) + "\n"); print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
