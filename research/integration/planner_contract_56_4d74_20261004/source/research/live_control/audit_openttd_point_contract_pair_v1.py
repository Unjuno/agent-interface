"""Audit the first cross-domain OpenTTD explicit point-contract pair."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from model_point_target_v1 import derive, patch
from point_target_contract_v2 import runtime_reference


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-point-contract-pair-01"
PRIOR = HERE / "results/openttd-observe-target-live-01/live/result.json"
EXPECTED_POINT = [820, 51]
EXPECTED_BOX = [812, 43, 16, 16]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(root):
    events = [json.loads(line) for line in
              (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    images = {}
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        image_path = root / "runtime" / Path(observation["image"]).name
        with Image.open(image_path) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        images[observation["sequence"]] = image
    assert len(list((root / "runtime").glob("*.ait"))) == len(observations)
    return events, images


def patch_digest(image, box):
    return hashlib.sha256(patch(image, box)).hexdigest()


def outside(point, box):
    x, y = point
    left, top, width, height = box
    return not (left <= x < left + width and top <= y < top + height)


def audit():
    prior = read(PRIOR)
    assert prior["handle_check"]["point"] == EXPECTED_POINT
    assert prior["handle_check"]["observed_box"] == EXPECTED_BOX
    assert prior["independent_evaluation"]["success"] is True
    assert all(prior["independent_evaluation"]["checks"].values())

    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        source = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(source) == digest, name
    assert plan["failure_policy"].startswith("retain both first sessions")

    report = read(ROOT / "report.json")
    assert report["promotion_gate"] == {
        "model_authored_contract_2_of_2": False,
        "model_input_range_at_most_128": True,
        "stable_moved_handle_and_engine_success": False,
        "transient_visual_change_refused": False,
        "passed": False,
    }
    assert report["decision"] == "HOLD_AND_PRESERVE_OPENTTD_POINT_PAIR"
    expected = [(row["name"], row["transient_target"], row["seed"])
                for row in plan["execution_order"]]
    assert [(row["name"], row["transient_target"], row["seed"])
            for row in report["cases"]] == expected

    roots = {row["name"]: ROOT / f"{row['index']}-{row['name']}-seed{row['seed']}"
             for row in report["cases"]}
    prompt_hash = sha(roots["transient-target"] / "point-contract-prompt.txt")
    assert prompt_hash == sha(roots["stable"] / "point-contract-prompt.txt")
    frames = {}
    images = {}
    expected_points = {"transient-target": [650, 51], "stable": [432, 51]}
    for row in report["cases"]:
        root = roots[row["name"]]
        assert row == read(root / "result.json")
        events, by_sequence = replay(root)
        frames[row["name"]] = len(by_sequence)
        images[row["name"]] = by_sequence
        assert all(event["release"]["verified"] is True
                   for event in events if event.get("event") == "terminal")
        cleanup = read(root / "runtime/cleanup.json")
        assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
        model = row["model"]
        assert model["typed"] == row["model_authored_contract"]
        assert runtime_reference(model["typed"]) == row["runtime_reference"]
        assert model["typed"]["point_space"] == "source_observation_pixels"
        assert model["typed"]["motion_model"] == "surface_origin_translation"
        point = list(model["typed"]["point"].values())
        assert point == expected_points[row["name"]]
        assert outside(point, EXPECTED_BOX)
        assert model["strict_contract_correct"] is False
        assert row["mint_step"]["coordinate_frame"] == "window_content"
        assert row["mint_step"]["point"] == point
        assert row["mint_step"]["region_size"] == [24, 14]
        model_plan = read(root / "model-point-contract/plan.json")
        process = read(root / "model-point-contract/process.json")
        assert model_plan["requested_model"] == "gpt-5.6-luna"
        assert model_plan["requested_effort"] == "low"
        assert model_plan["mode"] == "coordinate"
        assert model_plan["prompt_sha256"] == prompt_hash
        assert model_plan["instructions_sha256"] == sha(
            HERE / "point_target_reference_responder_v1.txt")
        assert model_plan["schema_sha256"] == sha(
            HERE / "point_target_contract_schema_v1.json")
        source_path = root / "runtime" / Path(row["source_observation"]["image"]).name
        assert model_plan["image_sha256"] == sha(source_path)
        assert process["exit_code"] == 0
        assert process["observed_model_identity"] is None and process["cost"] is None
        assert row["bridge_exit_code"] == 0

    transient = next(row for row in report["cases"] if row["name"] == "transient-target")
    stable = next(row for row in report["cases"] if row["name"] == "stable")

    assert [(row["operation"], row["payload"])
            for row in transient["transient_pointer_admissions"]] == [
        ("move", {"x": 820, "y": 51}), ("button_down", 1)]
    assert transient["transient_terminal"]["status"] == "completed"
    assert transient["mint_refusal"] is None
    assert transient["minted"]["derived_box"] == [638, 44, 24, 14]
    assert derive([650, 51], [24, 14])["box"] == [638, 44, 24, 14]
    source = transient["source_observation"]["sequence"]
    fresh = transient["minted"]["fresh_sequence"]
    source_digest = patch_digest(images["transient-target"][source], [638, 44, 24, 14])
    fresh_digest = patch_digest(images["transient-target"][fresh], [638, 44, 24, 14])
    assert source_digest == fresh_digest == transient["minted"]["patch_sha256"]
    assert transient["minted"]["fresh_patch_exact"] is True
    assert transient["program_pointer_admissions"] == []
    assert transient["independent_evaluation"]["success"] is False
    assert transient["independent_evaluation"]["checks"] == {
        "target_owned_roads": False,
        "ordered_bidirectional_connections": False,
        "forbidden_tiles_clear": True,
        "surrounding_road_owner_unchanged": True,
    }
    assert transient["durable_calls"] == 8

    assert stable["minted"]["derived_box"] == [420, 44, 24, 14]
    assert derive([432, 51], [24, 14])["box"] == [420, 44, 24, 14]
    stable_source = stable["source_observation"]["sequence"]
    stable_fresh = stable["minted"]["fresh_sequence"]
    stable_source_digest = patch_digest(
        images["stable"][stable_source], [420, 44, 24, 14])
    stable_fresh_digest = patch_digest(
        images["stable"][stable_fresh], [420, 44, 24, 14])
    assert stable_source_digest == stable_fresh_digest == stable["minted"]["patch_sha256"]
    assert stable["actual_surface_delta"] == [21, 28]
    assert stable["handle_check"]["binding_translation"] == [21, 28]
    assert stable["handle_check"]["point"] == [453, 79]
    assert stable["admission_revalidation"]["status"] == "REVALIDATED"
    assert stable["program_steps_started"] == [0, 1, 2, 3, 4]
    assert stable["local_condition"]["reason"] == "target_not_reached"
    assert stable["local_condition"]["measurements"][-1]["target_changed_total"] == 12
    assert stable["local_condition"]["measurements"][-1]["guard_changed_total"] == 0
    assert stable["terminal"]["status"] == "needs_decision"
    assert stable["terminal"]["steps_completed"] == 4
    assert stable["terminal"]["release"]["verified"] is True
    assert stable["independent_evaluation"]["success"] is False
    assert stable["independent_evaluation"]["checks"] == transient[
        "independent_evaluation"]["checks"]
    assert stable["durable_calls"] == 12

    assert report["reported_input_tokens"] == {
        "transient-target": 9297, "stable": 9296}
    result = {
        "audit_passed": True,
        "preregistered_sources_match": True,
        "prior_known_target": {"point": EXPECTED_POINT, "box": EXPECTED_BOX,
                               "independent_success": True},
        "same_prompt_sha256": prompt_hash,
        "model_configuration": {
            "requested_model": "gpt-5.6-luna", "requested_effort": "low",
            "image_present": True, "observed_model_identity": None, "cost": None},
        "explicit_contract_semantics": {
            "point_space_correct": "2/2", "motion_model_correct": "2/2",
            "semantic_point_grounding_correct": "0/2",
            "model_points": expected_points},
        "reported_input_tokens": report["reported_input_tokens"],
        "cached_input_tokens": {
            row["name"]: row["model"]["usage"]["cached_input_tokens"]
            for row in report["cases"]},
        "transient_target": {
            "known_target_click_admissions": 2,
            "model_region_unchanged": True,
            "expected_refusal_observed": False,
            "handle_created_for_wrong_icon": True,
            "independent_success": False,
            "durable_calls": 8,
            "timing_ms": transient["timing_ms"]},
        "stable": {
            "wrong_icon_handle_revalidated": True,
            "binding_translation": [21, 28],
            "local_condition": "target_not_reached",
            "target_changed_total": 12,
            "guard_changed_total": 0,
            "terminal_status": "needs_decision",
            "release_verified": True,
            "independent_success": False,
            "durable_calls": 12,
            "timing_ms": stable["timing_ms"]},
        "exact_frames": frames,
        "total_exact_frames": sum(frames.values()),
        "promotion_gate": report["promotion_gate"],
        "preregistered_decision": report["decision"],
        "audit_decision": "RETAIN_CROSS_DOMAIN_GROUNDING_FAILURE",
        "next_hypothesis": "add bounded hover-label evidence for dense icon-only controls",
        "limits": report["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main():
    try:
        result = audit()
    except Exception as error:
        result = {
            "audit_passed": False,
            "error_type": type(error).__name__,
            "error": str(error),
            "decision": "HOLD_AND_PRESERVE_OPENTTD_POINT_PAIR",
            "failure_policy": "preserve both first preregistered sessions; do not retry or repair in place",
        }
        (ROOT / "audit.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
