"""Audit the frozen Chromium observe-target pair and replay every exact frame."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/chromium-observe-target-pair-01"


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
    assert [(row["mode"], row["seed"]) for row in report["cases"]] == [
        (row["mode"], row["seed"]) for row in plan["execution_order"]
    ]
    frames = {}
    for row in report["cases"]:
        root = ROOT / f"{row['index']}-{row['mode']}-seed{row['seed']}"
        assert row == read(root / "result.json")
        count, events = replay(root)
        frames[row["mode"]] = count
        assert row["handle_check"]["status"] == "REVALIDATED"
        assert row["admission_revalidation"]["status"] == "REVALIDATED"
        assert row["handle_check"]["handle"] == "save_form"
        assert row["admission_revalidation"]["handle"] == "save_form"
        assert row["handle_check"]["private_registry_id_exposed"] is False
        assert row["admission_revalidation"]["private_registry_id_exposed"] is False
        assert row["terminal"]["status"] == "completed"
        assert row["terminal"]["release"]["verified"] is True
        assert row["independent_evaluation"]["success"] is True
        assert parse_qs((root / "runtime/submitted.txt").read_text()) == {
            "value": [row["goal"]["token"]]
        }
        assert len(row["pointer_admissions"]) == 2
        assert len([event for event in events
                    if event.get("event") == "target_handle_revalidated"]) == 1
    combined = next(row for row in report["cases"] if row["mode"] == "combined")
    separate = next(row for row in report["cases"] if row["mode"] == "separate")
    assert combined["handle_check"]["observation_sequence"] == \
        combined["fresh_observation"]["sequence"]
    assert combined["handle_check"]["observation_capture_ns"] == \
        combined["fresh_observation"]["capture_ns"]
    assert combined["durable_calls"] == 12
    assert separate["durable_calls"] == 14
    audit = {
        "audit_passed": True,
        "fresh_independent_success": "2/2",
        "fresh_identity_exact": True,
        "durable_calls": {"combined": 12, "separate": 14},
        "observe_check_submit_to_return_ms": {
            "combined": combined["observe_check_submit_to_return_ms"],
            "separate": separate["observe_check_submit_to_return_ms"],
            "interpretation": "descriptive single-pair values; no causal latency claim",
        },
        "exact_frames": frames,
        "total_exact_frames": sum(frames.values()),
        "retained_probe_failures": plan["known_probe_failures"],
        "scope": report["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
