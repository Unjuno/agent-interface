"""Audit and reconstruct the retained first hover-target pair."""
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageChops

from audit_local_visual_barrier_v1 import Decoder, Frame
from hover_target_contract_v1 import runtime_reference
from model_point_target_v1 import patch
from openttd_hover_evidence_v1 import CANDIDATES, ORDER, verify


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-hover-target-pair-01"
FAULT = ROOT / "1-association-fault-seed991004"
STABLE = ROOT / "2-stable-seed991004"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def replay(root):
    events = [json.loads(line) for line in
              (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    images = {}
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        images[observation["sequence"]] = image
    assert len(list((root / "runtime").glob("*.ait"))) == len(observations)
    return events, images


def records(call):
    return call["result"].get("reply", {}).get("records", [])


def first(rows, event):
    return next(row for row in rows if row.get("event") == event)


def hover_steps():
    steps = []
    for name in ORDER:
        x, y = CANDIDATES[name]["point"]
        steps.extend([{"op": "pointer_move", "x": x, "y": y},
                      {"op": "dwell_observe", "delay_ms": 800},
                      {"op": "observe"}])
    return steps


def observer_score(root):
    score_path = HERE.parent / "openttd_task/guarded_l_score_v1.py"
    spec = importlib.util.spec_from_file_location("hover_audit_guarded_score", score_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for line in (root / "runtime/game-stderr.txt").read_text(
            encoding="utf-8", errors="replace").splitlines():
        if "AIT {" in line:
            rows.append(json.loads(line.split("AIT ", 1)[1]))
    assert rows
    return len(rows), module.score(rows[-1], rows[0])


def audit():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    assert plan["failure_policy"].startswith("retain both first sessions")
    assert not (ROOT / "report.json").exists()

    fault = read(FAULT / "result.json")
    assert fault["hover_readiness"]["status"] == "READY"
    assert fault["association_refusal"] == \
        "hover program does not match declared candidate order"
    assert fault["model"] is None and fault["program_pointer_admissions"] == []
    assert fault["independent_evaluation"]["success"] is False
    assert fault["durable_calls"] == 6

    fault_events, _ = replay(FAULT)
    stable_events, stable_images = replay(STABLE)
    for events in (fault_events, stable_events):
        assert all(row["release"]["verified"] is True
                   for row in events if row.get("event") == "terminal")
    for root in (FAULT, STABLE):
        assert read(root / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}

    calls = read(STABLE / "calls.json")
    assert len(calls) == 14
    hover_records = records(calls[5])
    readiness = verify(hover_records, hover_steps(), STABLE / "runtime")
    assert readiness["status"] == "READY"
    assert [row["candidate_id"] for row in readiness["evidence"]] == ORDER
    assert [(row["operation"], row["payload"])
            for row in hover_records if row.get("event") == "pointer_admission"] == [
        ("move", {"x": 432, "y": 51}),
        ("move", {"x": 650, "y": 51}),
        ("move", {"x": 820, "y": 51})]
    assert first(hover_records, "terminal")["status"] == "completed"

    model = read(STABLE / "model-result.json")
    assert model["strict_contract_correct"] is True
    assert model["contract_error"] is None
    assert runtime_reference(model["typed"]) == model["runtime_reference"]
    assert model["runtime_reference"] == {
        "candidate_id": "roads", "point": [820, 51],
        "coordinate_frame": "window_content",
        "point_space": "source_observation_pixels",
        "motion_model": "surface_origin_translation"}
    assert model["usage"]["input_tokens"] == 9932
    model_plan = read(STABLE / "model-hover-contract/plan.json")
    process = read(STABLE / "model-hover-contract/process.json")
    assert model_plan["requested_model"] == "gpt-5.6-luna"
    assert model_plan["requested_effort"] == "low"
    assert model_plan["image_sha256"] == sha(STABLE / "hover-presentation.png")
    assert model_plan["instructions_sha256"] == sha(
        HERE / "hover_target_reference_responder_v1.txt")
    assert model_plan["schema_sha256"] == sha(
        HERE / "hover_target_contract_schema_v1.json")
    assert process["exit_code"] == 0
    assert process["observed_model_identity"] is None and process["cost"] is None
    with Image.open(STABLE / "hover-presentation.png") as presentation:
        assert presentation.size == (1280, 1175)

    mint_records = records(calls[7])
    minted = first(mint_records, "target_handle_minted_from_point")
    assert minted["source_sequence"] == 23 and minted["fresh_sequence"] == 24
    assert minted["derived_box"] == [808, 44, 24, 14]
    assert minted["fresh_patch_exact"] is True
    hovered_digest = hashlib.sha256(
        patch(stable_images[23], [808, 44, 24, 14])).hexdigest()
    fresh_digest = hashlib.sha256(
        patch(stable_images[24], [808, 44, 24, 14])).hexdigest()
    assert hovered_digest == fresh_digest == minted["patch_sha256"]

    moved = first(records(calls[9]), "test_surface_moved")
    delta = [moved["after"]["geometry"][0] - moved["before"]["geometry"][0],
             moved["after"]["geometry"][1] - moved["before"]["geometry"][1]]
    assert delta == [21, 28]
    checked = first(records(calls[11]), "target_handle_checked")
    assert checked["status"] == "MISSING"
    assert checked["reason"] == "region_pixels_missing"
    assert checked["predicted_box"] == [829, 72, 24, 14]

    pre_hover = patch(stable_images[14], [808, 44, 24, 14])
    moved_unhovered = patch(stable_images[25], [829, 72, 24, 14])
    hovered = patch(stable_images[23], [808, 44, 24, 14])
    assert pre_hover == moved_unhovered
    assert hovered != moved_unhovered
    with Image.frombytes("RGB", (24, 14), hovered) as hover_image, \
            Image.frombytes("RGB", (24, 14), moved_unhovered) as plain_image:
        difference = ImageChops.difference(hover_image, plain_image)
        hover_changed_pixels = sum(pixel != (0, 0, 0)
                                   for pixel in difference.getdata())
        hover_change_box = list(difference.getbbox())
    assert hover_changed_pixels == 35 and hover_change_box == [12, 7, 20, 14]

    program_records = records(calls[13])
    revalidated = first(program_records, "target_handle_revalidated")
    terminal = first(program_records, "terminal")
    assert revalidated["status"] == "MISSING"
    assert revalidated["reason"] == "region_pixels_missing"
    assert [row for row in program_records
            if row.get("event") == "pointer_admission"] == []
    assert terminal["status"] == "needs_decision"
    assert terminal["steps_completed"] == 0
    assert terminal["release"]["verified"] is True
    assert not (STABLE / "runtime/evaluation.json").exists()
    observer_records, posthoc_score = observer_score(STABLE)
    assert posthoc_score["success"] is False
    assert posthoc_score["checks"] == {
        "target_owned_roads": False,
        "ordered_bidirectional_connections": False,
        "forbidden_tiles_clear": True,
        "surrounding_road_owner_unchanged": True}

    safe_stop_ms = (calls[13]["end_ns"] - calls[5]["begin_ns"]) / 1e6
    hover_ms = (calls[5]["end_ns"] - calls[5]["begin_ns"]) / 1e6
    result = {
        "audit_passed": True,
        "preregistered_sources_match": True,
        "primary_report_created": False,
        "failure_class": "interaction_conditioned_target_patch",
        "association_fault": {
            "hover_readiness": "READY", "refused_before_model": True,
            "target_pointer_admissions": 0, "independent_success": False,
            "formal_independent_evaluation": True,
            "durable_calls": 6,
            "decision_to_evaluation_ms": fault["timing_ms"][
                "decision_start_to_evaluation_return"]},
        "stable": {
            "hover_readiness": "READY", "hover_program_ms": hover_ms,
            "model_contract_correct": True, "candidate_id": "roads",
            "model_point": [820, 51], "reported_input_tokens": 9932,
            "model_runner_ms": model["runner_ms"],
            "mint_source_and_fresh_hover_patch_exact": True,
            "binding_translation": delta,
            "post_move_handle_status": "MISSING",
            "post_move_handle_reason": "region_pixels_missing",
            "hover_changed_pixels_in_target_patch": hover_changed_pixels,
            "pre_hover_patch_equals_post_move_unhovered_patch": True,
            "target_pointer_admissions": 0,
            "terminal_status": "needs_decision",
            "release_verified": True,
            "formal_independent_evaluation": False,
            "posthoc_observer_records": observer_records,
            "posthoc_independent_success": False,
            "decision_to_safe_stop_ms": safe_stop_ms,
            "durable_calls": 14},
        "direct_point_baseline": {
            "semantic_grounding": "0/2", "stable_input_tokens": 9296,
            "stable_decision_to_evaluation_ms": 18628.776261},
        "exact_frames": {"association-fault": 23, "stable": 25},
        "total_exact_frames": 48,
        "preregistered_gate_passed": False,
        "decision": "HOLD_AND_PRESERVE_INTERACTION_CONDITIONED_TARGET_FAILURE",
        "next_hypothesis": (
            "separate hover evidence from persistent target identity by clearing the "
            "pointer and rebasing mint to the retained pre-hover patch"),
        "limits": plan["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main():
    try:
        result = audit()
    except Exception as error:
        result = {"audit_passed": False, "error_type": type(error).__name__,
                  "error": str(error),
                  "decision": "HOLD_AND_PRESERVE_HOVER_TARGET_PAIR"}
        (ROOT / "audit.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
