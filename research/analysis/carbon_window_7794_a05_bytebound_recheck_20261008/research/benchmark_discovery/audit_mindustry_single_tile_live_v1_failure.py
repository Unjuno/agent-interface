"""Audit the retained zero-input candidate-contract failure."""
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from PIL import Image

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))
from audit_local_visual_barrier_v1 import Decoder, Frame
from uncertain_target_contract_v1 import validate as validate_uncertain

OUT = HERE / "results/mindustry-single-tile-live-01"
ROOT = OUT / "live-changed-geometry"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("live_control/") else HERE / name


def main():
    prereg = read(OUT / "preregistration.json"); failure = read(OUT / "failure.json")
    assert sha(HERE / prereg["reference_image"]) == prereg["reference_sha256"]
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    result = read(ROOT / "model-palette-candidate-result.json")
    schema = read(LIVE / "uncertain_target_contract_schema_v1.json")
    Draft202012Validator(schema).validate(result["typed"])
    rejected = None
    try: validate_uncertain(result["typed"], 1280, 800)
    except ValueError as error: rejected = str(error)
    assert rejected == "direct point must be among probe candidates"
    assert result["typed"]["point"] == {"x": 368, "y": 393}
    assert result["typed"]["points"][0] == {"x": 1004, "y": 578}
    raw = [json.loads(line) for line in (ROOT / "model-palette-candidate/events.jsonl").read_text().splitlines()]
    turn = [row for row in raw if row.get("type") == "turn.completed"]
    message = [row for row in raw if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    assert len(turn) == len(message) == 1 and turn[0]["usage"] == result["usage"]
    assert json.loads(message[0]["item"]["text"]) == result["typed"]
    assert failure["model_usage_ledger"] == [{"stage": "model-palette-candidate", "usage": result["usage"],
        "runner_ms": result["runner_ms"], "parent_elapsed_ms": result["parent_elapsed_ms"]}]
    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert len(observations) == 1 and not [row for row in events if row.get("event") == "pointer_admission"]
    decoder = Decoder("live-control"); frame = decoder.accept((ROOT / "runtime/001.ait").read_bytes())
    with Image.open(ROOT / "runtime/001.png") as opened:
        image = opened.convert("RGB")
    assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    cleanup = read(ROOT / "runtime/cleanup.json")
    assert cleanup == {"all_owned_processes_exited": True, "save_unchanged": True}
    audit = {"passed": True, "decision": "RETAIN_ZERO_INPUT_SCHEMA_VALIDATOR_MISMATCH",
        "schema_valid": True, "validator_refusal": rejected, "model_calls": 1,
        "input_tokens": result["usage"]["input_tokens"], "pointer_admissions": 0,
        "exact_frames": 1, "cleanup": cleanup}
    (OUT / "failure-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
