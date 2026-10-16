"""Audit preregistered model-point target minting and changed-patch refusal."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from model_point_target_v1 import derive, patch


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/chromium-model-point-target-pair-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(root):
    rows = [json.loads(line) for line in
            (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in rows if row.get("event") == "observation"]
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
    return rows, images


def assert_model_plan(root, label, mode, image_expected):
    plan = read(root / f"model-{label}/plan.json")
    process = read(root / f"model-{label}/process.json")
    assert plan["requested_model"] == "gpt-5.6-luna"
    assert plan["requested_effort"] == "low" and plan["mode"] == mode
    assert (plan["image_sha256"] is not None) is image_expected
    assert plan["instructions_sha256"] == sha(HERE / "gui_action_responder_v1.txt")
    assert plan["schema_sha256"] == sha(HERE / "target_action_envelope_schema_v1.json")
    assert process["exit_code"] == 0
    assert process["requested_model"] == "gpt-5.6-luna"
    assert process["requested_effort"] == "low"
    assert process["observed_model_identity"] is None and process["cost"] is None
    return plan


def patch_digest(image, box):
    return hashlib.sha256(patch(image, box)).hexdigest()


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["promotion_gate"]["passed"] is True
    assert report["decision"] == "RETAIN_MODEL_POINT_DERIVED_TARGET_CANDIDATE"
    expected = [(row["name"], row["changed_target"], row["seed"])
                for row in plan["execution_order"]]
    assert [(row["name"], row["changed_target"], row["seed"])
            for row in report["cases"]] == expected

    roots = {row["name"]: ROOT / f"{row['index']}-{row['name']}-seed{row['seed']}"
             for row in report["cases"]}
    assert sha(roots["changed-target"] / "coordinate-prompt.txt") == \
        sha(roots["stable"] / "coordinate-prompt.txt")
    coordinate_prompt = (roots["stable"] / "coordinate-prompt.txt").read_text(
        encoding="utf-8")
    assert "absolute screenshot x/y" in coordinate_prompt
    assert read(roots["changed-target"] / "coordinate-result.json") == \
        report["cases"][0]["coordinate_model"]
    frame_counts = {}
    images = {}
    for row in report["cases"]:
        root = roots[row["name"]]
        assert row == read(root / "result.json")
        events, by_sequence = replay(root)
        images[row["name"]] = by_sequence
        frame_counts[row["name"]] = len(by_sequence)
        assert all(event["release"]["verified"] is True
                   for event in events if event.get("event") == "terminal")
        assert row["coordinate_model"]["strict_shape_correct"] is True
        coordinate_plan = assert_model_plan(root, "coordinate", "coordinate", True)
        assert coordinate_plan["image_sha256"] == sha(
            root / "runtime" / Path(row["source_observation"]["image"]).name)
        assert row["model_point"] == [270, 243]
        assert derive(row["model_point"], [24, 14]) == {
            "box": [258, 236, 24, 14], "offset": [12, 7]}
        assert row["mint_step"]["source_sequence"] == 12
        assert row["mint_step"]["point"] == row["model_point"]
        assert row["mint_step"]["region_size"] == [24, 14]
        assert row["bridge_exit_code"] == 0

    stable = next(row for row in report["cases"] if row["name"] == "stable")
    changed = next(row for row in report["cases"] if row["name"] == "changed-target")
    stable_root, changed_root = roots["stable"], roots["changed-target"]
    stable_images, changed_images = images["stable"], images["changed-target"]

    minted = stable["minted"]
    assert minted["handle"] == "save_form" and minted["status"] == "VALID"
    assert minted["reference_kind"] == "session_alias"
    assert minted["private_registry_id_exposed"] is False
    assert minted["source_sequence"] == 12 and minted["fresh_sequence"] == 13
    assert minted["source_point"] == stable["model_point"]
    assert minted["derived_box"] == [258, 236, 24, 14]
    assert minted["derived_offset"] == [12, 7]
    source_digest = patch_digest(stable_images[12], minted["derived_box"])
    fresh_digest = patch_digest(stable_images[13], minted["derived_box"])
    assert source_digest == fresh_digest == minted["source_patch_sha256"]
    assert fresh_digest == minted["fresh_patch_sha256"] == minted["patch_sha256"]
    assert minted["fresh_patch_exact"] is True
    assert stable["mint_terminal"]["status"] == "completed"
    assert stable["surface_move"]["before"]["geometry"] == [10, 10, 1050, 780]
    assert stable["surface_move"]["after"]["geometry"] == [30, 18, 1050, 780]
    checked = stable["handle_check"]
    assert checked["status"] == "REVALIDATED" and checked["eligible"] is True
    assert checked["binding_translation"] == [20, 8]
    assert checked["observed_box"] == [278, 244, 24, 14]
    assert checked["point"] == [290, 251]
    assert checked["private_registry_id_exposed"] is False
    handle_plan = assert_model_plan(stable_root, "handle", "handle", False)
    assert handle_plan["image_sha256"] is None
    assert stable["handle_model"]["strict_shape_correct"] is True
    assert stable["handle_model"]["typed"]["target"] == {
        "kind": "handle", "x": 0, "y": 0, "target_handle": "save_form",
        "dx": 12, "dy": 7}
    assert stable["admission_revalidation"]["status"] == "REVALIDATED"
    assert stable["admission_revalidation"]["private_registry_id_exposed"] is False
    assert [(row["operation"], row["payload"])
            for row in stable["target_action_pointer_admissions"]] == [
        ("move", {"x": 290, "y": 251}), ("button_down", 1)]
    assert stable["click_terminal"]["status"] == "completed"
    assert stable["click_terminal"]["release"]["verified"] is True
    assert stable["independent_evaluation"]["success"] is True
    assert parse_qs((stable_root / "runtime/submitted.txt").read_text()) == {
        "value": ["t991014"]}
    assert stable["durable_calls"] == 16

    refusal = changed["mint_refusal"]
    assert changed["minted"] is None and refusal["handle_created"] is False
    assert refusal["reason"] == "source_patch_changed"
    assert refusal["source_sequence"] == 12 and refusal["current_sequence"] == 19
    assert refusal["predicted_box"] == [258, 236, 24, 14]
    changed_source_digest = patch_digest(changed_images[12], refusal["predicted_box"])
    changed_current_digest = patch_digest(changed_images[19], refusal["predicted_box"])
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

    tokens = report["reported_input_tokens"]
    assert tokens == {"changed-target": {"coordinate": 9285, "handle": None},
                      "stable": {"coordinate": 9284, "handle": 8012}}
    audit = {
        "audit_passed": True,
        "preregistered_sources_match": True,
        "same_coordinate_prompt_sha256": sha(stable_root / "coordinate-prompt.txt"),
        "model_configuration": {
            "requested_model": "gpt-5.6-luna", "requested_effort": "low",
            "coordinate_image_present": True, "handle_image_present": False,
            "observed_model_identity": None, "cost": None},
        "posthoc_contract_review": {
            "numeric_basis_requested": "absolute screenshot x/y",
            "transformation_frame_assigned_by_caller": "window_content",
            "aligned": False,
            "effect": "the run proves this caller assignment follows one surface move, but does not prove that the model authored or understood the frame",
        },
        "reported_input_tokens": tokens,
        "stable": {
            "model_point": stable["model_point"],
            "derived_box": minted["derived_box"],
            "derived_offset": minted["derived_offset"],
            "source_and_fresh_patch_exact": True,
            "binding_translation": checked["binding_translation"],
            "resolved_point": checked["point"],
            "target_pointer_admissions": 2,
            "durable_calls": stable["durable_calls"],
            "independent_success": True},
        "changed_target": {
            "refusal": refusal["reason"], "handle_created": False,
            "source_and_current_patch_differ": True,
            "target_pointer_admissions": 0,
            "terminal_status": changed["mint_terminal"]["status"],
            "durable_calls": changed["durable_calls"],
            "independent_success": False},
        "exact_frames": frame_counts,
        "total_exact_frames": sum(frame_counts.values()),
        "promotion_gate": report["promotion_gate"],
        "preregistered_decision": report["decision"],
        "audit_decision": "HOLD_FOR_EXPLICIT_COORDINATE_FRAME_AUTHORSHIP",
        "scope": report["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
