"""Audit cross-domain observe-target use and replay all OpenTTD frames."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-observe-target-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(path) == digest, name
    report = read(ROOT / "report.json")
    result = read(ROOT / "live/result.json")
    assert report["passed"] is True and report["case"] == result
    assert result["handle_check"]["observation_sequence"] == \
        result["fresh_observation"]["sequence"]
    assert result["handle_check"]["observation_capture_ns"] == \
        result["fresh_observation"]["capture_ns"]
    for record in (result["minted"], result["handle_check"],
                   result["admission_revalidation"]):
        assert record["handle"] == "road_construction_opener"
        assert record["private_registry_id_exposed"] is False
    assert result["handle_check"]["status"] in ("VALID", "REVALIDATED")
    assert result["admission_revalidation"]["status"] in ("VALID", "REVALIDATED")
    assert result["local_condition"]["reason"] == "met"
    assert result["local_condition"]["measurements"][-1]["target_changed_total"] >= 120
    assert result["local_condition"]["measurements"][-1]["guard_changed_total"] <= 20
    assert result["steps_started"] == list(range(8))
    assert result["terminal"]["status"] == "completed"
    assert result["terminal"]["release"]["verified"] is True
    assert result["bridge_exit_code"] == 0
    evaluation = result["independent_evaluation"]
    assert evaluation["success"] is True and all(evaluation["checks"].values())
    assert evaluation["changed_surrounding_tiles"] == []
    assert read(ROOT / "live/runtime/evaluation.json")["success"] is True
    cleanup = read(ROOT / "live/runtime/cleanup.json")
    assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
    events = [json.loads(line) for line in
              (ROOT / "live/runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept(
            (ROOT / "live/runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(ROOT / "live/runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    assert len(observations) == 37
    assert len(list((ROOT / "live/runtime").glob("*.ait"))) == 37
    audit = {
        "audit_passed": True,
        "fresh_observation_identity_exact": True,
        "handle_check_status": result["handle_check"]["status"],
        "admission_revalidation_status": result["admission_revalidation"]["status"],
        "local_condition": {
            "reason": result["local_condition"]["reason"],
            "target_changed_total": result["local_condition"]["measurements"][-1]["target_changed_total"],
            "guard_changed_total": result["local_condition"]["measurements"][-1]["guard_changed_total"],
        },
        "independent_checks": evaluation["checks"],
        "durable_calls": result["durable_calls"],
        "exact_frames": len(observations),
        "observe_check_submit_to_return_ms": result["observe_check_submit_to_return_ms"],
        "program_submit_to_return_ms": result["program_submit_to_return_ms"],
        "cleanup": cleanup,
        "scope": report["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
