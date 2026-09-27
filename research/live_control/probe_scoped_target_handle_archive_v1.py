"""Replay handle geometry against two retained real OpenTTD observations."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from scoped_target_handle_v1 import TargetHandleStore


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results" / "scoped-target-handle-archive-01"
SOURCE_ROOT = HERE / "results" / "openttd-target-guard-live-03" / "target" / "runtime"
TARGET_ROOT = HERE / "results" / "openttd-target-guard-transform-04" / "target" / "runtime"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_observation(path):
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("event") == "observation" and event.get("image"):
            return event
    raise ValueError(f"no image observation in {path}")


def normalized(event, sequence, capture_ns):
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": event["pointer_binding"]}


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    source_events = SOURCE_ROOT / "events.jsonl"
    target_events = TARGET_ROOT / "events.jsonl"
    source_event = first_observation(source_events)
    target_event = first_observation(target_events)
    source_image_path = SOURCE_ROOT / Path(source_event["image"]).name
    target_image_path = TARGET_ROOT / Path(target_event["image"]).name
    with Image.open(source_image_path) as opened:
        source_image = opened.convert("RGB")
    with Image.open(target_image_path) as opened:
        target_image = opened.convert("RGB")
    # Separate archived runs cannot prove handle lifetime. Normalize only clocks and
    # sequence so this replay isolates retained pixels plus recorded geometries.
    source = normalized(source_event, 1, 1_000_000_000)
    target = normalized(target_event, 2, 1_001_000_000)
    ids = iter(("content-region", "wrong-frame-control"))
    store = TargetHandleStore("archive-pixel-feasibility", lambda: next(ids))
    common = dict(name="openttd_centered_toolbar_region", box=[624, 6, 16, 16],
                  observation=source, image=source_image, now_ns=1_000_000_100,
                  ttl_ms=1000, freshness_ms=100, search_radius=0)
    content = store.mint(coordinate_frame="window_content", **common)
    wrong_frame = store.mint(coordinate_frame="screen_chrome", **common)
    content_result = store.resolve_point(content["handle"], [8, 8], target,
                                         target_image, 1_001_000_100)
    wrong_frame_result = store.resolve_point(wrong_frame["handle"], [8, 8], target,
                                             target_image, 1_001_000_100)
    assert source["pointer_binding"]["geometry"] == [129, 40, 1024, 720]
    assert target["pointer_binding"]["geometry"] == [65, 40, 1152, 720]
    assert content_result["status"] == "REVALIDATED" and content_result["eligible"]
    assert content_result["binding_translation"] == [-64, 0]
    assert content_result["observed_box"] == [560, 6, 16, 16]
    assert content_result["point"] == [568, 14]
    assert wrong_frame_result["status"] == "MISSING" and not wrong_frame_result["eligible"]
    report = {
        "format": "scoped-target-handle-archive-replay-v1",
        "scope": "offline retained-pixel and geometry feasibility only; separate processes, normalized clocks/sequence, no valid cross-session handle and no GUI input",
        "source_geometry": source["pointer_binding"]["geometry"],
        "target_geometry": target["pointer_binding"]["geometry"],
        "region": [624, 6, 16, 16],
        "window_content": content_result,
        "screen_chrome_negative_control": wrong_frame_result,
        "sources": {str(path.relative_to(HERE.parent.parent)): sha(path) for path in
                    (Path(__file__), HERE / "scoped_target_handle_v1.py", source_events,
                     target_events, source_image_path, target_image_path)},
        "decision": "pixel/geometry feasibility passes; live same-session mint/revalidation/input remains required",
    }
    (ROOT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "content_status": content_result["status"],
                      "resolved_point": content_result["point"],
                      "wrong_frame_status": wrong_frame_result["status"],
                      "scope": report["scope"]}, indent=2))


if __name__ == "__main__":
    main()
