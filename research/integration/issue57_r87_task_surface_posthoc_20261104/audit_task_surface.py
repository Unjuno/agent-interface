"""Posthoc task-surface crop analysis of the retained r87 screenshot pair.

This script reads verified retained screenshots and reports an exploratory
crop candidate. It does not alter r87's frozen full-frame gate or outcome.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
R87 = ROOT / "research/integration/issue57_calc_sameframe_live_20261103_r87"
ATTEMPT = R87 / "r87-c11"
CUSTODY = ROOT / "research/integration/issue57_r87_custody_correction_20261104/CUSTODY_CORRECTED_MANIFEST_20261104.json"
OUT = ROOT / "research/integration/issue57_r87_task_surface_posthoc_20261104/AUDIT.json"

# Initial visual estimate of the Calc sheet canvas. It leaves one scrollbar
# edge pixel inside the crop; the second diagnostic clips that boundary.
TASK_SURFACE_BOX = (0, 126, 1219, 742)
REFINED_TASK_SURFACE_BOX = (0, 126, 1218, 742)


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    compiled = json.loads((ATTEMPT / "compiled-result.json").read_text(encoding="utf-8"))
    outcome = json.loads((R87 / "audit.json").read_text(encoding="utf-8"))
    custody = json.loads(CUSTODY.read_text(encoding="utf-8"))
    observations = {row.get("evidence_ref"): row for row in compiled["method_receipt"]["observations"]}
    first = observations.get("observation-13")
    second = observations.get("observation-18")
    if first is None or second is None:
        fail("the two preregistered final observations are missing")
    if outcome.get("status") != "FAIL_OR_UNKNOWN" or outcome.get("failed_gates") != [
        "same_digest_across_final_save_observation"
    ]:
        fail("the preserved r87 full-frame outcome differs from the retained report")

    manifest_rows = custody.get("files", [])
    images = {}
    source_records = {}
    for label, observation in (("observation-13", first), ("observation-18", second)):
        digest = observation.get("evidence_digest")
        candidates = sorted(
            (row for row in manifest_rows
             if row.get("expected_sha256") == digest
             and row.get("availability") == "present"
             and row.get("disposition") == "verified_original_bytes"),
            key=lambda row: row["path"],
        )
        if not candidates:
            fail(f"custody manifest has no verified screenshot for {label}")
        record = candidates[0]
        path = ATTEMPT / Path(record["path"])
        if not path.is_file():
            fail(f"verified screenshot is absent from this checkout: {record['path']}")
        raw = path.read_bytes()
        if len(raw) != record["expected_bytes"] or sha256(raw) != digest:
            fail(f"screenshot bytes fail original custody digest for {label}")
        image = Image.open(path)
        image.load()
        if image.size != (1280, 800):
            fail(f"unexpected source image dimensions for {label}: {image.size}")
        images[label] = image.convert("RGB")
        source_records[label] = {
            "evidence_ref": label,
            "sequence": observation.get("sequence"),
            "sha256": digest,
            "custody_path": record["path"],
            "custody_disposition": record["disposition"],
            "bytes": len(raw),
        }

    left, right = images["observation-13"], images["observation-18"]
    if sha256(left.tobytes()) == sha256(right.tobytes()):
        fail("source pixel arrays unexpectedly match despite distinct full-frame digests")
    a, b = list(left.getdata()), list(right.getdata())
    full_changed = sum(px != qx for px, qx in zip(a, b))
    total_pixels = left.width * left.height

    def crop_result(box):
        crop_left = left.crop(box)
        crop_right = right.crop(box)
        changed = [
            {"xy": [x, y], "observation_13_rgb": left.getpixel((x, y)),
             "observation_18_rgb": right.getpixel((x, y))}
            for y in range(box[1], box[3])
            for x in range(box[0], box[2])
            if left.getpixel((x, y)) != right.getpixel((x, y))
        ]
        pixel_bytes = struct.pack(">II", crop_left.width, crop_left.height) + crop_left.tobytes()
        return {
            "box": list(box),
            "dimensions": [crop_left.width, crop_left.height],
            "changed_pixels": len(changed),
            "surface_pixel_sha256_rgb_with_dimensions": sha256(pixel_bytes),
            "same_candidate_surface": not changed,
            "changed_pixel_details": changed,
        }

    initial_crop = crop_result(TASK_SURFACE_BOX)
    refined_crop = crop_result(REFINED_TASK_SURFACE_BOX)

    # The audited sidecar hash binds to a retained server-owned FODS artifact.
    artifact_hash = outcome.get("artifact_sha256")
    artifact_rows = [
        row for row in manifest_rows
        if row.get("path", "").endswith("/task-artifact.fods")
        and row.get("expected_sha256") == artifact_hash
        and row.get("availability") == "present"
        and row.get("disposition") == "verified_original_bytes"
    ]
    if not artifact_rows:
        fail("task artifact is not present in the corrected custody manifest")
    artifact_path = ATTEMPT / Path(sorted(artifact_rows, key=lambda row: row["path"])[0]["path"])
    artifact_data = artifact_path.read_bytes()
    if sha256(artifact_data) != artifact_hash:
        fail("task artifact bytes do not match the retained audit receipt")

    result = {
        "schema": "issue57-r87-task-surface-posthoc-audit-v1",
        "classification": "POSTHOC_CROP_CANDIDATE_ONLY",
        "selection_was_posthoc": True,
        "prospective_gate_validated": False,
        "original_r87_outcome_unchanged": outcome["status"],
        "original_failed_gates_unchanged": outcome["failed_gates"],
        "inputs": source_records,
        "full_frame": {
            "dimensions": [left.width, left.height],
            "observation_13_sha256": first["evidence_digest"],
            "observation_18_sha256": second["evidence_digest"],
            "different_pixels": full_changed,
            "total_pixels": total_pixels,
            "different_pixel_fraction": full_changed / total_pixels,
        },
        "candidate_task_surface": {
            "coordinate_convention": "Pillow crop box: left, upper, right, lower; right/lower exclusive",
            "included": "Calc column and row headers plus visible spreadsheet cell canvas",
            "intended_exclusion": "window title, menus, toolbars, bottom tabs/status, horizontal and vertical scrollbars",
            "boundary_note": "initial crop includes one scrollbar-edge column at x=1218; refined crop excludes that column",
            "initial_visual_boundary_crop": initial_crop,
            "one_pixel_scrollbar_edge_refinement": refined_crop,
            "interpretation": "exploratory only; both crop boundaries were selected after observing the mismatch",
        },
        "retained_task_artifact": {
            "sha256": artifact_hash,
            "bytes": len(artifact_data),
            "custody_path": str(artifact_path.relative_to(ATTEMPT)).replace("\\", "/"),
            "outer_audit_task_cells": outcome.get("task_cells"),
            "compiled_result_task_success": compiled.get("task_success"),
            "compiled_effect_verification": compiled.get("task_effect_verification"),
        },
        "scope_limits": [
            "does not change the preregistered full-frame equality gate or FAIL_OR_UNKNOWN result",
            "does not establish that the crop is a sufficient observation-validity contract",
            "does not establish a same-frame pass, model/provider efficiency, or a new live result",
            "the original packet still has seven unavailable log files and an unrecovered experiment.py source mismatch",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": result["classification"],
        "original_outcome": result["original_r87_outcome_unchanged"],
        "full_frame_changed_pixels": full_changed,
        "candidate_crop": list(TASK_SURFACE_BOX),
        "initial_crop_changed_pixels": initial_crop["changed_pixels"],
        "refined_crop_changed_pixels": refined_crop["changed_pixels"],
        "candidate_only": True,
        "output": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
