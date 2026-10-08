"""Independent structural, provenance, and classification audit for A01."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import io
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


def transformed_digest(source: Image.Image, variant: str, parameters: dict) -> str:
    image = source.copy()
    if variant == "baseline":
        pass
    elif variant.startswith("translate_"):
        image = Image.new("RGB", source.size, (0, 0, 0))
        image.paste(source, (parameters["dx"], parameters["dy"]))
    elif variant.startswith("brightness_"):
        image = ImageEnhance.Brightness(source).enhance(parameters["factor"])
    elif variant.startswith("contrast_"):
        image = ImageEnhance.Contrast(source).enhance(parameters["factor"])
    elif variant.startswith("jpeg_q"):
        encoded = io.BytesIO()
        source.save(encoded, format="JPEG", quality=parameters["quality"], subsampling=0, optimize=False)
        with Image.open(io.BytesIO(encoded.getvalue())) as reopened:
            image = reopened.convert("RGB")
    else:
        raise ValueError(f"unknown variant {variant}")
    return rgb_digest(image)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    errors = []
    result_path = PACKAGE / "results" / "a01.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    base = FREEZE["base_commit"]
    if sha((PACKAGE / "FREEZE.json").read_bytes()) != result.get("freeze_sha256"):
        errors.append("freeze hash")
    if sha((PACKAGE / "analyze.py").read_bytes()) != FREEZE["candidate_sha256"]:
        errors.append("candidate hash")
    if sha((PACKAGE / "audit.py").read_bytes()) != FREEZE["auditor_sha256"]:
        errors.append("auditor hash")
    if sha(args.wad.resolve().read_bytes()) != FREEZE["wad_sha256"]:
        errors.append("WAD hash")
    if result.get("base_commit") != base:
        errors.append("base commit")
    if result.get("source_blobs") != FREEZE["source_blobs"]:
        errors.append("source blob manifest")
    if result.get("runtime") is None or any(
            result["runtime"].get(key) != value
            for key, value in FREEZE["runtime_versions"].items()):
        errors.append("runtime versions")
    if result.get("status") != "PASS_NO_FALSE_OBSERVED_VALUE":
        errors.append("result status")

    a01_bytes = git_blob(repo, base, FREEZE["a01_freeze_path"])
    if sha(a01_bytes) != FREEZE["a01_freeze_sha256"]:
        errors.append("A01 freeze hash")
    a01 = json.loads(a01_bytes)
    for path, expected_blob in FREEZE["source_blobs"].items():
        actual_blob = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"], cwd=repo, text=True).strip()
        if actual_blob != expected_blob:
            errors.append(f"source blob {path}")
    expected = []
    transforms = ["baseline"]
    transforms += [f"translate_{dx:+d}_{dy:+d}" for dx, dy in FREEZE["translation_px"]]
    transforms += [f"brightness_{factor:.2f}" for factor in FREEZE["brightness_factors"]]
    transforms += [f"contrast_{factor:.2f}" for factor in FREEZE["contrast_factors"]]
    transforms += [f"jpeg_q{quality}" for quality in FREEZE["jpeg_qualities"]]
    expected_parameters = {"baseline": {}}
    expected_parameters.update({
        f"translate_{dx:+d}_{dy:+d}": {"dx": dx, "dy": dy}
        for dx, dy in FREEZE["translation_px"]
    })
    expected_parameters.update({
        f"brightness_{factor:.2f}": {"factor": factor}
        for factor in FREEZE["brightness_factors"]
    })
    expected_parameters.update({
        f"contrast_{factor:.2f}": {"factor": factor}
        for factor in FREEZE["contrast_factors"]
    })
    expected_parameters.update({
        f"jpeg_q{quality}": {"quality": quality}
        for quality in FREEZE["jpeg_qualities"]
    })
    source_images = {}
    for frame in a01["frames"]:
        frame_bytes = git_blob(repo, base, frame["frame_path"])
        if sha(frame_bytes) != frame["sha256"]:
            errors.append(f"frozen frame hash {frame['frame_path']}")
        with Image.open(io.BytesIO(frame_bytes)) as opened:
            source_images[frame["index"]] = opened.convert("RGB")
    for index, (frame, health) in enumerate(zip(a01["frames"], a01["manual_health"], strict=True)):
        for transform in transforms:
            expected.append((index, frame, health, transform))
    rows = result.get("rows")
    if type(rows) is not list or len(rows) != len(expected):
        errors.append("row count")
        rows = []
    seen = set()
    baseline = []
    perturbed = []
    false_observed = []
    for row in rows:
        key = (row.get("frame_index"), row.get("variant"))
        if key in seen:
            errors.append(f"duplicate row {key}")
        seen.add(key)
        if not (0 <= row.get("frame_index", -1) < len(a01["frames"])):
            errors.append(f"frame index {key}")
            continue
        frame = a01["frames"][row["frame_index"]]
        health = a01["manual_health"][row["frame_index"]]
        if row.get("source_path") != frame["frame_path"] or row.get("source_png_sha256") != frame["sha256"]:
            errors.append(f"frame provenance {key}")
        if row.get("sequence") != frame["sequence"] or row.get("capture_ns") != frame["capture_ns"] or row.get("pointer_binding") != frame["pointer_binding"]:
            errors.append(f"observation metadata {key}")
        if row.get("expected_health") != health:
            errors.append(f"manual oracle {key}")
        if row.get("parameters") != expected_parameters.get(row.get("variant")):
            errors.append(f"variant parameters {key}")
        elif row.get("transformed_rgb_sha256") != transformed_digest(
                source_images[row["frame_index"]], row["variant"], row["parameters"]):
            errors.append(f"transformed frame hash {key}")
        if type(row.get("transformed_rgb_sha256")) is not str or len(row["transformed_rgb_sha256"]) != 64:
            errors.append(f"transformed hash {key}")
        status, value = row.get("status"), row.get("value")
        if status == "observed":
            if type(value) is not int:
                errors.append(f"observed value type {key}")
            if row.get("variant") == "baseline":
                if value != health:
                    errors.append(f"baseline mismatch {key}")
            elif value != health:
                false_observed.append(key)
        elif status != "unknown" or value is not None:
            errors.append(f"invalid reader status/value {key}")
        if row.get("variant") == "baseline":
            baseline.append(row)
        else:
            perturbed.append(row)
    if seen != {(index, transform) for index in range(FREEZE["frame_count"]) for transform in transforms}:
        errors.append("variant coverage")

    counts = {}
    for row in perturbed:
        variant = row["variant"]
        counts[variant] = counts.get(variant, 0) + (row.get("status") == "unknown")
    if result.get("baseline_reads") != len(baseline) or len(baseline) != FREEZE["frame_count"]:
        errors.append("baseline count")
    if result.get("baseline_matches") != sum(row.get("status") == "observed" and row.get("value") == row.get("expected_health") for row in baseline):
        errors.append("baseline matches")
    if result.get("perturbed_reads") != len(perturbed):
        errors.append("perturbed count")
    if result.get("perturbed_unknown") != sum(row.get("status") == "unknown" for row in perturbed):
        errors.append("perturbed unknown count")
    if result.get("perturbed_observed_same") != sum(row.get("status") == "observed" and row.get("value") == row.get("expected_health") for row in perturbed):
        errors.append("same-value count")
    if result.get("perturbed_observed_wrong") != len(false_observed) or false_observed:
        errors.append("false observed value")
    if result.get("unknown_by_variant") != counts:
        errors.append("per-variant unknown counts")

    audit = {
        "schema": "v39-hud-reader-perturbation-audit-a01-v1",
        "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "recomputed": {
            "frames": len(a01["frames"]),
            "baseline_reads": len(baseline),
            "perturbed_reads": len(perturbed),
            "baseline_matches": sum(row.get("status") == "observed" and row.get("value") == row.get("expected_health") for row in baseline),
            "perturbed_unknown": sum(row.get("status") == "unknown" for row in perturbed),
            "perturbed_observed_wrong": len(false_observed),
            "variant_counts": counts,
        },
        "scope": "independent provenance and metric audit; does not reimplement WAD patch extraction or infer real capture-fault probabilities",
    }
    (PACKAGE / "results" / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
