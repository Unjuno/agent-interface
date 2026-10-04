"""Reconstruct the anchor-first translated OpenTTD live allocation."""
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image

from anchor_evidence_contract_v1 import validate as validate_anchor
from audit_local_visual_barrier_v1 import Decoder, Frame
from openttd_compact_hover_sheet_v1 import build as build_compact
from openttd_finance_oracle_v2 import score as score_finance
from openttd_hover_receipt_batches_v1 import verify_batches
from openttd_toolbar_slots_v1 import local_neighbourhood
from openttd_toolbar_slots_v2 import discover
from uncertain_target_contract_v1 import validate as validate_uncertain


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-anchor-first-live-01"
ROOT = OUT / "live-seed991004"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image: return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
def source_path(name): return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def audit_model(name, instructions, schema, image):
    plan = read(ROOT / name / "plan.json"); process = read(ROOT / name / "process.json")
    result = read(ROOT / f"{name}-result.json")
    events = [json.loads(line) for line in (ROOT / name / "events.jsonl").read_text(
        encoding="utf-8").splitlines()]
    messages = [row for row in events if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    assert len(messages) == len(turns) == 1
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert turns[0]["usage"] == result["usage"]
    assert plan["requested_model"] == "gpt-5.6-luna" and plan["requested_effort"] == "low"
    assert plan["instructions_sha256"] == sha(HERE / instructions)
    assert plan["schema_sha256"] == sha(HERE / schema)
    assert plan["image_sha256"] == sha(image)
    assert process["exit_code"] == 0
    assert process["observed_model_identity"] is None and process["cost"] is None
    return result


def main():
    prereg, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    assert sha(HERE / prereg["baseline_report"]) == prereg["baseline_sha256"]
    for name, digest in prereg["sources"].items(): assert sha(source_path(name)) == digest, name
    result = report["result"]
    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text(
        encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((ROOT / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(ROOT / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    assert len(list((ROOT / "runtime").glob("*.ait"))) == len(observations)
    assert all(row["release"]["verified"] is True
               for row in events if row.get("event") == "terminal")
    assert read(ROOT / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}

    source = ROOT / "runtime" / Path(result["source"]["image"]).name
    candidate = audit_model("model-candidates", "uncertain_target_reference_responder_v1.txt",
                            "uncertain_target_contract_schema_v1.json", source)
    assert validate_uncertain(candidate["typed"], 1152, 768) == result["candidate_decision"]
    structure = discover(source); assert structure == result["toolbar_structure"]
    assert local_neighbourhood(result["anchor"], structure["slots"], 2) == \
        result["screen_derived_expansion"]
    assert result["anchor_point"] == structure["slots"][
        result["screen_derived_expansion"]["anchor_slot_index"]]["point"]
    calls = read(ROOT / "calls.json")
    anchor_readiness = verify_batches([{
        "records": calls[7]["result"]["reply"]["records"],
        "steps": result["anchor_steps"], "points": [result["anchor_point"]]}], ROOT / "runtime")
    assert anchor_readiness == result["anchor_readiness"]
    with tempfile.TemporaryDirectory() as temporary:
        rebuilt = Path(temporary) / "anchor.png"
        manifest = build_compact(anchor_readiness, ROOT / "runtime", rebuilt)
        assert pixel_sha(rebuilt) == pixel_sha(ROOT / "anchor-presentation.png")
        assert manifest["pixels_sha256"] == result["anchor_manifest"]["pixels_sha256"]
    anchor_model = audit_model("model-anchor-evidence", "anchor_evidence_responder_v1.txt",
                               "anchor_evidence_contract_schema_v1.json",
                               ROOT / "anchor-presentation.png")
    decision = validate_anchor(anchor_model["typed"], anchor_readiness)
    assert decision == result["anchor_decision"] == result["selected"]
    assert decision["status"] == "EVIDENCE_BOUND"
    assert result["branch"] == "anchor-accepted" and result["expansion_batches"] == []
    assert result["expanded_readiness"] is None and result["selection_model"] is None
    x, y = decision["point"]
    rehover_steps = [{"op": "pointer_move", "x": x, "y": y},
                     {"op": "dwell_observe", "delay_ms": 800}, {"op": "observe"}]
    rehover = verify_batches([{
        "records": calls[9]["result"]["reply"]["records"],
        "steps": rehover_steps, "points": [[x, y]]}], ROOT / "runtime")
    assert rehover == result["rehover_readiness"]
    assert rehover["receipts"][0]["tooltip"] == decision["receipt"]["tooltip"]
    final = ROOT / "runtime" / Path(result["final_observation"]["image"]).name
    assert score_finance(final, result["actual_surface_delta"]) == result["independent_finance_oracle"]
    assert result["independent_finance_oracle"]["success"] is True

    baseline = read(HERE / prereg["baseline_report"])["result"]
    comparison = {"prior_five_hover_ms": baseline["timing_ms"]["hover_batches"],
                  "anchor_hover_ms": result["timing_ms"]["anchor_hover_submit_to_return"],
                  "hover_stage_reduction_ms": baseline["timing_ms"]["hover_batches"] -
                      result["timing_ms"]["anchor_hover_submit_to_return"],
                  "prior_durable_calls": baseline["durable_calls"],
                  "anchor_first_durable_calls": result["durable_calls"],
                  "prior_exact_frames": 50}
    assert comparison == report["comparison"]
    gate = {"anchor_only_branch": True, "one_initial_hover_receipt": True,
            "strict_anchor_evidence_bound": True, "exact_rehover": True,
            "released_click": result["click_terminal"]["release"]["verified"] is True,
            "independent_translated_oracle": True,
            "deterministic_hover_stage_lower": comparison["hover_stage_reduction_ms"] > 0,
            "durable_calls_lower": result["durable_calls"] < baseline["durable_calls"]}
    gate["passed"] = all(gate.values())
    assert gate == report["promotion_gate"] and gate["passed"] is True
    audit = {"audit_passed": True, "preregistered_sources_match": True,
             "exact_frames": len(observations), "all_releases_verified": True,
             "branch": result["branch"], "anchor_point": result["anchor_point"],
             "independent_finance_oracle": True,
             "reported_input_tokens": report["reported_input_tokens"],
             "comparison": comparison, "timing_ms": result["timing_ms"],
             "same_single_model": "gpt-5.6-luna low", "subagents": 0,
             "observed_model_identity": None, "reported_cost": None,
             "decision": report["decision"], "limits": report["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
