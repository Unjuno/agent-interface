"""Audit explicit model-authored point space and motion semantics."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from model_point_target_v1 import derive, patch
from point_target_contract_v2 import runtime_reference


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/chromium-point-contract-pair-01"
PRIOR = HERE / "results/chromium-model-point-target-pair-01/audit.json"


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


def audit():
    prior = read(PRIOR)
    assert prior["audit_decision"] == "HOLD_FOR_EXPLICIT_COORDINATE_FRAME_AUTHORSHIP"
    assert prior["posthoc_contract_review"]["aligned"] is False
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["promotion_gate"]["passed"] is True
    assert report["decision"] == "ADVANCE_EXPLICIT_POINT_SPACE_AND_MOTION_CONTRACT"
    expected = [(row["name"], row["changed_target"], row["seed"])
                for row in plan["execution_order"]]
    assert [(row["name"], row["changed_target"], row["seed"])
            for row in report["cases"]] == expected
    roots = {row["name"]: ROOT / f"{row['index']}-{row['name']}-seed{row['seed']}"
             for row in report["cases"]}
    prompt_hash = sha(roots["stable"] / "point-contract-prompt.txt")
    assert prompt_hash == sha(roots["changed-target"] / "point-contract-prompt.txt")
    frames = {}
    images = {}
    for row in report["cases"]:
        root = roots[row["name"]]
        assert row == read(root / "result.json")
        events, by_sequence = replay(root)
        frames[row["name"]] = len(by_sequence)
        images[row["name"]] = by_sequence
        assert all(event["release"]["verified"] is True
                   for event in events if event.get("event") == "terminal")
        model = row["model"]
        assert model["strict_contract_correct"] is True
        assert runtime_reference(model["typed"]) == row["runtime_reference"]
        assert model["typed"] == row["model_authored_contract"]
        assert model["typed"] == {
            "op": "target_reference",
            "point_space": "source_observation_pixels",
            "point": {"x": 270, "y": 243},
            "motion_model": "surface_origin_translation"}
        assert row["runtime_reference"] == {
            "point": [270, 243], "coordinate_frame": "window_content",
            "point_space": "source_observation_pixels",
            "motion_model": "surface_origin_translation"}
        assert row["mint_step"]["coordinate_frame"] == "window_content"
        assert row["mint_step"]["point"] == [270, 243]
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

    stable = next(row for row in report["cases"] if row["name"] == "stable")
    changed = next(row for row in report["cases"] if row["name"] == "changed-target")
    stable_root, changed_root = roots["stable"], roots["changed-target"]
    minted = stable["minted"]
    assert derive([270, 243], [24, 14]) == {
        "box": [258, 236, 24, 14], "offset": [12, 7]}
    assert minted["derived_box"] == [258, 236, 24, 14]
    assert minted["derived_offset"] == [12, 7]
    assert minted["private_registry_id_exposed"] is False
    stable_source = stable["source_observation"]["sequence"]
    stable_fresh = minted["fresh_sequence"]
    source_digest = patch_digest(images["stable"][stable_source], minted["derived_box"])
    fresh_digest = patch_digest(images["stable"][stable_fresh], minted["derived_box"])
    assert source_digest == fresh_digest == minted["source_patch_sha256"]
    assert fresh_digest == minted["fresh_patch_sha256"]
    assert stable["surface_move"]["before"]["geometry"] == [10, 10, 1050, 780]
    assert stable["surface_move"]["after"]["geometry"] == [30, 18, 1050, 780]
    assert stable["handle_check"]["binding_translation"] == [20, 8]
    assert stable["handle_check"]["point"] == [290, 251]
    assert stable["admission_revalidation"]["status"] == "REVALIDATED"
    assert [(row["operation"], row["payload"])
            for row in stable["target_action_pointer_admissions"]] == [
        ("move", {"x": 290, "y": 251}), ("button_down", 1)]
    assert stable["click_terminal"]["status"] == "completed"
    assert stable["click_terminal"]["release"]["verified"] is True
    assert stable["independent_evaluation"]["success"] is True
    assert parse_qs((stable_root / "runtime/submitted.txt").read_text()) == {
        "value": ["t991015"]}
    assert stable["durable_calls"] == 14

    refusal = changed["mint_refusal"]
    assert changed["minted"] is None
    assert refusal["reason"] == "source_patch_changed"
    assert refusal["handle_created"] is False
    changed_source = changed["source_observation"]["sequence"]
    changed_current = refusal["current_sequence"]
    changed_source_digest = patch_digest(
        images["changed-target"][changed_source], refusal["predicted_box"])
    changed_current_digest = patch_digest(
        images["changed-target"][changed_current], refusal["predicted_box"])
    assert changed_source_digest == refusal["source_patch_sha256"]
    assert changed_current_digest == refusal["current_patch_sha256"]
    assert changed_source_digest != changed_current_digest
    assert changed["mint_terminal"]["status"] == "needs_decision"
    assert changed["mint_terminal"]["steps_completed"] == 0
    assert changed["mint_terminal"]["release"]["verified"] is True
    assert changed["target_action_pointer_admissions"] == []
    assert changed["independent_evaluation"]["success"] is False
    assert not (changed_root / "runtime/submitted.txt").exists()
    assert changed["durable_calls"] == 10

    assert report["reported_input_tokens"] == {"stable": 9264, "changed-target": 9265}
    audit = {
        "audit_passed": True,
        "preregistered_sources_match": True,
        "repairs_prior_contract_hold": True,
        "same_prompt_sha256": prompt_hash,
        "model_authored_contracts": "2/2",
        "point_space": "source_observation_pixels",
        "motion_model": "surface_origin_translation",
        "runtime_coordinate_frame": "window_content",
        "reported_input_tokens": report["reported_input_tokens"],
        "cached_input_tokens": {
            row["name"]: row["model"]["usage"]["cached_input_tokens"]
            for row in report["cases"]},
        "stable": {"independent_success": True, "durable_calls": 14,
                   "binding_translation": [20, 8],
                   "target_pointer_admissions": 2,
                   "timing_ms": stable["timing_ms"]},
        "changed_target": {"independent_success": False, "durable_calls": 10,
                           "refusal": "source_patch_changed",
                           "handle_created": False, "target_pointer_admissions": 0,
                           "timing_ms": changed["timing_ms"]},
        "exact_frames": frames,
        "total_exact_frames": sum(frames.values()),
        "promotion_gate": report["promotion_gate"],
        "decision": report["decision"],
        "limits": "one known Chromium button; fixed caller-authored24x14 region; no cross-domain, causal speed, cost, broad token or human-tempo claim",
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    return audit


def main():
    try:
        result = audit()
    except Exception as error:
        result = {
            "audit_passed": False,
            "error_type": type(error).__name__,
            "error": str(error),
            "decision": "HOLD_AND_PRESERVE_POINT_CONTRACT_PAIR",
            "failure_policy": "preserve the first preregistered sessions; do not retry or repair in place",
        }
        (ROOT / "audit.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
