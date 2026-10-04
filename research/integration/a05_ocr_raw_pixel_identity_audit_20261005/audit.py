"""Reconstruct A05 crop pixels and compare them with retained OCR inputs.

This is a read-only Pillow audit. It does not invoke Tesseract or any study
runner. Run from any directory inside a checkout containing the A05 files.
"""

from __future__ import annotations

import hashlib
import io
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, __version__ as pillow_version


HERE = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(
    ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"], text=True
).strip())
A05 = REPO / "research/integration/compiled_comparison_57_4d74_20261004/a05"
READBACK = A05 / "independent-readback"
PREVIEW_DIR = READBACK / "crop-previews"
MANIFEST_PATH = PREVIEW_DIR / "manifest.json"
OCR_SEQUENCES = {(1, 5): 124, (1, 6): 143, (2, 6): 150}
EXPECTED_CROP_ENTRIES = {
    (block, task, crop)
    for block, task in ((1, 5), (1, 6), (2, 6))
    for crop in ("frozen", "candidate")
}
OCR_INPUT_SHA256 = {
    (1, 5): "cfa028089883adf5c705df8fa36f1da19b249d0d459993dcdbe7edb370af59eb",
    (1, 6): "749a67248052644317ad0f98c7fdf6962e862e9dbbc8f972719d4b988fd27c4a",
    (2, 6): "356b8d3a900e8e6bfbba1b1ce455291801e29d46939efc3d2afe40125f15fbb7",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pixel_equal(left: Image.Image, right: Image.Image) -> bool:
    a = left.convert("RGB")
    b = right.convert("RGB")
    return a.size == b.size and ImageChops.difference(a, b).getbbox() is None


def main() -> dict:
    started = datetime.now(timezone.utc).isoformat()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["source_revision"] != "58bcbb4c45501880db8782158ddd3add3b765984":
        raise ValueError("unexpected retained A05 source revision")
    entries = manifest.get("entries")
    actual_entries = {
        (entry.get("block"), entry.get("task"), entry.get("crop"))
        for entry in entries
    } if isinstance(entries, list) else set()
    if (not isinstance(entries, list)
            or len(entries) != len(EXPECTED_CROP_ENTRIES)
            or actual_entries != EXPECTED_CROP_ENTRIES):
        raise ValueError("manifest must contain exactly the expected crop entries")

    rows = []
    for entry in entries:
        source_path = REPO / entry["source_path"]
        preview_path = READBACK / entry["output"]
        source_bytes = source_path.read_bytes()
        source_digest = sha256(source_bytes)
        if source_digest != entry["source_sha256"]:
            raise ValueError(f"source hash mismatch: {source_path}")

        with Image.open(io.BytesIO(source_bytes)) as source_image:
            generated = source_image.convert("RGB").crop(
                tuple(entry["box_xyxy"])
            ).resize(tuple(entry["output_size"]))
        encoded = io.BytesIO()
        generated.save(encoded, format="PNG")
        generated_bytes = encoded.getvalue()
        preview_bytes = preview_path.read_bytes()
        if sha256(preview_bytes) != entry["output_sha256"]:
            raise ValueError(f"preview hash mismatch: {preview_path}")
        with Image.open(io.BytesIO(preview_bytes)) as preview_image:
            preview = preview_image.convert("RGB")

        row = {
            "block": entry["block"],
            "task": entry["task"],
            "crop": entry["crop"],
            "source_path": entry["source_path"],
            "source_sha256": source_digest,
            "box_xyxy": entry["box_xyxy"],
            "output_size": list(generated.size),
            "generated_preview_sha256": sha256(generated_bytes),
            "manifest_preview_sha256": entry["output_sha256"],
            "reconstructed_preview_matches_manifest_bytes": (
                sha256(generated_bytes) == entry["output_sha256"]
            ),
            "reconstructed_preview_matches_manifest_pixels": pixel_equal(
                generated, preview
            ),
        }

        if entry["crop"] == "frozen":
            sequence = OCR_SEQUENCES[(entry["block"], entry["task"])]
            ocr_path = A05 / (
                f"formal-output/block-{entry['block']}/C/client/ocr-{sequence}.png"
            )
            ocr_bytes = ocr_path.read_bytes()
            ocr_digest = sha256(ocr_bytes)
            if ocr_digest != OCR_INPUT_SHA256[(entry["block"], entry["task"])]:
                raise ValueError(f"archived OCR input hash mismatch: {ocr_path}")
            with Image.open(io.BytesIO(ocr_bytes)) as ocr_image:
                ocr_pixels = ocr_image.convert("RGB")
            row.update({
                "archived_ocr_input_path": str(ocr_path.relative_to(REPO)),
                "archived_ocr_input_sha256": ocr_digest,
                "archived_ocr_input_size": list(ocr_pixels.size),
                "archived_ocr_input_matches_preview_pixels": pixel_equal(
                    ocr_pixels, preview
                ),
                "archived_ocr_input_matches_preview_bytes": (
                    sha256(ocr_bytes) == sha256(preview_bytes)
                ),
            })
        rows.append(row)

    frozen_rows = [row for row in rows if row["crop"] == "frozen"]
    candidate_rows = [row for row in rows if row["crop"] == "candidate"]
    result = {
        "schema": "a05_raw_crop_pixel_identity_audit_v1",
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit_before_audit": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "pinned_a05_source_revision": manifest["source_revision"],
        "crop_manifest_sha256": sha256(MANIFEST_PATH.read_bytes()),
        "audit_script_sha256": sha256(Path(__file__).resolve().read_bytes()),
        "expected_crop_entries": len(EXPECTED_CROP_ENTRIES),
        "archived_ocr_hashes_pinned": True,
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "invocation": [sys.executable,
                       str(Path(__file__).relative_to(REPO))],
        "pillow": pillow_version,
        "tesseract_invoked": False,
        "rows": rows,
        "frozen_preview_reconstructions": len(frozen_rows),
        "candidate_preview_reconstructions": len(candidate_rows),
        "frozen_preview_reconstructions_match": all(
            row["reconstructed_preview_matches_manifest_bytes"]
            and row["reconstructed_preview_matches_manifest_pixels"]
            for row in frozen_rows
        ),
        "candidate_preview_reconstructions_match": all(
            row["reconstructed_preview_matches_manifest_bytes"]
            and row["reconstructed_preview_matches_manifest_pixels"]
            for row in candidate_rows
        ),
        "archived_ocr_inputs_pixel_identical_to_frozen_previews": all(
            row["archived_ocr_input_matches_preview_pixels"]
            for row in frozen_rows
        ),
        "archived_ocr_inputs_byte_identical_to_frozen_previews": all(
            row["archived_ocr_input_matches_preview_bytes"]
            for row in frozen_rows
        ),
        "scope": (
            "read-only crop reconstruction and pixel comparison; no OCR, GUI, "
            "provider, runtime, or formal allocation"
        ),
    }
    if not (result["frozen_preview_reconstructions_match"]
            and result["candidate_preview_reconstructions_match"]
            and result["archived_ocr_inputs_pixel_identical_to_frozen_previews"]):
        raise AssertionError("retained crop pixel identity did not reconcile")
    return result


if __name__ == "__main__":
    output = main()
    target = HERE / "AUDIT.json"
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps(output, indent=2, sort_keys=True))
