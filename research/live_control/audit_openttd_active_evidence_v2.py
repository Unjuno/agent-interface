"""Audit the retained v1 failure and screen-derived v2 active-evidence pair."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from evidence_target_contract_v1 import validate as validate_evidence
from openttd_finance_oracle_v1 import score as score_finance
from openttd_hover_receipt_batches_v1 import verify_batches
from openttd_toolbar_slots_v1 import discover as discover_slots, local_neighbourhood
from uncertain_target_contract_v1 import validate as validate_uncertain


HERE = Path(__file__).resolve().parent
V1 = HERE / "results/openttd-active-evidence-pair-01"
V2 = HERE / "results/openttd-active-evidence-pair-02"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def records(calls, index):
    return calls[index]["result"]["reply"]["records"]


def replay(root):
    events = [json.loads(line) for line in
              (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    assert len(list((root / "runtime").glob("*.ait"))) == len(observations)
    assert all(row["release"]["verified"] is True
               for row in events if row.get("event") == "terminal")
    assert read(root / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    return len(observations)


def audit_model(root, name, instructions, schema, image=None):
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
    assert plan["instructions_sha256"] == sha(HERE / instructions)
    assert plan["schema_sha256"] == sha(HERE / schema)
    if image is not None:
        assert plan["image_sha256"] == sha(image)
    assert process["exit_code"] == 0
    assert process["observed_model_identity"] is None and process["cost"] is None
    return result


def audit():
    prereg1, prereg2 = read(V1 / "preregistration.json"), read(V2 / "preregistration.json")
    for prereg in (prereg1, prereg2):
        for name, digest in prereg["sources"].items():
            assert sha(source_path(name)) == digest, name
    report1, report2 = read(V1 / "report.json"), read(V2 / "report.json")
    assert report1["decision"] == "HOLD_AND_PRESERVE_ACTIVE_EVIDENCE_PAIR"
    assert report1["promotion_gate"]["passed"] is False
    assert report2["decision"] == "RETAIN_SCREEN_DERIVED_ACTIVE_EVIDENCE_CANDIDATE"
    assert report2["promotion_gate"]["passed"] is True

    frame_counts = {}
    for study, report, root in (("v1", report1, V1), ("v2", report2, V2)):
        for case in report["cases"]:
            case_root = root / f'{case["index"]}-{case["name"]}-seed{case["seed"]}'
            frame_counts[f'{study}-{case["name"]}'] = replay(case_root)
            source_image = case_root / "runtime" / Path(case["source"]["image"]).name
            candidate = audit_model(
                case_root, "model-candidates", "uncertain_target_reference_responder_v1.txt",
                "uncertain_target_contract_schema_v1.json", source_image)
            assert validate_uncertain(candidate["typed"], 1152, 768) == case["candidate_decision"]

    v1_fault, v1_stable = report1["cases"]
    assert v1_fault["hover_readiness"] is None
    assert v1_fault["evidence_model"] is None
    assert v1_fault["target_pointer_admissions"] == []
    assert v1_fault["independent_finance_oracle"]["success"] is False
    v1_root = V1 / "2-stable-seed991004"
    v1_evidence = audit_model(
        v1_root, "model-evidence-selection", "evidence_target_reference_responder_v1.txt",
        "evidence_target_contract_schema_v1.json", v1_root / "hover-presentation.png")
    assert v1_stable["candidate_model"]["typed"]["confidence_basis"] == "visually_unambiguous"
    assert v1_stable["candidate_model"]["typed"]["point"] == {"x": 436, "y": 51}
    assert v1_evidence["typed"]["point"] == {"x": 460, "y": 51}
    assert v1_stable["independent_finance_oracle"]["success"] is False
    assert score_finance(v1_root / "runtime" / Path(
        v1_stable["final_observation"]["image"]).name)["success"] is False

    v2_fault, v2_stable = report2["cases"]
    for case in (v2_fault, v2_stable):
        case_root = V2 / f'{case["index"]}-{case["name"]}-seed{case["seed"]}'
        slots = discover_slots(case_root / "runtime" / Path(case["source"]["image"]).name)
        assert slots == case["toolbar_slots"] and len(slots) == 30
        assert local_neighbourhood(case["anchor"], slots, 2) == case["screen_derived_expansion"]
        assert case["screen_derived_expansion"]["points"] == [
            [389, 51], [412, 51], [435, 51], [458, 51], [485, 51]]
        calls = read(case_root / "calls.json")
        batches = [
            {"records": records(calls, 5), "steps": case["hover_batches"][0]["steps"],
             "points": case["hover_batches"][0]["points"]},
            {"records": records(calls, 7), "steps": case["hover_batches"][1]["steps"],
             "points": case["hover_batches"][1]["points"]},
        ]
        if case["association_fault"]:
            batches[0]["points"] = list(reversed(batches[0]["points"]))
            try:
                verify_batches(batches, case_root / "runtime")
            except ValueError as error:
                assert str(error) == case["hover_readiness_error"]
            else:
                raise AssertionError("v2 association fault was accepted")
        else:
            assert verify_batches(batches, case_root / "runtime") == case["hover_readiness"]

    assert v2_fault["evidence_model"] is None
    assert v2_fault["target_pointer_admissions"] == []
    assert v2_fault["independent_finance_oracle"]["success"] is False
    stable_root = V2 / "2-stable-seed991004"
    stable_model = audit_model(
        stable_root, "model-evidence-selection",
        "evidence_target_reference_responder_v1.txt",
        "evidence_target_contract_schema_v2.json", stable_root / "hover-presentation.png")
    assert validate_evidence(stable_model["typed"], v2_stable["hover_readiness"]) == \
        v2_stable["evidence_binding"]
    assert v2_stable["evidence_binding"]["point"] == [485, 51]
    assert v2_stable["rehover_readiness"]["receipts"][0]["tooltip"] == \
        v2_stable["evidence_binding"]["receipt"]["tooltip"]
    assert v2_stable["click_terminal"]["status"] == "completed"
    assert v2_stable["click_terminal"]["release"]["verified"] is True
    final_path = stable_root / "runtime" / Path(v2_stable["final_observation"]["image"]).name
    assert score_finance(final_path) == v2_stable["independent_finance_oracle"]
    assert v2_stable["independent_finance_oracle"]["success"] is True

    result = {
        "audit_passed": True,
        "preregistered_sources_match": True,
        "retained_v1_failure_reconstructed": True,
        "v2_gate_reconstructed": True,
        "same_single_model": "gpt-5.6-luna low",
        "observed_model_identity": None,
        "reported_cost": None,
        "exact_frames": frame_counts,
        "total_exact_frames": sum(frame_counts.values()),
        "v1": {
            "candidate_self_reported_unambiguous": True,
            "candidate_point": [436, 51], "selected_point": [460, 51],
            "independent_success": False,
            "decision_to_evaluation_ms": v1_stable["timing_ms"][
                "decision_start_to_evaluation_return"]},
        "v2": {
            "detected_toolbar_slots": 30,
            "probed_points": v2_stable["screen_derived_expansion"]["points"],
            "hover_batches": 2, "selected_point": [485, 51],
            "independent_success": True,
            "reported_input_tokens": report2["reported_input_tokens"],
            "hover_batches_ms": v2_stable["timing_ms"]["hover_batches_submit_to_return"],
            "decision_to_evaluation_ms": v2_stable["timing_ms"][
                "decision_start_to_evaluation_return"]},
        "negative_target_pointer_admissions": 0,
        "decision": "RETAIN_SCREEN_DERIVED_ACTIVE_EVIDENCE_CANDIDATE",
        "limits": report2["scope"],
    }
    (V2 / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    return result


def main():
    try:
        result = audit()
    except Exception as error:
        result = {"audit_passed": False, "error_type": type(error).__name__,
                  "error": str(error), "decision": "HOLD_AND_PRESERVE_ACTIVE_EVIDENCE_V2"}
        (V2 / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
