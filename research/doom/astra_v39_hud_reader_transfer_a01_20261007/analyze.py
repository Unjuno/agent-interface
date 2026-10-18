"""Apply the frozen current-main V39 health reader to retained Astra frames."""
import argparse
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile


PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_bytes(root, relative):
    return (root / relative).read_bytes()


def load_json(root, relative):
    return json.loads(file_bytes(root, relative))


def source_health_labels(source):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "HEALTH"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("HEALTH transcription assignment missing")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.repo_root.resolve()
    git_root = args.git_root.resolve()

    for relative, expected in FREEZE["source_blobs"].items():
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{FREEZE['base_commit']}:{relative}"],
            cwd=git_root, text=True).strip()
        if actual != expected:
            raise SystemExit(f"FAIL_SOURCE_BLOB:{relative}")
    for relative, expected in FREEZE["input_sha256"].items():
        actual = sha(file_bytes(root, relative))
        if actual != expected:
            raise SystemExit(f"FAIL_INPUT_HASH:{relative}")
    if sha(args.wad.read_bytes()) != FREEZE["wad_sha256"]:
        raise SystemExit("FAIL_WAD_HASH")

    sys.path.insert(0, str(root / "research" / "doom"))
    module = importlib.import_module("doom_hud_signal_v3")
    reader = module.DoomStatusNumberReader(args.wad, signal_id="health")
    import PIL
    import numpy
    runtime_versions = {
        "python": sys.version.split()[0],
        "pillow": PIL.__version__,
        "numpy": numpy.__version__,
    }
    if runtime_versions != FREEZE["runtime_versions"]:
        raise SystemExit(f"HOLD_RUNTIME_VERSION:{runtime_versions}")

    data_root = Path("research/doom/results/map01-astra-attempt-v1")
    events = [json.loads(line) for line in
              (root / data_root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    report = load_json(root, str(data_root / "report.json"))
    frame_manifest = load_json(root, str(data_root / "frame-manifest.json"))
    exact_manifest = load_json(root, str(data_root / "local-exact-frame-manifest.json"))["frames"]
    exact_by_name = {row["file"]: row for row in exact_manifest}
    frame_by_index = {int(row["file"].split("/")[-1][:2]): row for row in frame_manifest}
    manual_health = source_health_labels(file_bytes(
        root, "research/doom/analyze_map01_astra_failure_v1.py").decode("utf-8"))

    if len(report["decisions"]) != FREEZE["expected_frames"]:
        raise SystemExit("FAIL_DECISION_COUNT")
    if len(manual_health) != FREEZE["expected_frames"]:
        raise SystemExit("FAIL_LABEL_COUNT")

    rows = []
    unknown_controls = 0
    with tempfile.TemporaryDirectory(prefix="astra-v39-reader-") as temp:
        temp_root = Path(temp)
        for index, decision in enumerate(report["decisions"]):
            source_name = decision["source_image"].rsplit("/", 1)[-1]
            frozen_frame = FREEZE["frames"][index]
            if source_name != frozen_frame["source_file"]:
                raise SystemExit(f"FAIL_FROZEN_SOURCE_IMAGE:{index}")
            original = next((row for row in events
                             if row.get("event") == "observation" and
                             row.get("image", "").endswith("/" + source_name)), None)
            if original is None:
                raise SystemExit(f"FAIL_SOURCE_OBSERVATION:{index}")
            frame_record = frame_by_index.get(index)
            exact_record = exact_by_name.get(source_name)
            frame_relative = str(data_root / f"frames/{index:02}.png")
            frame_path = root / frame_relative
            frame_data = frame_path.read_bytes()
            digest = sha(frame_data)
            if (frame_record is None or exact_record is None or
                    frame_record["sha256"] != digest or
                    exact_record["sha256"] != digest or
                    frame_record["sha256"] != exact_record["sha256"]):
                raise SystemExit(f"FAIL_FRAME_JOIN:{index}")
            if original.get("sequence") is None or original.get("capture_ns") is None:
                raise SystemExit(f"FAIL_CAPTURE_METADATA:{index}")
            if (original["sequence"] != frozen_frame["sequence"] or
                    original["capture_ns"] != frozen_frame["capture_ns"] or
                    original["pointer_binding"] != frozen_frame["pointer_binding"]):
                raise SystemExit(f"FAIL_FROZEN_OBSERVATION_METADATA:{index}")
            image = temp_root / f"{index:02}.png"
            image.write_bytes(frame_data)
            observation = {
                "sequence": original["sequence"],
                "capture_ns": original["capture_ns"],
                "pointer_binding": original["pointer_binding"],
                "image": str(image),
            }
            value = reader.read(observation)
            expected = manual_health[index]

            # Negative control: blank only the exact frozen health-number ROI.
            from PIL import Image, ImageDraw
            with Image.open(image) as opened:
                blank = opened.convert("RGB")
            geometry = original["pointer_binding"]["geometry"]
            anchor = FREEZE["health_roi"]["local_anchor"]
            width, height = FREEZE["health_roi"]["glyph_size"]
            left, top = geometry[0] + anchor[0], geometry[1] + anchor[1]
            draw = ImageDraw.Draw(blank)
            draw.rectangle((left, top,
                            left + width * FREEZE["health_roi"]["slots"] - 1,
                            top + height - 1), fill=(0, 0, 0))
            blank_path = temp_root / f"{index:02}-blank.png"
            blank.save(blank_path, format="PNG")
            blank_observation = dict(observation, image=str(blank_path))
            negative = reader.read(blank_observation)
            if negative.get("status") == "unknown":
                unknown_controls += 1

            rows.append({
                "index": index,
                "source_file": source_name,
                "frame_sha256": digest,
                "sequence": original["sequence"],
                "capture_ns": original["capture_ns"],
                "pointer_binding": original["pointer_binding"],
                "expected_manual_health": expected,
                "reader_status": value.get("status"),
                "reader_value": value.get("value"),
                "reader_slots": value.get("slots"),
                "blank_roi_status": negative.get("status"),
                "blank_roi_reason": negative.get("reason"),
            })

    exact_values = all(row["reader_status"] == "observed" and
                       row["reader_value"] == row["expected_manual_health"]
                       for row in rows)
    all_unknown = unknown_controls == FREEZE["expected_frames"]
    status = "PASS_CROSS_RUN_HEALTH_READER" if exact_values and all_unknown else (
        "HOLD_OR_FAIL_CROSS_RUN_READER")
    result = {
        "schema": "astra-v39-hud-reader-transfer-a01-v1",
        "execution_id": FREEZE["execution_id"],
        "status": status,
        "base_commit": FREEZE["base_commit"],
        "freeze_sha256": sha((PACKAGE / "FREEZE.json").read_bytes()),
        "input_sha256": FREEZE["input_sha256"],
        "wad_sha256": FREEZE["wad_sha256"],
        "frame_count": len(rows),
        "observed_matching_values": sum(
            row["reader_status"] == "observed" and
            row["reader_value"] == row["expected_manual_health"] for row in rows),
        "blank_roi_unknown": unknown_controls,
        "blank_roi_total": len(rows),
        "rows": rows,
        "runtime": {
            **runtime_versions,
            "platform": sys.platform,
            "external_services": 0,
            "game_or_gui_launched": False,
            "model_calls": 0,
            "os_input_emitted": False,
        },
        "scope": FREEZE["scope"],
    }
    destination = PACKAGE / "results" / "a01.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "execution_id", "status", "frame_count", "observed_matching_values",
        "blank_roi_unknown", "blank_roi_total")}, sort_keys=True))
    if status != "PASS_CROSS_RUN_HEALTH_READER":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
