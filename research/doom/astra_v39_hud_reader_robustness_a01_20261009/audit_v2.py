"""Posthoc corrected audit of the retained A01 result; does not rerun the reader."""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageEnhance


PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((PACKAGE / "results" / "a01.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def rgb_digest(image: Image.Image) -> str:
    image = image.convert("RGB")
    width, height = image.size
    return sha(width.to_bytes(4, "big") + height.to_bytes(4, "big") + image.tobytes())


def render(source: Image.Image, variant: str, parameters: dict) -> tuple[dict, str]:
    image = source.copy()
    expected_parameters = {}
    if variant == "baseline":
        pass
    elif variant.startswith("translate_"):
        expected_parameters = {"dx": parameters["dx"], "dy": parameters["dy"]}
        image = Image.new("RGB", source.size, (0, 0, 0))
        image.paste(source, (expected_parameters["dx"], expected_parameters["dy"]))
    elif variant.startswith("brightness_"):
        expected_parameters = {"factor": parameters["factor"]}
        image = ImageEnhance.Brightness(source).enhance(expected_parameters["factor"])
    elif variant.startswith("contrast_"):
        expected_parameters = {"factor": parameters["factor"]}
        image = ImageEnhance.Contrast(source).enhance(expected_parameters["factor"])
    elif variant.startswith("jpeg_q"):
        quality = parameters["quality"]
        encoded = io.BytesIO()
        source.save(encoded, format="JPEG", quality=quality, subsampling=0, optimize=False)
        encoded_bytes = encoded.getvalue()
        expected_parameters = {"quality": quality, "jpeg_sha256": sha(encoded_bytes)}
        with Image.open(io.BytesIO(encoded_bytes)) as reopened:
            image = reopened.convert("RGB")
    else:
        raise ValueError(f"unexpected transform {variant}")
    return expected_parameters, rgb_digest(image)


def audit_result(result: dict, repo: Path, wad_sha: str, a01: dict, source_images: dict) -> list[str]:
    errors = []
    base = FREEZE["base_commit"]
    if result.get("schema") != "v39-hud-reader-perturbation-a01-v1":
        errors.append("result schema")
    if result.get("execution_id") != FREEZE["execution_id"]:
        errors.append("execution id")
    if result.get("base_commit") != base:
        errors.append("base commit")
    if result.get("freeze_sha256") != sha((PACKAGE / "FREEZE.json").read_bytes()):
        errors.append("freeze hash")
    if result.get("candidate_sha256") != FREEZE["candidate_sha256"] or sha((PACKAGE / "analyze.py").read_bytes()) != FREEZE["candidate_sha256"]:
        errors.append("candidate hash")
    if result.get("auditor_sha256") != FREEZE["auditor_sha256"] or sha((PACKAGE / "audit.py").read_bytes()) != FREEZE["auditor_sha256"]:
        errors.append("frozen initial auditor hash")
    if result.get("wad_sha256") != FREEZE["wad_sha256"] or wad_sha != FREEZE["wad_sha256"]:
        errors.append("WAD identity")
    if result.get("source_blobs") != FREEZE["source_blobs"]:
        errors.append("source blob manifest")
    if result.get("runtime") is None or any(result["runtime"].get(key) != value for key, value in FREEZE["runtime_versions"].items()):
        errors.append("runtime versions")
    for path, expected_blob in FREEZE["source_blobs"].items():
        actual_blob = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"], cwd=repo, text=True).strip()
        if actual_blob != expected_blob:
            errors.append(f"source blob {path}")

    variants = ["baseline"]
    variants += [f"translate_{dx:+d}_{dy:+d}" for dx, dy in FREEZE["translation_px"]]
    variants += [f"brightness_{factor:.2f}" for factor in FREEZE["brightness_factors"]]
    variants += [f"contrast_{factor:.2f}" for factor in FREEZE["contrast_factors"]]
    variants += [f"jpeg_q{quality}" for quality in FREEZE["jpeg_qualities"]]
    expected_rows = {(index, variant) for index in range(FREEZE["frame_count"]) for variant in variants}
    rows = result.get("rows")
    if type(rows) is not list or len(rows) != FREEZE["expected_reads"]:
        errors.append("row count")
        rows = []
    seen = set()
    baseline = []
    perturbed = []
    wrong = []
    parameters_by_variant = {"baseline": {}}
    parameters_by_variant.update({f"translate_{dx:+d}_{dy:+d}": {"dx": dx, "dy": dy} for dx, dy in FREEZE["translation_px"]})
    parameters_by_variant.update({f"brightness_{factor:.2f}": {"factor": factor} for factor in FREEZE["brightness_factors"]})
    parameters_by_variant.update({f"contrast_{factor:.2f}": {"factor": factor} for factor in FREEZE["contrast_factors"]})
    parameters_by_variant.update({f"jpeg_q{quality}": {"quality": quality} for quality in FREEZE["jpeg_qualities"]})

    for row in rows:
        index, variant = row.get("frame_index"), row.get("variant")
        key = (index, variant)
        if key in seen:
            errors.append(f"duplicate row {key}")
        seen.add(key)
        if key not in expected_rows:
            errors.append(f"unexpected row {key}")
            continue
        frame, health = a01["frames"][index], a01["manual_health"][index]
        if row.get("source_path") != frame["frame_path"] or row.get("source_png_sha256") != frame["sha256"]:
            errors.append(f"source frame {key}")
        if row.get("sequence") != frame["sequence"] or row.get("capture_ns") != frame["capture_ns"] or row.get("pointer_binding") != frame["pointer_binding"]:
            errors.append(f"capture metadata {key}")
        if row.get("expected_health") != health:
            errors.append(f"frozen label {key}")
        expected_parameters, expected_rgb_sha = render(source_images[index], variant, parameters_by_variant[variant])
        if row.get("parameters") != expected_parameters:
            errors.append(f"transform parameters {key}")
        if row.get("transformed_rgb_sha256") != expected_rgb_sha:
            errors.append(f"transformed pixels {key}")
        status, value = row.get("status"), row.get("value")
        if status == "observed":
            if type(value) is not int:
                errors.append(f"observed value type {key}")
            elif variant == "baseline" and value != health:
                errors.append(f"baseline value {key}")
            elif variant != "baseline" and value != health:
                wrong.append(key)
        elif status != "unknown" or value is not None:
            errors.append(f"reader status/value {key}")
        (baseline if variant == "baseline" else perturbed).append(row)

    if seen != expected_rows:
        errors.append("transform coverage")
    baseline_matches = sum(row.get("status") == "observed" and row.get("value") == row.get("expected_health") for row in baseline)
    unknown = sum(row.get("status") == "unknown" for row in perturbed)
    same = sum(row.get("status") == "observed" and row.get("value") == row.get("expected_health") for row in perturbed)
    unknown_by_variant = {}
    for row in perturbed:
        unknown_by_variant[row["variant"]] = unknown_by_variant.get(row["variant"], 0) + (row.get("status") == "unknown")
    expected_metrics = {
        "status": "PASS_NO_FALSE_OBSERVED_VALUE" if baseline_matches == FREEZE["frame_count"] and not wrong else "FAIL_FALSE_OBSERVED_VALUE",
        "baseline_reads": len(baseline),
        "baseline_matches": baseline_matches,
        "perturbed_reads": len(perturbed),
        "perturbed_unknown": unknown,
        "perturbed_observed_same": same,
        "perturbed_observed_wrong": len(wrong),
        "unknown_by_variant": unknown_by_variant,
    }
    for key, expected_value in expected_metrics.items():
        if result.get(key) != expected_value:
            errors.append(f"metric {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    errors = []
    base = FREEZE["base_commit"]
    wad_sha = sha(args.wad.resolve().read_bytes())
    a01_bytes = git_blob(repo, base, FREEZE["a01_freeze_path"])
    if sha(a01_bytes) != FREEZE["a01_freeze_sha256"]:
        errors.append("A01 freeze hash")
    a01 = json.loads(a01_bytes)
    if a01.get("base_commit") != FREEZE["reader_base_commit"]:
        errors.append("reader base commit")
    source_images = {}
    for frame in a01["frames"]:
        frame_bytes = git_blob(repo, base, frame["frame_path"])
        if sha(frame_bytes) != frame["sha256"]:
            errors.append(f"Git frame hash {frame['frame_path']}")
        with Image.open(io.BytesIO(frame_bytes)) as opened:
            source_images[frame["index"]] = opened.convert("RGB")
    errors.extend(audit_result(RESULT, repo, wad_sha, a01, source_images))

    controls = []
    for mutate in (
        lambda x: x["rows"][0].__setitem__("value", 99),
        lambda x: x["rows"].pop(),
        lambda x: x["rows"][0].__setitem__("source_png_sha256", "0" * 64),
        lambda x: x["rows"][0].__setitem__("transformed_rgb_sha256", "0" * 64),
        lambda x: x["rows"][0].__setitem__("expected_health", -1),
    ):
        mutant = copy.deepcopy(RESULT)
        mutate(mutant)
        controls.append(bool(audit_result(mutant, repo, wad_sha, a01, source_images)))
    if not all(controls):
        errors.append("mutation controls failed")

    audit = {
        "schema": "v39-hud-reader-perturbation-audit-a01-v2",
        "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "corrected_auditor_sha256": sha(Path(__file__).read_bytes()),
        "preserved_initial_audit": "results/audit.json (FAIL_AUDIT: v1 did not account for the candidate's JPEG byte digest field)",
        "errors": errors,
        "mutation_controls_passed": sum(controls),
        "mutation_controls_total": len(controls),
        "scope": "posthoc correction of the read-only raw/result auditor; no HUD reader execution or new experiment was performed",
    }
    (PACKAGE / "results" / "audit_v2.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
