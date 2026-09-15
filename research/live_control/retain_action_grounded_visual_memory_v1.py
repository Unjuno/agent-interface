"""Derive non-authoritative action-grounded crops from the frozen v2 live run."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from action_grounded_visual_memory_v1 import canonical, validate, verify_artifact


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results/adaptive-semantic-repair-live-02"
OUT = HERE / "results/action-grounded-visual-memory-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(value): return hashlib.sha256(value).hexdigest()


def observation(events, sequence):
    rows = [row for row in events if row.get("event") == "observation"
            and row.get("sequence") == sequence and row.get("exact") is True]
    if len(rows) != 1:
        raise ValueError(f"one exact observation required for sequence {sequence}")
    return rows[0]


def successful_effect(events, action_id):
    probes = [row for row in events if row.get("event") == "semantic_probe"
              and row.get("id") == action_id and row.get("score", {}).get("success") is True]
    if not probes:
        raise ValueError("successful semantic probe required")
    probe = min(probes, key=lambda row: row["sequence"])
    reconciled = [row for row in events if row.get("event") == "semantic_probe_reconciled"
                  and row.get("id") == action_id and row.get("sequence") == probe["sequence"]]
    if len(reconciled) != 1 or reconciled[0]["reconciliation"].get("matches") is not True:
        raise ValueError("one exact artifact reconciliation required")
    return probe, reconciled[0]


def build_case(row, case_name, destination, refresh=False):
    source_dir = SOURCE / case_name
    events = read(source_dir / "events.json")
    target = row["adaptive"]["selected_target"]
    source = observation(events, target["source_sequence"])
    source_path = source_dir / Path(source["image"]).name
    point = target["point"]
    box = [point[0] - 20, point[1] - 9, point[0] + 22, point[1] + 9]
    with Image.open(source_path) as opened:
        frame = opened.convert("RGB")
    crop = frame.crop(tuple(box))
    patch_sha = sha(crop.tobytes())
    if patch_sha != target["mint"]["patch_sha256"]:
        raise ValueError("selected target patch changed")
    destination.mkdir(parents=True, exist_ok=refresh)
    crop_path = destination / "target.png"
    crop.save(crop_path, compress_level=6)

    action = row["actions"][-1]
    if action["id"] != f"adaptive-submit-{row['ordinal'] + 1}-{row['mode']}":
        raise ValueError("final submit action required")
    probe, reconciliation = successful_effect(events, action["id"])
    effect_observation = observation(events, probe["sequence"])
    recovery = row["adaptive"]
    model_call_ids = [entry["call_id"] for entry in recovery["model_call_ledger"]]
    receipt = {
        "schema": "action-grounded-visual-memory-v1",
        "memory_id": f"adaptive-v2-{row['mode']}-submit-target",
        "task": {"task_id": "save-exact-token",
                 "environment_id": f"chromium-x11-seed-{row['seed']}"},
        "source": {"session_id": f"adaptive-v2-case-{row['ordinal'] + 1}",
                   "sequence": source["sequence"], "capture_ns": source["capture_ns"],
                   "exact": source["exact"],
                   "surface": source["pointer_binding"]["surface"],
                   "geometry": source["pointer_binding"]["geometry"],
                   "frame_size": [frame.width, frame.height],
                   "image_name": source_path.name,
                   "image_sha256": sha(source_path.read_bytes()),
                   "rgb_sha256": sha(frame.tobytes())},
        "target": {"name": target["mint"]["name"], "handle": target["handle"],
                   "point": point, "crop_box": box, "patch_sha256": patch_sha},
        "action": {"id": action["id"],
                   "program_sha256": action["accepted"]["program_sha256"],
                   "accepted_ns": action["accepted"]["accepted_ns"],
                   "terminal_ns": action["terminal"]["terminal_ns"],
                   "status": action["terminal"]["status"],
                   "release_verified": action["terminal"]["release"]["verified"],
                   "keys_down": action["terminal"]["release"]["keys_down"],
                   "buttons_down": action["terminal"]["release"]["buttons_down"]},
        "effect": {"predicate_id": probe["score"]["probe_id"],
                   "sequence": probe["sequence"], "capture_ns": probe["capture_ns"],
                   "success": probe["score"]["success"], "reason": probe["score"]["reason"],
                   "frame_sha256": reconciliation["reconciliation"]["scored_frame_sha256"],
                   "artifact_sha256": reconciliation["reconciliation"]["artifact_sha256"],
                   "reconciled_exact": reconciliation["reconciliation"]["matches"],
                   "independent_output_sha256": sha(canonical(row["actual"]))},
        "recovery": {"path": recovery["repair_path"], "route": recovery["route"],
                     "trace": recovery["repair_trace"], "model_call_ids": model_call_ids,
                     "attempted_model_calls": recovery["accounting"]["attempted_calls"],
                     "completed_model_calls": recovery["accounting"]["completed_calls"],
                     "model_wait_ns": recovery["accounting"]["model_wait_ns"]},
        "artifact": {"path": f"{row['mode']}/target.png", "width": crop.width,
                     "height": crop.height, "png_sha256": sha(crop_path.read_bytes()),
                     "rgb_sha256": patch_sha},
        "retention": {"class": "conditional_visual_reference",
                      "requires_current_observation": True,
                      "requires_fresh_input_admission": True},
        "authority": "none",
    }
    validate(receipt)
    verify_artifact(receipt, OUT)
    (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    return receipt


def main(refresh=False):
    if OUT.exists() and not refresh:
        raise FileExistsError(OUT)
    report = read(SOURCE / "report.json")
    cases = ["case-01-local", "case-02-model"]
    receipts = [build_case(row, case, OUT / row["mode"], refresh=refresh)
                for row, case in zip(report["results"], cases)]
    source_names = ["action_grounded_visual_memory_v1.py",
                    "retain_action_grounded_visual_memory_v1.py",
                    "test_action_grounded_visual_memory_v1.py",
                    "audit_action_grounded_visual_memory_v1.py"]
    manifest = {"schema": "action-grounded-visual-memory-retention-v1",
                "source_report_sha256": sha((SOURCE / "report.json").read_bytes()),
                "source_sha256": {name: sha((HERE / name).read_bytes()) for name in source_names},
                "receipts": [{"memory_id": row["memory_id"],
                              "path": f"{row['memory_id'].split('-')[2]}/receipt.json"}
                             for row in receipts],
                "scope": "retrospective derivation from one frozen run; no model call or performance comparison",
                "authority": "none"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps({"receipts": len(receipts), "authority": "none"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-derived", action="store_true",
                        help="overwrite only the known derived receipt/crop files")
    args = parser.parse_args()
    main(refresh=args.refresh_derived)
