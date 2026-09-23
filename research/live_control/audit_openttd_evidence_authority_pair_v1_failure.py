"""Audit the retained generic-anchor-task failure before expanded selection."""
import hashlib
import json
from pathlib import Path
from PIL import Image

from anchor_evidence_contract_v1 import validate
from audit_local_visual_barrier_v1 import Decoder, Frame
from openttd_hover_receipt_batches_v1 import verify_batches

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-evidence-authority-pair-01"
ROOT = OUT / "positive"

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source(name): return HERE.parent / name if name.startswith("openttd_task/") else HERE / name

def main():
    prereg = read(OUT / "preregistration.json")
    for name, digest in prereg["sources"].items(): assert sha(source(name)) == digest, name
    assert "wrong anchor was accepted instead of expanded" in (OUT / "driver-stderr.txt").read_text()
    model = read(ROOT / "model-anchor-evidence-result.json")
    calls = read(ROOT / "calls.json"); anchor_call = calls[7]["result"]
    steps = anchor_call["request"]["command"]["steps"]
    point = [[steps[0]["x"], steps[0]["y"]]]
    readiness = verify_batches([{"records": anchor_call["reply"]["records"], "steps": steps, "points": point}], ROOT / "runtime")
    decision = validate(model["typed"], readiness)
    assert decision["status"] == "EVIDENCE_BOUND" and decision["point"] == [456, 79]
    result_plan = read(ROOT / "model-anchor-evidence/plan.json")
    assert result_plan["requested_model"] == "gpt-5.6-luna" and result_plan["requested_effort"] == "low"
    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((ROOT / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(ROOT / "runtime" / Path(observation["image"]).name) as opened: image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    buttons = [row for row in events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
    assert buttons == [] and read(ROOT / "runtime/cleanup.json") == {"all_owned_processes_exited": True, "save_unchanged": True}
    assert len(calls) == 8
    audit = {"passed": True, "formal_run_passed": False,
        "decision": "RETAIN_GENERIC_ANCHOR_TASK_FAILURE", "model_output": model["typed"],
        "model_input_tokens": model["usage"]["input_tokens"], "durable_calls": 8,
        "exact_frames": len(observations), "button_downs": 0,
        "cleanup": {"all_owned_processes_exited": True, "save_unchanged": True},
        "failure": "condition target noun absent from anchor prompt; wrong receipt accepted before expansion"}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__": main()
