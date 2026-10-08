"""Reconstruct the freshness boundary behind matched semantic repair v2."""
import json
from pathlib import Path
from PIL import Image

try:
    from .scoped_target_handle_v1 import TargetHandleStore
except ImportError:
    from scoped_target_handle_v1 import TargetHandleStore


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/matched-semantic-repair-live-02"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    arm = ROOT / "arm-02-model"
    report = read(arm / "report.json")
    observations = [row for row in read(arm / "events.json")
                    if row.get("event") == "observation"]
    resized = next(row for row in observations if row["id"] == "matched-repair-resized")
    outcome = report["reacquisition_outcome"]
    point = outcome["result"]["grounding"]["submit_point"]
    box = [point[0]-20, point[1]-9, 42, 18]
    image_path = arm / Path(resized["image"]).name
    with Image.open(image_path) as opened:
        image = opened.convert("RGB")
    delayed_ns = resized["capture_ns"] + round(outcome["caller_elapsed_ms"]*1_000_000)
    delayed = TargetHandleStore("delayed", lambda: "delayed-save")
    delayed_mint = delayed.mint("save_form", "window_content", box, resized, image,
        delayed_ns, ttl_ms=60000, freshness_ms=3000, search_radius=0,
        allowed_transformations=("window_translation",))
    delayed_resolution = delayed.resolve_point(delayed_mint["handle"], [20, 9], resized,
                                                image, delayed_ns)
    fresh_ns = resized["capture_ns"] + 1_000_000
    fresh = TargetHandleStore("fresh", lambda: "fresh-save")
    fresh_mint = fresh.mint("save_form", "window_content", box, resized, image,
        fresh_ns, ttl_ms=60000, freshness_ms=3000, search_radius=0,
        allowed_transformations=("window_translation",))
    fresh_resolution = fresh.resolve_point(fresh_mint["handle"], [20, 9], resized,
                                            image, fresh_ns)
    checks = {"same_model_point": point == [270, 243],
        "wait_exceeds_freshness": outcome["caller_elapsed_ms"] > 3000,
        "delayed_refuses_stale": delayed_resolution["eligible"] is False
            and delayed_resolution["status"] == "STALE"
            and delayed_resolution["reason"] == "expired_or_nonfresh_observation",
        "same_pixels_resolve_when_fresh": fresh_resolution["eligible"] is True
            and fresh_resolution["point"] == point,
        "same_patch": delayed_mint["patch_sha256"] == fresh_mint["patch_sha256"]}
    result = {"schema": "matched-semantic-repair-v2-diagnosis-v1",
        "passed": all(checks.values()), "checks": checks, "model_point": point,
        "model_caller_elapsed_ms": outcome["caller_elapsed_ms"],
        "freshness_ms": 3000, "delayed_resolution": delayed_resolution,
        "fresh_control_resolution": fresh_resolution,
        "failure_class": "model_reacquisition_outlived_source_observation_freshness",
        "repair_boundary": "After a completed reacquisition, take one passive current exact observation and revalidate the model-derived patch on that observation before deriving a contract or admitting input.",
        "scope": "Posthoc deterministic replay on the retained arm-2 resized PNG and binding. It explains the frozen rejection; it is not a live repair or comparison result."}
    (ROOT / "diagnosis.json").write_text(json.dumps(result, indent=2)+"\n",
                                          encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
