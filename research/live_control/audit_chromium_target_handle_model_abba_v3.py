"""Audit fresh Chromium alias-handle live ABBA and replay exact frames."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/chromium-target-handle-model-abba-03"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(root):
    events = [
        json.loads(line)
        for line in (root / "runtime/events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept(
            (root / "runtime" / f"{index:03d}.ait").read_bytes()
        )
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    return events, len(observations)


def main():
    plan = read(ROOT / "preregistration.json")
    first_failure = read(
        HERE / "results/chromium-target-handle-model-abba-01/failure.json"
    )
    assert first_failure["gui_sessions_started"] == 0
    assert first_failure["model_calls"] == 0
    predecessor_root = HERE / "results/chromium-target-handle-model-abba-02"
    predecessor = read(predecessor_root / "report.json")
    predecessor_coordinate = [
        row for row in predecessor["cases"] if row["mode"] == "coordinate"
    ]
    predecessor_handle = [
        row for row in predecessor["cases"] if row["mode"] == "handle"
    ]
    assert all(row["independent_evaluation"]["success"]
               for row in predecessor_coordinate)
    assert all(
        row["handle_query"]["status"] == "REVALIDATED"
        and row["admission_revalidation"]["status"] == "MISSING"
        and row["admission_revalidation"]["reason"] == "unknown_handle"
        and row["pointer_admissions"] == []
        and row["terminal"]["status"] == "needs_decision"
        and row["independent_evaluation"]["success"] is False
        for row in predecessor_handle
    )
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["promotion_gate"]["passed"] is True
    expected = [
        (entry["mode"], entry["seed"]) for entry in plan["execution_order"]
    ]
    assert [(row["mode"], row["seed"]) for row in report["cases"]] == expected
    frame_counts = {}
    for row in report["cases"]:
        root = ROOT / row["name"]
        assert row == read(root / "result.json")
        assert row["model"]["strict_shape_correct"] is True
        assert row["terminal"]["status"] == "completed"
        assert row["terminal"]["release"]["verified"] is True
        assert row["independent_evaluation"]["success"] is True
        assert row["actual"] == {"value": [row["goal"]["token"]]}
        assert parse_qs((root / "runtime/submitted.txt").read_text()) == row["actual"]
        assert len(row["pointer_admissions"]) == 2
        assert row["bridge_exit_code"] == 0
        model_plan = read(root / "model/plan.json")
        assert model_plan["requested_model"] == "gpt-5.6-luna"
        assert model_plan["requested_effort"] == "low"
        assert model_plan["instructions_sha256"] == sha(
            HERE / "gui_action_responder_v1.txt"
        )
        assert model_plan["schema_sha256"] == sha(
            HERE / "target_action_envelope_schema_v1.json"
        )
        events, frames = replay(root)
        frame_counts[row["name"]] = frames
        assert len([event for event in events if event.get("event") == "terminal"]) >= 1
        if row["mode"] == "coordinate":
            assert row["coordinate_in_expected_box"] is True
            assert row["handle_query"] is None
            assert row["admission_revalidation"] is None
            assert model_plan["image_sha256"] is not None
        else:
            assert row["coordinate_in_expected_box"] is None
            assert row["handle_query"]["status"] == "REVALIDATED"
            assert row["admission_revalidation"]["status"] == "REVALIDATED"
            assert row["runtime_action"]["target_handle"] == "save_form"
            assert model_plan["image_sha256"] is None
            for record in (
                row["minted"], row["handle_query"], row["admission_revalidation"]
            ):
                assert record["handle"] == "save_form"
                assert record["private_registry_id_exposed"] is False
    coordinate = report["arm_stats"]["coordinate"]
    handle = report["arm_stats"]["handle"]
    audit = {
        "audit_passed": True,
        "retained_failures": {
            "v1": "Windows fcntl import failed before GUI/model",
            "v2": "coordinate 2/2 success; friendly-name handle 0/2 safe refusal",
        },
        "fresh_independent_success": "4/4",
        "reported_input_tokens": {
            "coordinate": coordinate["input_tokens"],
            "handle": handle["input_tokens"],
            "coordinate_mean": coordinate["input_mean"],
            "handle_mean": handle["input_mean"],
            "handle_minus_coordinate_mean":
                handle["input_mean"] - coordinate["input_mean"],
            "handle_reduction_percent":
                (coordinate["input_mean"] - handle["input_mean"])
                / coordinate["input_mean"] * 100,
        },
        "decision_to_evaluation_return_ms": {
            "coordinate": coordinate["decision_to_evaluation_return_ms"],
            "handle": handle["decision_to_evaluation_return_ms"],
            "coordinate_mean": coordinate["decision_to_evaluation_return_mean_ms"],
            "handle_mean": handle["decision_to_evaluation_return_mean_ms"],
            "handle_minus_coordinate_mean":
                handle["decision_to_evaluation_return_mean_ms"]
                - coordinate["decision_to_evaluation_return_mean_ms"],
        },
        "durable_calls": {
            "coordinate": coordinate["durable_calls"],
            "handle": handle["durable_calls"],
        },
        "exact_frames": frame_counts,
        "total_exact_frames": sum(frame_counts.values()),
        "promotion_gate": report["promotion_gate"],
        "scope": report["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
