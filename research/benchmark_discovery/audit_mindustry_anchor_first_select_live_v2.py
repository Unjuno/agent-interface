"""Reconstruct the retained Mindustry presentation failure and v2 selection."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from anchor_evidence_contract_v1 import validate as validate_anchor
from audit_local_visual_barrier_v1 import Decoder, Frame
from compact_hover_sheet_v2 import build as build_compact
from uncertain_target_contract_v1 import validate as validate_uncertain

from mindustry_conveyor_selection_oracle_v1 import score as score_selection
from mindustry_palette_hover_receipt_v1 import verify as verify_hover
from mindustry_palette_slots_v1 import discover, nearest


OUT = HERE / "results/mindustry-anchor-first-select-live-02"
ROOT = OUT / "live-fixed-palette"
FAILED = HERE / "results/mindustry-anchor-first-select-live-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
def source_path(name):
    return HERE.parent / name if name.startswith("live_control/") else HERE / name


def audit_model(root, name, instructions, schema, image):
    plan = read(root / name / "plan.json")
    process = read(root / name / "process.json")
    result = read(root / f"{name}-result.json")
    events = [json.loads(line) for line in
              (root / name / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row for row in events if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    assert len(messages) == len(turns) == 1
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert turns[0]["usage"] == result["usage"]
    assert plan["requested_model"] == "gpt-5.6-luna"
    assert plan["requested_effort"] == "low"
    assert plan["instructions_sha256"] == sha(instructions)
    assert plan["schema_sha256"] == sha(schema)
    assert plan["image_sha256"] == sha(image)
    assert process["exit_code"] == 0
    assert process["observed_model_identity"] is None and process["cost"] is None
    return result


def decode_runtime(root):
    events = [json.loads(line) for line in
              (root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / f"{index:03d}.ait").read_bytes())
        with Image.open(root / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    assert len(list(root.glob("*.ait"))) == len(observations)
    return events, observations


def main():
    prereg, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    assert sha(HERE / prereg["reference_image"]) == prereg["reference_sha256"]
    assert sha(HERE / prereg["prior_failure"]) == prereg["prior_failure_sha256"]
    for name, digest in prereg["sources"].items():
        assert sha(source_path(name)) == digest, name

    failure = read(FAILED / "failure.json")
    failed_events = [json.loads(line) for line in
                     (FAILED / "live-fixed-palette/runtime/events.jsonl").read_text(
                         encoding="utf-8").splitlines()]
    assert len(failed_events) == failure["runtime_events"] == 20
    assert not [row for row in failed_events if row.get("event") == "pointer_admission"
                and row.get("operation") == "button_down"]
    assert all(row["release"]["verified"] is True
               for row in failed_events if row.get("event") == "terminal")
    assert read(FAILED / "live-fixed-palette/runtime/cleanup.json")[
        "all_owned_processes_exited"] is True
    failed_candidate = audit_model(
        FAILED / "live-fixed-palette", "model-candidate",
        HERE / "mindustry_palette_target_responder_v1.txt",
        LIVE / "uncertain_target_contract_schema_v1.json",
        FAILED / "live-fixed-palette/runtime/001.png")
    assert failed_candidate["usage"]["input_tokens"] == failure[
        "candidate_model_input_tokens"]

    result = report["result"]
    events, observations = decode_runtime(ROOT / "runtime")
    assert all(row["release"]["verified"] is True
               for row in events if row.get("event") == "terminal")
    assert read(ROOT / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    calls = read(ROOT / "calls.json")
    assert len(calls) == result["socket_exchanges"] == 6
    source = ROOT / "runtime" / Path(result["source"]["image"]).name
    candidate_model = audit_model(
        ROOT, "model-candidate", HERE / "mindustry_palette_target_responder_v1.txt",
        LIVE / "uncertain_target_contract_schema_v1.json", source)
    with Image.open(source) as opened:
        width, height = opened.size
    candidate = validate_uncertain(candidate_model["typed"], width, height)
    assert candidate == result["candidate_decision"]
    structure = discover(source)
    assert structure == result["palette_structure"]
    normalization = nearest(result["coarse_point"], structure["slots"])
    assert normalization == result["normalization"]
    readiness = verify_hover(calls[2]["reply"]["records"], result["anchor_steps"],
                             normalization["point"], structure["tooltip_box"],
                             ROOT / "runtime", source)
    assert readiness == result["anchor_readiness"]
    with tempfile.TemporaryDirectory() as temporary:
        rebuilt = Path(temporary) / "anchor.png"
        manifest = build_compact(readiness, ROOT / "runtime", rebuilt)
        assert pixel_sha(rebuilt) == pixel_sha(ROOT / "anchor-presentation.png")
        assert manifest["pixels_sha256"] == result["anchor_manifest"]["pixels_sha256"]
        assert manifest["rows"][0]["display_scale"] == 1
        assert manifest["rows"][0]["row_height"] == 104
    anchor_model = audit_model(ROOT, "model-anchor-evidence",
                               LIVE / "anchor_evidence_responder_v1.txt",
                               LIVE / "anchor_evidence_contract_schema_v1.json",
                               ROOT / "anchor-presentation.png")
    decision = validate_anchor(anchor_model["typed"], readiness)
    assert decision == result["anchor_decision"]
    assert decision["status"] == "EVIDENCE_BOUND"
    pre_click_image = ROOT / "runtime" / Path(
        next(row for row in reversed(calls[2]["reply"]["records"])
             if row.get("event") == "observation")["image"]).name
    assert score_selection(pre_click_image) == result["pre_click_oracle"]
    assert result["pre_click_oracle"]["success"] is False
    final = ROOT / "runtime" / Path(result["final_observation"]["image"]).name
    assert score_selection(final) == result["selection_oracle"]
    assert result["selection_oracle"]["success"] is True
    button_downs = [row for row in events if row.get("event") == "pointer_admission"
                    and row.get("operation") == "button_down"]
    assert button_downs == result["all_button_down_admissions"]
    assert len(button_downs) == 1 and button_downs[0]["id"] == "select-conveyor"
    assert button_downs[0]["payload"] == 1
    assert result["driver_evaluation"]["collateral_tiles"] == []
    assert result["driver_evaluation"]["initial_to_final_copper_net"] == 0
    assert result["driver_evaluation"]["delivery_layout_unchanged"] is True

    gate = {"one_verified_anchor": len(readiness["receipts"]) == 1,
            "strict_evidence_bound": True,
            "hover_only_not_selected": True,
            "one_final_button_down": True,
            "released_click": next(row for row in calls[4]["reply"]["records"]
                if row.get("event") == "terminal")["release"]["verified"] is True,
            "independent_selection_oracle": True,
            "bridge_exit_zero": result["bridge_exit_code"] == 0}
    gate["passed"] = all(gate.values())
    assert gate == report["promotion_gate"] and gate["passed"] is True
    audit = {"audit_passed": True, "preregistered_sources_match": True,
             "retained_v1_failure_verified": True,
             "exact_frames": len(observations), "all_releases_verified": True,
             "coarse_point": result["coarse_point"],
             "normalized_anchor": normalization["point"],
             "verified_receipts": 1, "button_down_admissions": 1,
             "hover_only_oracle": False, "selection_oracle": True,
             "guard_region_unchanged": True,
             "reported_input_tokens": report["reported_input_tokens"],
             "timing_ms": result["timing_ms"],
             "socket_exchanges": len(calls),
             "same_single_model": "gpt-5.6-luna low", "subagents": 0,
             "observed_model_identity": None, "reported_cost": None,
             "decision": report["decision"], "limits": report["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
