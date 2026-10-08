"""Audit exact provenance of derived OpenTTD action-effect memory inputs."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from openttd_drag_effect_v1 import build as build_crop


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results/timing-envelope-openttd-l-09/fixed-astra"
OUT = HERE / "results/openttd-action-effect-memory-inputs-01"
AUDIT = HERE / "results/timing-envelope-openttd-l-09/audit.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = read(OUT / "manifest.json")
    source_audit = read(AUDIT)
    assert manifest["source_plan_sha256"] == sha(SOURCE / "plan.json")
    assert manifest["source_audit_sha256"] == sha(AUDIT)
    assert source_audit["audit_passed"] is True and source_audit["hard_success"] is True
    assert source_audit["semantic_outcome"] == "verified_success"
    expected = {"segment-a-b": (5, 6, 36, 90, [977, 978, 979]),
                "segment-b-c": (7, 8, 44, 131, [1043, 1107])}
    for entry in manifest["contexts"]:
        name = entry["name"]
        action_turn, inspection_turn, current_sequence, transition_index, transition_tiles = expected[name]
        root = OUT / name; receipt = read(root / "receipt.json")
        assert entry["receipt_sha256"] == sha(root / "receipt.json")
        assert (receipt["action_turn"], receipt["inspection_turn"], receipt["current_sequence"]) == (
            action_turn, inspection_turn, current_sequence)
        assert receipt["independent_ground_truth"] == "observed" and receipt["authority"].startswith("none")
        assert receipt["engine_transition_index"] == transition_index
        assert receipt["engine_transition_tiles"] == transition_tiles
        assert transition_index in source_audit["observer"]["transition_indices"]
        assert transition_tiles in source_audit["observer"]["transition_tiles"]
        typed = read(SOURCE / f"typed-{action_turn}.json")
        drag = next(step for step in typed["steps"] if step.get("op") == "pointer_drag")
        assert receipt["drag_points"] == drag["points"]
        inspection = read(SOURCE / f"applied-{inspection_turn}.json")
        record = next(row for row in inspection["result"]["reply"]["records"]
                      if row.get("event") == "observation" and row.get("sequence") == current_sequence)
        assert sha(root / "current.png") == sha(SOURCE / "runtime" / Path(record["image"]).name)
        for label, artifact in receipt["artifacts"].items():
            assert artifact == {"sha256": sha(root / label), "bytes": (root / label).stat().st_size}
        temporary = root / ".audit-crop.png"
        regenerated = build_crop(SOURCE, action_turn, temporary)
        try:
            assert sha(temporary) == sha(root / "action-effect-crop.png")
            assert regenerated["before_sequence"] == receipt["before_sequence"]
            assert regenerated["after_sequence"] == receipt["after_sequence"]
            assert regenerated["crop_box"] == receipt["crop_box"]
            assert regenerated["crop_changed_pixels"] == receipt["crop_changed_pixels"]
        finally:
            temporary.unlink(missing_ok=True)
        with Image.open(root / "current.png") as image: assert image.size == (1280, 800)
    print(json.dumps({"passed": True, "contexts": len(expected),
                      "source_hard_success": True}, indent=2))


if __name__ == "__main__": main()
