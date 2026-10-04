"""Audit model use of combined observe-target and stale-target refusal."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/chromium-observe-target-model-pair-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
    return len(observations), events


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["promotion_gate"]["passed"] is True
    assert [(row["name"], row["changed_target"], row["seed"])
            for row in report["cases"]] == [
        (row["name"], row["changed_target"], row["seed"])
        for row in plan["execution_order"]]
    roots = {row["name"]: ROOT / f"{row['index']}-{row['name']}-seed{row['seed']}"
             for row in report["cases"]}
    assert sha(roots["changed-target"] / "model-prompt.txt") == \
        sha(roots["stable"] / "model-prompt.txt")
    frames = {}
    for row in report["cases"]:
        root = roots[row["name"]]
        assert row == read(root / "result.json")
        count, events = replay(root)
        frames[row["name"]] = count
        assert row["model"]["strict_shape_correct"] is True
        assert row["model"]["usage"]["input_tokens"] == 8013
        assert row["handle_check"]["observation_sequence"] == \
            row["fresh_observation"]["sequence"]
        assert row["handle_check"]["observation_capture_ns"] == \
            row["fresh_observation"]["capture_ns"]
        for record in (row["minted"], row["handle_check"],
                       row["admission_revalidation"]):
            assert record["handle"] == "save_form"
            assert record["private_registry_id_exposed"] is False
        model_plan = read(root / "model/plan.json")
        assert model_plan["requested_model"] == "gpt-5.6-luna"
        assert model_plan["requested_effort"] == "low"
        assert model_plan["mode"] == "handle" and model_plan["image_sha256"] is None
        assert model_plan["instructions_sha256"] == sha(HERE / "gui_action_responder_v1.txt")
        assert model_plan["schema_sha256"] == sha(HERE / "target_action_envelope_schema_v1.json")
        assert len([event for event in events if event.get("event") == "terminal"]) >= 1
    stable = next(row for row in report["cases"] if row["name"] == "stable")
    changed = next(row for row in report["cases"] if row["name"] == "changed-target")
    assert stable["durable_calls"] == 14
    assert stable["admission_revalidation"]["status"] == "REVALIDATED"
    assert len(stable["target_action_pointer_admissions"]) == 2
    assert stable["terminal"]["status"] == "completed"
    assert stable["terminal"]["release"]["verified"] is True
    assert stable["independent_evaluation"]["success"] is True
    assert parse_qs((roots["stable"] / "runtime/submitted.txt").read_text()) == {
        "value": [stable["goal"]["token"]]}
    assert changed["admission_revalidation"]["status"] == "MISSING"
    assert changed["admission_revalidation"]["reason"] == "region_pixels_missing"
    assert changed["target_action_pointer_admissions"] == []
    assert changed["terminal"]["status"] == "needs_decision"
    assert changed["terminal"]["release"]["verified"] is True
    assert changed["independent_evaluation"]["success"] is False
    assert not (roots["changed-target"] / "runtime/submitted.txt").exists()
    prior = read(HERE / "results/chromium-target-handle-model-abba-03/report.json")
    prior_handle_calls = [row["durable_calls"] for row in prior["cases"]
                          if row["mode"] == "handle"]
    assert prior_handle_calls == [16, 16]
    audit = {
        "audit_passed": True,
        "same_prompt_sha256": sha(roots["stable"] / "model-prompt.txt"),
        "strict_model_actions": "2/2",
        "reported_input_tokens": {"changed-target": 8013, "stable": 8013},
        "stable": {"durable_calls": 14, "independent_success": True,
                   "admission_revalidation": "REVALIDATED"},
        "changed_target": {"durable_calls": changed["durable_calls"],
                           "target_action_pointer_admissions": 0,
                           "independent_success": False,
                           "admission_revalidation": "MISSING"},
        "prior_separate_query_handle_calls": prior_handle_calls,
        "exact_frames": frames,
        "total_exact_frames": sum(frames.values()),
        "decision_start_to_evaluation_return_ms": {
            row["name"]: row["decision_start_to_evaluation_return_ms"]
            for row in report["cases"]},
        "scope": report["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
