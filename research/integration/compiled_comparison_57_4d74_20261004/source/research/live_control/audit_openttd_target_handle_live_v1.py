"""Audit the first preregistered same-session scoped target-handle run."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-target-handle-live-01"
TRIAL = ROOT / "live"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    assert read(ROOT / "driver-attempt-windows.json")["started_gui_episode"] is False
    report = read(ROOT / "report.json")
    result = read(TRIAL / "result.json")
    assert report["case"] == result and report["passed"] is False
    minted = result["minted"]
    moved = result["surface_move"]
    fresh = result["fresh_observation"]
    resolved = result["revalidation"]
    terminal = result["terminal"]
    assert minted["status"] == "VALID" and minted["authority"].startswith("observational")
    assert moved["before"]["geometry"] == [65, 40, 1152, 720]
    assert moved["after"]["geometry"] == [82, 60, 1152, 720]
    assert fresh["pointer_binding"]["geometry"] == moved["after"]["geometry"]
    assert resolved["status"] == "REVALIDATED" and resolved["eligible"] is True
    assert resolved["binding_translation"] == [17, 20]
    assert resolved["observed_box"] == [829, 63, 16, 16]
    assert resolved["point"] == [837, 71]
    assert result["click_program"] == [{"op": "pointer_click_target",
        "target_handle": minted["handle"], "offset": [8, 8], "button": 1,
        "duration_ms": 40}]
    admissions = result["pointer_admissions"]
    assert [(row["operation"], row["payload"]) for row in admissions] == [
        ("move", {"x": 837, "y": 71}), ("button_down", 1)]
    assert terminal["status"] == "completed" and terminal["release"]["verified"] is True
    assert result["bridge_exit_code"] == 0
    assert result["independent_evaluation"]["success"] is False
    assert result["independent_evaluation"]["changed_surrounding_tiles"] == []
    events = [json.loads(line) for line in
              (TRIAL / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((TRIAL / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(TRIAL / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    with Image.open(TRIAL / "runtime/003.png") as opened:
        before = opened.convert("RGB")
    with Image.open(TRIAL / "runtime/004.png") as opened:
        after = opened.convert("RGB")
    tooltip_box = (826, 82, 966, 107)
    difference = ImageChops.difference(before.crop(tooltip_box), after.crop(tooltip_box))
    tooltip_changed_pixels = sum(pixel != (0, 0, 0) for pixel in difference.getdata())
    assert tooltip_changed_pixels == 3383
    assert read(TRIAL / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    audit = {"audit_passed": True, "preregistered_primary_endpoint_passed": False,
        "mint_status": minted["status"], "revalidation_status": resolved["status"],
        "requested_surface_delta": [16, 0], "observed_binding_translation": [17, 20],
        "resolved_point": resolved["point"], "pointer_admissions": len(admissions),
        "terminal_status": terminal["status"], "release_verified": True,
        "tooltip_region_changed_pixels": tooltip_changed_pixels,
        "click_submit_to_return_ms": result["click_submit_to_return_ms"],
        "exact_frames": len(observations), "durable_calls": result["durable_calls"],
        "independent_task_success": False, "save_unchanged": True,
        "all_owned_processes_exited": True,
        "decision": "HOLD: runtime handle revalidated the observed WM translation and admitted the derived click, but the preregistered fixed geometry endpoint was false and no semantic task effect was independently verified",
        "next": "preregister a different application/task endpoint against observed binding deltas rather than requested window deltas, and require an independent semantic effect",
        "scope": report["scope"]}
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
