"""Audit the preregistered persistent-target rebase pair from durable artifacts."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame
from hover_target_contract_v1 import runtime_reference
from model_point_target_v1 import patch
from openttd_hover_evidence_v1 import CANDIDATES, ORDER, classify, verify as verify_hover
from openttd_target_rebase_v1 import verify as verify_rebase


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-hover-rebased-pair-01"
PRIOR = HERE / "results/openttd-hover-target-pair-01"
NEGATIVE = ROOT / "1-rehover-negative-seed991004"
STABLE = ROOT / "2-stable-seed991004"
PATCH_SHA = "a2a5675570c583f7acdf1f545fd5ca706ccb367f58b89b688c4658e2b2e3b2e8"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def records(call):
    return call["result"].get("reply", {}).get("records", [])


def first(rows, event):
    return next(row for row in rows if row.get("event") == event)


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


def hover_steps():
    steps = []
    for name in ORDER:
        x, y = CANDIDATES[name]["point"]
        steps.extend([{"op": "pointer_move", "x": x, "y": y},
                      {"op": "dwell_observe", "delay_ms": 800},
                      {"op": "observe"}])
    return steps


def audit():
    prereg = read(ROOT / "preregistration.json")
    for name, digest in prereg["sources"].items():
        assert sha(source_path(name)) == digest, name
    prior = read(PRIOR / "audit.json")
    assert prior["decision"] == "HOLD_AND_PRESERVE_INTERACTION_CONDITIONED_TARGET_FAILURE"

    report = read(ROOT / "report.json")
    assert report["promotion_gate"] == {
        "hover_and_rebase_ready_2_of_2": True,
        "model_contract_correct_2_of_2": True,
        "rehover_negative_refused_before_target_click": True,
        "stable_moved_handle_and_engine_success": True,
        "passed": True}
    assert [case["name"] for case in report["cases"]] == ["rehover-negative", "stable"]

    decoded = {}
    for name, root in (("rehover-negative", NEGATIVE), ("stable", STABLE)):
        events, images = replay(root)
        decoded[name] = (events, images)
        assert all(row["release"]["verified"] is True
                   for row in events if row.get("event") == "terminal")
        assert read(root / "runtime/cleanup.json") == {
            "all_owned_processes_exited": True, "save_unchanged": True}

    plans = []
    prompts = []
    case_audit = {}
    for case, root in zip(report["cases"], (NEGATIVE, STABLE)):
        calls = read(root / "calls.json")
        assert len(calls) == case["durable_calls"]
        readiness = verify_hover(records(calls[5]), hover_steps(), root / "runtime")
        assert readiness == case["hover_readiness"]
        assert [row["candidate_id"] for row in readiness["evidence"]] == ORDER
        assert [row["tooltip_sha256"] for row in readiness["evidence"]] == [
            CANDIDATES[name]["tooltip_sha256"] for name in ORDER]

        model = read(root / "model-result.json")
        assert model["strict_contract_correct"] is True and model["contract_error"] is None
        assert runtime_reference(model["typed"]) == model["runtime_reference"]
        assert model["runtime_reference"] == {
            "candidate_id": "roads", "point": [820, 51],
            "coordinate_frame": "window_content",
            "point_space": "source_observation_pixels",
            "motion_model": "surface_origin_translation"}
        assert model["usage"]["cached_input_tokens"] == 0
        plan = read(root / "model-hover-contract/plan.json")
        process = read(root / "model-hover-contract/process.json")
        assert plan["requested_model"] == "gpt-5.6-luna"
        assert plan["requested_effort"] == "low"
        assert plan["image_sha256"] == sha(root / "hover-presentation.png")
        assert plan["instructions_sha256"] == sha(HERE / "hover_target_reference_responder_v1.txt")
        assert plan["schema_sha256"] == sha(HERE / "hover_target_contract_schema_v1.json")
        assert process["exit_code"] == 0
        assert process["observed_model_identity"] is None and process["cost"] is None
        plans.append((plan["requested_model"], plan["requested_effort"],
                      plan["instructions_sha256"], plan["schema_sha256"]))
        prompts.append(sha(root / "hover-contract-prompt.txt"))

        source = case["source_before_hover"]
        current = case["clear_observation"]
        rebase = verify_rebase(
            source, root / "runtime" / f'{source["sequence"]:03d}.png',
            current, root / "runtime" / f'{current["sequence"]:03d}.png',
            [820, 51], [24, 14])
        assert rebase == case["rebase"] and rebase["patch_sha256"] == PATCH_SHA
        minted = case["minted"]
        assert minted["source_sequence"] == 15 and minted["fresh_sequence"] == 28
        assert minted["fresh_patch_exact"] is True
        assert minted["source_patch_sha256"] == minted["fresh_patch_sha256"] == PATCH_SHA
        images = decoded[case["name"]][1]
        assert hashlib.sha256(patch(images[15], [808, 44, 24, 14])).hexdigest() == PATCH_SHA
        assert hashlib.sha256(patch(images[28], [808, 44, 24, 14])).hexdigest() == PATCH_SHA

        case_audit[case["name"]] = {
            "hover_readiness": "READY", "model_candidate": "roads",
            "model_point": [820, 51],
            "input_tokens": model["usage"]["input_tokens"],
            "cached_input_tokens": model["usage"]["cached_input_tokens"],
            "hover_program_ms": case["timing_ms"]["hover_submit_to_return"],
            "decision_to_evaluation_ms": case["timing_ms"]["decision_start_to_evaluation_return"],
            "durable_calls": len(calls), "persistent_patch_rebased": True}

    assert plans[0] == plans[1]
    assert prompts[0] == prompts[1]
    assert [case_audit[name]["input_tokens"] for name in case_audit] == [9936, 9935]

    negative = report["cases"][0]
    neg_calls = read(NEGATIVE / "calls.json")
    rehover_records = records(neg_calls[11])
    rehover_admissions = [row for row in rehover_records
                          if row.get("event") == "pointer_admission"]
    assert [(row["step"], row["operation"], row["payload"])
            for row in rehover_admissions] == [(0, "move", {"x": 820, "y": 51})]
    rehover_observations = [row for row in rehover_records
                            if row.get("event") == "observation" and row.get("step") in (1, 2)]
    assert len(rehover_observations) == 2
    rehover_classes = [classify(NEGATIVE / "runtime" / Path(row["image"]).name)
                        for row in rehover_observations]
    assert [row["candidate_id"] for row in rehover_classes] == ["roads", "roads"]
    assert [row["tooltip_sha256"] for row in rehover_classes] == [
        CANDIDATES["roads"]["tooltip_sha256"]] * 2
    assert negative["handle_check"]["status"] == "MISSING"
    assert negative["handle_check"]["reason"] == "region_pixels_missing"
    assert negative["program_pointer_admissions"] == [] and negative["terminal"] is None
    assert negative["independent_evaluation"]["success"] is False
    case_audit["rehover-negative"].update({
        "rehover_evidence": "READY", "post_rehover_handle": "MISSING",
        "post_rehover_reason": "region_pixels_missing", "target_pointer_admissions": 0,
        "independent_success": False, "safe_refusal": True})

    stable = report["cases"][1]
    assert stable["actual_surface_delta"] == [21, 28]
    assert stable["handle_check"]["status"] == "REVALIDATED"
    assert stable["handle_check"]["point"] == [841, 79]
    assert stable["handle_check"]["observed_box"] == [829, 72, 24, 14]
    assert stable["admission_revalidation"]["status"] == "REVALIDATED"
    measurement = stable["local_condition"]["measurements"][-1]
    assert measurement["target_changed_total"] == 160
    assert measurement["guard_changed_total"] == 0
    assert stable["program_steps_started"] == list(range(8))
    assert stable["terminal"]["status"] == "completed"
    assert stable["terminal"]["release"]["verified"] is True
    assert stable["independent_evaluation"]["success"] is True
    assert all(stable["independent_evaluation"]["checks"].values())
    case_audit["stable"].update({
        "surface_delta": [21, 28], "revalidated_point": [841, 79],
        "local_target_changed_pixels": 160, "local_guard_changed_pixels": 0,
        "program_steps_completed": 8, "terminal_status": "completed",
        "release_verified": True, "independent_success": True})

    frame_counts = {name: len(images) for name, (_, images) in decoded.items()}
    assert frame_counts == {"rehover-negative": 32, "stable": 49}
    result = {
        "audit_passed": True, "preregistered_sources_match": True,
        "prior_failure_preserved": True, "report_gate_reconstructed": True,
        "same_model_plan_and_prompt": True,
        "observed_model_identity": None, "reported_cost": None,
        "cases": case_audit, "exact_frames": frame_counts,
        "total_exact_frames": sum(frame_counts.values()),
        "direct_point_baseline": {"semantic_grounding": "0/2",
                                  "stable_input_tokens": 9296,
                                  "stable_decision_to_evaluation_ms": 18628.776261},
        "first_hover_failure": {"model_semantic_selection": "1/1",
                                "reported_input_tokens": 9932,
                                "decision_to_safe_stop_ms": 13207.127},
        "preregistered_gate_passed": True,
        "decision": "RETAIN_PERSISTENT_TARGET_REBASE_CANDIDATE",
        "next_hypothesis": ("trigger active hover evidence only under uncertainty, then test "
                            "a held-out toolbar target or changed candidate layout"),
        "limits": report["scope"]}
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    return result


def main():
    try:
        result = audit()
    except Exception as error:
        result = {"audit_passed": False, "error_type": type(error).__name__,
                  "error": str(error),
                  "decision": "HOLD_AND_PRESERVE_HOVER_REBASED_PAIR"}
        (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
        print(json.dumps(result, indent=2))
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
