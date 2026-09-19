"""Derive two history-needed OpenTTD effect contexts from retained v9."""
import hashlib
import json
import shutil
from pathlib import Path

from openttd_drag_effect_v1 import build as build_crop


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results/timing-envelope-openttd-l-09/fixed-astra"
OUT = HERE / "results/openttd-action-effect-memory-inputs-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        existing = read(OUT / "manifest.json")
        if existing.get("schema") != "openttd-action-effect-memory-inputs-manifest-v1":
            raise FileExistsError(OUT)
    source_audit_path = HERE / "results/timing-envelope-openttd-l-09/audit.json"
    source_audit = read(source_audit_path)
    if not source_audit.get("audit_passed") or not source_audit.get("hard_success"):
        raise ValueError("source run is not independently verified")
    transitions = source_audit["observer"]
    OUT.mkdir(exist_ok=True); contexts = []
    for position, (name, action_turn, inspection_turn, current_sequence) in enumerate((
            ("segment-a-b", 5, 6, 36), ("segment-b-c", 7, 8, 44))):
        destination = OUT / name; destination.mkdir(exist_ok=True)
        crop = build_crop(SOURCE, action_turn, destination / "action-effect-crop.png")
        applied = read(SOURCE / f"applied-{action_turn}.json")
        before = SOURCE / crop["before_image"]
        after = SOURCE / crop["after_image"]
        inspection = read(SOURCE / f"applied-{inspection_turn}.json")
        current_records = [row for row in inspection["result"]["reply"]["records"]
                           if row.get("event") == "observation"]
        current_record = next(row for row in current_records if row["sequence"] == current_sequence)
        current = SOURCE / "runtime" / Path(current_record["image"]).name
        for label, source in (("before.png", before), ("after.png", after), ("current.png", current)):
            shutil.copyfile(source, destination / label)
        typed = read(SOURCE / f"typed-{action_turn}.json")
        drag = next(step for step in typed["steps"] if step.get("op") == "pointer_drag")
        receipt = {"schema": "openttd-action-effect-memory-input-v1", "context": name,
            "action_turn": action_turn, "inspection_turn": inspection_turn,
            "drag_points": drag["points"], "before_sequence": crop["before_sequence"],
            "after_sequence": crop["after_sequence"], "current_sequence": current_sequence,
            "crop_box": crop["crop_box"], "crop_changed_pixels": crop["crop_changed_pixels"],
            "full_frame_changed_pixels": crop["full_frame_changed_pixels"],
            "engine_transition_index": transitions["transition_indices"][position],
            "engine_transition_tiles": transitions["transition_tiles"][position],
            "artifacts": {label: {"sha256": sha(destination / label),
                                    "bytes": (destination / label).stat().st_size}
                          for label in ("before.png", "after.png", "current.png", "action-effect-crop.png")},
            "independent_ground_truth": "observed",
            "ground_truth_source": "timing-envelope-openttd-l-09 independent engine transition plus final scorer",
            "authority": "none; archived decision evidence only"}
        (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                   encoding="utf-8", newline="\n")
        contexts.append({"name": name, "receipt": f"{name}/receipt.json",
                         "receipt_sha256": sha(destination / "receipt.json")})
    manifest = {"schema": "openttd-action-effect-memory-inputs-manifest-v1",
        "source_plan_sha256": sha(SOURCE / "plan.json"),
        "source_audit_sha256": sha(source_audit_path),
        "contexts": contexts,
        "scope": "retrospective exact v9 frames; no new model call or game input"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps({"contexts": len(contexts)}, indent=2))


if __name__ == "__main__": main()
