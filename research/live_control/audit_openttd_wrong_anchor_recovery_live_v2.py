"""Independently reconstruct the wrong-anchor OpenTTD recovery allocation."""
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image

from anchor_evidence_contract_v1 import validate as validate_anchor
from audit_local_visual_barrier_v1 import Decoder, Frame
from evidence_target_contract_v1 import validate as validate_evidence
from openttd_compact_hover_sheet_v1 import build as build_compact
from openttd_finance_oracle_v2 import score as score_finance
from openttd_hover_receipt_batches_v1 import verify_batches
from openttd_toolbar_slots_v1 import local_neighbourhood
from openttd_toolbar_slots_v2 import discover


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-wrong-anchor-recovery-live-02"
ROOT = OUT / "fault-seed991004"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixel_sha(path):
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def audit_model(name, instructions, schema, image):
    plan = read(ROOT / name / "plan.json")
    process = read(ROOT / name / "process.json")
    result = read(ROOT / f"{name}-result.json")
    events = [json.loads(line) for line in
              (ROOT / name / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row for row in events if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    assert len(messages) == len(turns) == 1
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert turns[0]["usage"] == result["usage"]
    assert plan["requested_model"] == "gpt-5.6-luna"
    assert plan["requested_effort"] == "low"
    assert plan["instructions_sha256"] == sha(HERE / instructions)
    assert plan["schema_sha256"] == sha(HERE / schema)
    assert plan["image_sha256"] == sha(image)
    assert process["exit_code"] == 0
    assert process["observed_model_identity"] is None and process["cost"] is None
    return result


def main():
    prereg = read(OUT / "preregistration.json")
    report = read(OUT / "report.json")
    result = report["result"]
    assert sha(HERE / prereg["baseline_report"]) == prereg["baseline_sha256"]
    fault_source = HERE / prereg["fault_injection"]["source"]
    assert sha(fault_source) == prereg["fault_injection"]["source_sha256"]
    archived = read(fault_source)["typed"]
    assert archived["op"] == "expand_search"
    assert [archived["point"]["x"], archived["point"]["y"]] == [436, 51]
    for name, digest in prereg["sources"].items():
        assert sha(source_path(name)) == digest, name

    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
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
    structure = discover(source)
    assert structure == result["toolbar_structure"]
    delta = result["actual_surface_delta"]
    injected = [archived["point"]["x"] + delta[0], archived["point"]["y"] + delta[1]]
    assert injected == result["fault_injection"]["translated_probe_point"] == result["anchor"]
    expansion = local_neighbourhood(injected, structure["slots"], 2)
    assert expansion == result["screen_derived_expansion"]
    assert result["anchor_point"] == structure["slots"][expansion["anchor_slot_index"]]["point"]

    calls = read(ROOT / "calls.json")
    anchor_batch = {"records": calls[7]["result"]["reply"]["records"],
                    "steps": result["anchor_steps"], "points": [result["anchor_point"]]}
    anchor_readiness = verify_batches([anchor_batch], ROOT / "runtime")
    assert anchor_readiness == result["anchor_readiness"]
    expansion_batches = []
    for call_index, recorded in zip([9, 11], result["expansion_batches"]):
        expansion_batches.append({"records": calls[call_index]["result"]["reply"]["records"],
                                  "steps": recorded["steps"], "points": recorded["points"]})
    expanded = verify_batches([anchor_batch] + expansion_batches, ROOT / "runtime")
    assert expanded == result["expanded_readiness"]
    assert len(expanded["receipts"]) == 5

    with tempfile.TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        anchor_image = temporary / "anchor.png"
        expanded_image = temporary / "expanded.png"
        anchor_manifest = build_compact(anchor_readiness, ROOT / "runtime", anchor_image)
        build_compact(expanded, ROOT / "runtime", expanded_image)
        assert pixel_sha(anchor_image) == pixel_sha(ROOT / "anchor-presentation.png")
        assert pixel_sha(expanded_image) == pixel_sha(ROOT / "expanded-presentation.png")
        assert anchor_manifest["pixels_sha256"] == result["anchor_manifest"]["pixels_sha256"]

    anchor_model = audit_model("model-anchor-evidence", "anchor_evidence_responder_v1.txt",
                               "anchor_evidence_contract_schema_v1.json",
                               ROOT / "anchor-presentation.png")
    anchor_decision = validate_anchor(anchor_model["typed"], anchor_readiness)
    assert anchor_decision == result["anchor_decision"]
    assert anchor_decision["status"] == "EXPANSION_REQUIRED"
    selection_model = audit_model("model-expanded-evidence",
                                  "evidence_target_reference_responder_v2.txt",
                                  "evidence_target_contract_schema_v2.json",
                                  ROOT / "expanded-presentation.png")
    selected = validate_evidence(selection_model["typed"], expanded)
    assert selected == result["selected"]
    assert selected["point"] != result["anchor_point"]

    x, y = selected["point"]
    rehover_steps = [{"op": "pointer_move", "x": x, "y": y},
                     {"op": "dwell_observe", "delay_ms": 800}, {"op": "observe"}]
    rehover = verify_batches([{"records": calls[13]["result"]["reply"]["records"],
                               "steps": rehover_steps, "points": [[x, y]]}],
                             ROOT / "runtime")
    assert rehover == result["rehover_readiness"]
    assert rehover["receipts"][0]["tooltip"] == selected["receipt"]["tooltip"]
    final = ROOT / "runtime" / Path(result["final_observation"]["image"]).name
    assert score_finance(final, delta) == result["independent_finance_oracle"]
    assert result["independent_finance_oracle"]["success"] is True

    button_downs = [row for row in events if row.get("event") == "pointer_admission"
                    and row.get("operation") == "button_down"]
    assert button_downs == result["all_button_down_admissions"]
    assert len(button_downs) == 1
    assert button_downs[0]["id"] == result["click_terminal"]["id"] == \
        calls[17]["result"]["reply"]["records"][-1]["id"]
    comparison = {"initial_receipts_before_decision": 1,
                  "additional_receipts_after_expansion": 4,
                  "total_verified_receipts": 5, "durable_calls": len(calls)}
    assert comparison == report["comparison"]
    gate = {"expanded_branch": result["branch"] == "expanded",
            "one_initial_hover_receipt": len(anchor_readiness["receipts"]) == 1,
            "strict_expansion_required": True,
            "five_verified_receipts_after_expansion": len(expanded["receipts"]) == 5,
            "selected_different_from_wrong_anchor": selected["point"] != result["anchor_point"],
            "exact_rehover": True,
            "released_click": result["click_terminal"]["release"]["verified"] is True,
            "independent_translated_oracle": True,
            "only_one_button_down_after_selection": True}
    gate["passed"] = all(gate.values())
    assert gate == report["promotion_gate"] and gate["passed"] is True
    audit = {"audit_passed": True, "preregistered_sources_match": True,
             "exact_frames": len(observations), "all_releases_verified": True,
             "fault_kind": "deterministic archived wrong-anchor injection",
             "branch": result["branch"], "wrong_anchor": result["anchor_point"],
             "selected_point": selected["point"], "button_down_admissions": 1,
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
