"""Run the frozen V39 health-reader perturbation check over exact retained frames."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance


PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def rgb_digest(image: Image.Image) -> str:
    image = image.convert("RGB")
    width, height = image.size
    return sha(width.to_bytes(4, "big") + height.to_bytes(4, "big") + image.tobytes())


def variants(source: Image.Image):
    yield "baseline", {}, source.copy()
    for dx, dy in FREEZE["translation_px"]:
        shifted = Image.new("RGB", source.size, (0, 0, 0))
        shifted.paste(source, (dx, dy))
        yield f"translate_{dx:+d}_{dy:+d}", {"dx": dx, "dy": dy}, shifted
    for factor in FREEZE["brightness_factors"]:
        yield f"brightness_{factor:.2f}", {"factor": factor}, ImageEnhance.Brightness(source).enhance(factor)
    for factor in FREEZE["contrast_factors"]:
        yield f"contrast_{factor:.2f}", {"factor": factor}, ImageEnhance.Contrast(source).enhance(factor)
    for quality in FREEZE["jpeg_qualities"]:
        output = io.BytesIO()
        source.save(output, format="JPEG", quality=quality, subsampling=0, optimize=False)
        encoded = output.getvalue()
        with Image.open(io.BytesIO(encoded)) as reopened:
            yield f"jpeg_q{quality}", {"quality": quality, "jpeg_sha256": sha(encoded)}, reopened.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    if sha(Path(__file__).read_bytes()) != FREEZE["candidate_sha256"]:
        raise SystemExit("HOLD_CANDIDATE_HASH")
    if sha((PACKAGE / "audit.py").read_bytes()) != FREEZE["auditor_sha256"]:
        raise SystemExit("HOLD_AUDITOR_HASH")
    wad = args.wad.resolve().read_bytes()
    if sha(wad) != FREEZE["wad_sha256"]:
        raise SystemExit("HOLD_WAD_HASH")

    base = FREEZE["base_commit"]
    if subprocess.check_output(["git", "rev-parse", f"{base}^{{commit}}"], cwd=repo, text=True).strip() != base:
        raise SystemExit("HOLD_BASE_COMMIT")
    a01_freeze_bytes = git_blob(repo, base, FREEZE["a01_freeze_path"])
    if sha(a01_freeze_bytes) != FREEZE["a01_freeze_sha256"]:
        raise SystemExit("HOLD_A01_FREEZE_HASH")
    a01 = json.loads(a01_freeze_bytes)
    if a01["base_commit"] != FREEZE["reader_base_commit"]:
        raise SystemExit("HOLD_READER_BASE")
    for path, expected_blob in FREEZE["source_blobs"].items():
        actual_blob = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"], cwd=repo, text=True).strip()
        if actual_blob != expected_blob:
            raise SystemExit(f"HOLD_SOURCE_BLOB:{path}")

    with tempfile.TemporaryDirectory(prefix="v39-hud-perturb-") as temp:
        module_root = Path(temp)
        for path in FREEZE["reader_modules"]:
            target = module_root / Path(path).name
            target.write_bytes(git_blob(repo, base, path))
        sys.path.insert(0, str(module_root))
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

        rows = []
        expected_frames = a01["frames"]
        if len(expected_frames) != FREEZE["frame_count"]:
            raise SystemExit("HOLD_FRAME_COUNT")
        for frame_meta, expected_health in zip(expected_frames, a01["manual_health"], strict=True):
            frame_path = frame_meta["frame_path"]
            frame_png = git_blob(repo, base, frame_path)
            if sha(frame_png) != frame_meta["sha256"]:
                raise SystemExit(f"HOLD_FRAME_HASH:{frame_path}")
            with Image.open(io.BytesIO(frame_png)) as opened:
                original = opened.convert("RGB")
            observation = {
                "sequence": frame_meta["sequence"],
                "capture_ns": frame_meta["capture_ns"],
                "pointer_binding": frame_meta["pointer_binding"],
            }
            for variant_name, parameters, image in variants(original):
                outcome = reader.read_frame(observation, image)
                rows.append({
                    "frame_index": frame_meta["index"],
                    "source_path": frame_path,
                    "source_png_sha256": frame_meta["sha256"],
                    "sequence": frame_meta["sequence"],
                    "capture_ns": frame_meta["capture_ns"],
                    "pointer_binding": frame_meta["pointer_binding"],
                    "expected_health": expected_health,
                    "variant": variant_name,
                    "parameters": parameters,
                    "transformed_rgb_sha256": rgb_digest(image),
                    "status": outcome.get("status"),
                    "value": outcome.get("value"),
                    "reason": outcome.get("reason"),
                    "slots": outcome.get("slots"),
                })

    baseline = [row for row in rows if row["variant"] == "baseline"]
    perturbed = [row for row in rows if row["variant"] != "baseline"]
    baseline_matches = sum(row["status"] == "observed" and row["value"] == row["expected_health"] for row in baseline)
    false_observed = [row for row in perturbed if row["status"] == "observed" and row["value"] != row["expected_health"]]
    counts = {}
    for row in perturbed:
        counts[row["variant"]] = counts.get(row["variant"], 0) + (row["status"] == "unknown")
    status = "PASS_NO_FALSE_OBSERVED_VALUE" if baseline_matches == FREEZE["frame_count"] and not false_observed else "FAIL_FALSE_OBSERVED_VALUE"
    result = {
        "schema": "v39-hud-reader-perturbation-a01-v1",
        "execution_id": FREEZE["execution_id"],
        "status": status,
        "base_commit": base,
        "freeze_sha256": sha((PACKAGE / "FREEZE.json").read_bytes()),
        "candidate_sha256": sha(Path(__file__).read_bytes()),
        "auditor_sha256": sha((PACKAGE / "audit.py").read_bytes()),
        "wad_sha256": sha(wad),
        "source_blobs": FREEZE["source_blobs"],
        "frame_count": FREEZE["frame_count"],
        "baseline_reads": len(baseline),
        "baseline_matches": baseline_matches,
        "perturbed_reads": len(perturbed),
        "perturbed_unknown": sum(row["status"] == "unknown" for row in perturbed),
        "perturbed_observed_same": sum(row["status"] == "observed" and row["value"] == row["expected_health"] for row in perturbed),
        "perturbed_observed_wrong": len(false_observed),
        "unknown_by_variant": counts,
        "rows": rows,
        "runtime": {**runtime_versions, "platform": sys.platform, "game_or_gui_launched": False, "model_calls": 0, "os_input_emitted": False},
        "scope": FREEZE["scope"],
    }
    destination = PACKAGE / "results" / "a01.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("execution_id", "status", "baseline_matches", "perturbed_reads", "perturbed_unknown", "perturbed_observed_wrong", "unknown_by_variant")}, sort_keys=True))
    return 0 if status == "PASS_NO_FALSE_OBSERVED_VALUE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
