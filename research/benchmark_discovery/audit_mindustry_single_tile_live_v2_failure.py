"""Audit the retained unsupported-oneOf zero-input failure."""
import hashlib
import json
from pathlib import Path

from PIL import Image
import sys

HERE = Path(__file__).resolve().parent; LIVE = HERE.parent / "live_control"; sys.path.insert(0, str(LIVE))
from audit_local_visual_barrier_v1 import Decoder, Frame

OUT = HERE / "results/mindustry-single-tile-live-02"; ROOT = OUT / "live-changed-geometry"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("live_control/") else HERE / name


def main():
    prereg = read(OUT / "preregistration.json"); failure = read(OUT / "failure.json")
    assert sha(HERE / prereg["reference_image"]) == prereg["reference_sha256"]
    assert sha(HERE / prereg["prior_failure"]) == prereg["prior_failure_sha256"]
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    process = read(ROOT / "model-palette-candidate/process.json")
    raw = [json.loads(line) for line in (ROOT / "model-palette-candidate/events.jsonl").read_text().splitlines()]
    errors = [row for row in raw if row.get("type") in ("error", "turn.failed")]
    assert process["exit_code"] == 1 and len(errors) == 2
    assert all("'oneOf' is not permitted" in json.dumps(row) for row in errors)
    assert failure["model_usage_ledger"] == [] and not [row for row in raw if row.get("type") == "turn.completed"]
    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert len(observations) == 1 and not [row for row in events if row.get("event") == "pointer_admission"]
    frame = Decoder("live-control").accept((ROOT / "runtime/001.ait").read_bytes())
    with Image.open(ROOT / "runtime/001.png") as opened: image = opened.convert("RGB")
    assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    cleanup = read(ROOT / "runtime/cleanup.json"); assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
    audit = {"passed": True, "decision": "RETAIN_UNSUPPORTED_ONEOF_ZERO_INPUT_FAILURE",
        "api_error": "invalid_json_schema: oneOf is not permitted", "completed_model_calls": 0,
        "reported_usage": None, "pointer_admissions": 0, "exact_frames": 1, "cleanup": cleanup}
    (OUT / "failure-audit.json").write_text(json.dumps(audit, indent=2) + "\n"); print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
