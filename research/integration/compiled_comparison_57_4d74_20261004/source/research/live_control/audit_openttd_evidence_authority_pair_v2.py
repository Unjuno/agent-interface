"""Audit the fresh positive/no-match OpenTTD target-authority pair."""
import hashlib
import json
from pathlib import Path
from PIL import Image

from anchor_evidence_contract_v1 import validate as validate_anchor
from audit_local_visual_barrier_v1 import Decoder, Frame
from evidence_target_contract_v2 import validate as validate_target
from openttd_finance_oracle_v2 import score as score_finance

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-evidence-authority-pair-02"

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("openttd_task/") else HERE / name

def audit_model(root, stage, schema, instructions):
    result, plan, process = read(root / f"{stage}-result.json"), read(root / stage / "plan.json"), read(root / stage / "process.json")
    events = [json.loads(line) for line in (root / stage / "events.jsonl").read_text().splitlines()]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    messages = [row for row in events if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1 and turns[0]["usage"] == result["usage"]
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert process["exit_code"] == 0 and plan["schema_sha256"] == sha(HERE / schema) and plan["instructions_sha256"] == sha(HERE / instructions)
    return result

def audit_case(condition, expected_calls, expected_buttons):
    root = OUT / condition; report = read(root / "report.json"); result = report["result"]
    anchor_model = audit_model(root, "model-anchor-evidence", "anchor_evidence_contract_schema_v1.json", "anchor_evidence_responder_v1.txt")
    selection_model = audit_model(root, "model-expanded-evidence", "evidence_target_contract_schema_v3.json", "evidence_target_reference_responder_v3.txt")
    assert validate_anchor(anchor_model["typed"], result["anchor_readiness"])["status"] == "EXPANSION_REQUIRED"
    selected = validate_target(selection_model["typed"], result["expanded_readiness"]); assert selected == result["selected"]
    events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened: image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    buttons = [row for row in events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
    assert len(buttons) == expected_buttons
    assert all(row["release"]["verified"] is True for row in events if row.get("event") == "terminal")
    assert read(root / "runtime/cleanup.json") == {"all_owned_processes_exited": True, "save_unchanged": True}
    assert len(read(root / "calls.json")) == expected_calls
    if condition == "positive":
        final = root / "runtime" / Path(result["final_observation"]["image"]).name
        assert score_finance(final, result["actual_surface_delta"])["success"] is True
        assert selected["authority_class"] == "TARGET_REFERENCE_ONLY" and selected["point"] == [506, 79]
    else:
        assert selected["authority_class"] == "NO_TARGET_AUTHORITY" and selected["point"] is None
        assert selected["diagnostic_reason"] == "no_match_in_observed_set" and result["click_terminal"] is None
    assert report["promotion_gate"]["passed"] is True
    return {"authority_class": selected["authority_class"], "diagnostic": selected["diagnostic_reason"],
        "point": selected["point"], "button_downs": len(buttons), "durable_calls": expected_calls,
        "exact_frames": len(observations), "reported_input_tokens": report["reported_input_tokens"],
        "timing_ms": result["timing_ms"]}

def main():
    prereg, report = read(OUT / "preregistration.json"), read(OUT / "report.json")
    assert sha(HERE / prereg["prior_failure"]) == prereg["prior_failure_sha256"]
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    for name, digest in prereg["schema_cache"].items(): assert sha(OUT / "schema-cache" / name) == digest, name
    assert report["preflight"]["accepted"] is True and report["preflight"]["model_calls"] == 0
    cases = {"positive": audit_case("positive", 18, 1), "no-match": audit_case("no-match", 12, 0)}
    assert report["passed"] is True
    audit = {"passed": True, "decision": "RETAIN_EVIDENCE_TARGET_AUTHORITY_PAIR_V2",
        "preflight_model_calls": 0, "cases": cases,
        "same_model": "gpt-5.6-luna low", "subagents": 0,
        "scope": prereg["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__": main()
