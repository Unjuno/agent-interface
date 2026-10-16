"""Audit retained action-grounded crops against frozen live evidence."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from action_grounded_visual_memory_v1 import canonical, retrieve, validate, verify_artifact


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results/adaptive-semantic-repair-live-02"
OUT = HERE / "results/action-grounded-visual-memory-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(value): return hashlib.sha256(value).hexdigest()


def main():
    manifest = read(OUT / "manifest.json")
    assert manifest["schema"] == "action-grounded-visual-memory-retention-v1"
    assert manifest["source_report_sha256"] == sha((SOURCE / "report.json").read_bytes())
    for name, digest in manifest["source_sha256"].items():
        assert sha((HERE / name).read_bytes()) == digest
    report = read(SOURCE / "report.json")
    assert len(manifest["receipts"]) == len(report["results"]) == 2
    receipts = []
    for entry, row in zip(manifest["receipts"], report["results"]):
        receipt = validate(read(OUT / entry["path"]))
        receipts.append(receipt)
        assert receipt["memory_id"] == entry["memory_id"]
        assert verify_artifact(receipt, OUT)["authority"] == "none"
        selected = row["adaptive"]["selected_target"]
        action = row["actions"][-1]
        assert receipt["source"]["sequence"] == selected["source_sequence"]
        assert receipt["target"]["patch_sha256"] == selected["mint"]["patch_sha256"]
        assert receipt["target"]["point"] == selected["point"]
        assert receipt["action"]["id"] == action["id"]
        assert receipt["action"]["program_sha256"] == action["accepted"]["program_sha256"]
        assert receipt["action"]["release_verified"] is True
        assert receipt["effect"]["independent_output_sha256"] == sha(canonical(row["actual"]))
        assert receipt["recovery"]["path"] == row["adaptive"]["repair_path"]
        assert receipt["recovery"]["trace"] == row["adaptive"]["repair_trace"]
        source_dir = SOURCE / f"case-{row['ordinal'] + 1:02d}-{row['mode']}"
        events = read(source_dir / "events.json")
        source_rows = [event for event in events if event.get("event") == "observation"
                       and event.get("sequence") == receipt["source"]["sequence"]
                       and event.get("exact") is True]
        assert len(source_rows) == 1
        assert source_rows[0]["capture_ns"] == receipt["source"]["capture_ns"]
        probes = [event for event in events if event.get("event") == "semantic_probe"
                  and event.get("id") == receipt["action"]["id"]
                  and event.get("sequence") == receipt["effect"]["sequence"]]
        reconciled = [event for event in events
                      if event.get("event") == "semantic_probe_reconciled"
                      and event.get("id") == receipt["action"]["id"]
                      and event.get("sequence") == receipt["effect"]["sequence"]]
        assert len(probes) == len(reconciled) == 1
        assert probes[0]["capture_ns"] == receipt["effect"]["capture_ns"]
        assert probes[0]["score"]["success"] is True
        assert probes[0]["score"]["reason"] == receipt["effect"]["reason"]
        assert reconciled[0]["reconciliation"]["matches"] is True
        assert (reconciled[0]["reconciliation"]["scored_frame_sha256"]
                == receipt["effect"]["frame_sha256"])
        assert (reconciled[0]["reconciliation"]["artifact_sha256"]
                == receipt["effect"]["artifact_sha256"])
        source_path = source_dir / receipt["source"]["image_name"]
        assert receipt["source"]["image_sha256"] == sha(source_path.read_bytes())
        with Image.open(source_path) as opened:
            frame = opened.convert("RGB")
        assert receipt["source"]["rgb_sha256"] == sha(frame.tobytes())
        assert receipt["source"]["frame_size"] == [frame.width, frame.height]
        assert receipt["target"]["patch_sha256"] == sha(
            frame.crop(tuple(receipt["target"]["crop_box"])).tobytes())
        context = {"task_id": receipt["task"]["task_id"],
                   "environment_id": receipt["task"]["environment_id"],
                   "session_id": receipt["source"]["session_id"],
                   "surface": receipt["source"]["surface"],
                   "target_name": receipt["target"]["name"],
                   "current_observation_exact": True}
        eligible = retrieve(receipt, context)
        assert eligible["status"] == "ELIGIBLE_VISUAL_REFERENCE"
        assert eligible["current_target_status"] == "must_be_revalidated"
        assert eligible["input_admission"] == "must_be_fresh"
        context["surface"] += 1
        assert retrieve(receipt, context)["status"] == "NOT_ELIGIBLE"
    local, model = receipts
    assert local["recovery"]["path"] == "local"
    assert local["recovery"]["attempted_model_calls"] == 0
    assert model["recovery"]["path"] == "model_reacquisition"
    assert model["recovery"]["attempted_model_calls"] == 1
    assert local["target"]["patch_sha256"] != model["target"]["patch_sha256"]
    print(json.dumps({"passed": True, "receipts": 2,
                      "decision": "RETAIN_PROVENANCE_CONTRACT_NO_COMPARISON",
                      "authority": "none"}, indent=2))


if __name__ == "__main__": main()
