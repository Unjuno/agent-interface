"""Retained v39 audit v2: account for exact unchanged-image reuse in AIT."""
import hashlib
import json
from pathlib import Path

from PIL import Image
from audit_map01_v39_coast_liveness_live_v1 import PLAN, read, result


ROOT = Path(__file__).resolve().parent / "results/map01-v39-coast-liveness-live-01"


def exact_observation_artifacts(root):
    runtime = root / "runtime"
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text(
        encoding="utf-8").splitlines()]
    rows = [row for row in events if row.get("event") == "observation"]
    png = {path.name for path in runtime.glob("[0-9][0-9][0-9].png")}
    ait = {path.name for path in runtime.glob("[0-9][0-9][0-9].ait")}
    assert len(rows) == len({row["sequence"] for row in rows})
    assert ait == {f'{row["sequence"]:03}.ait' for row in rows}
    filenames = {Path(row["image"]).name for row in rows}
    assert filenames == png
    cached = {}
    prior = None
    reused = 0
    for row in rows:
        name = Path(row["image"]).name
        path = runtime / name
        assert path.is_file() and path.suffix == ".png"
        if name not in cached:
            with Image.open(path) as frame:
                cached[name] = hashlib.sha256(frame.convert("RGB").tobytes()).hexdigest()
        assert cached[name] == row["frame_rgb_sha256"]
        if row["image_reused"]:
            reused += 1
            assert prior is not None and name == Path(prior["image"]).name
            assert row["frame_rgb_sha256"] == prior["frame_rgb_sha256"]
        else:
            assert name == f'{row["sequence"]:03}.png'
        prior = row
    return {"observations": len(rows), "png": len(png), "ait": len(ait),
            "unchanged_image_reuse": reused}


def main():
    plan = read(PLAN)
    original = read(ROOT / "audit.json")
    assert original == result(plan, ROOT)
    assert original["formal_pass"] is False
    assert original["checks"]["exact_frames"] is False
    assert all(value is True for key, value in original["checks"].items()
               if key != "exact_frames")
    artifact = exact_observation_artifacts(ROOT)
    assert artifact == {"observations": 218, "png": 217, "ait": 218,
                        "unchanged_image_reuse": 1}
    corrected = dict(original)
    corrected["schema"] = "map01-v39-coast-liveness-retained-audit-v2"
    corrected["original_audit_formal_pass"] = False
    corrected["original_audit_failure"] = "exact_frames counted one allowed unchanged PNG reuse as missing"
    corrected["exact_observation_artifacts"] = artifact
    corrected["checks"] = dict(original["checks"])
    corrected["checks"]["exact_frames"] = True
    corrected["formal_pass"] = all(corrected["checks"].values())
    assert corrected["formal_pass"] is True
    corrected["decision"] = "COAST_LIVENESS_AND_RUNNING_RELEASE_EXPOSED_RETAIN_LIMITED"
    (ROOT / "audit-v2.json").write_text(json.dumps(corrected, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps({"formal_pass": corrected["formal_pass"],
                      "original_audit_formal_pass": False,
                      "coast_completed_after_damage": corrected["coast_completed_after_damage"],
                      "dynamic_revocation_exposed": corrected["dynamic_revocation_exposed"],
                      "artifacts": artifact}, indent=2))


if __name__ == "__main__":
    main()
