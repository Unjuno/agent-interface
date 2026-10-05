#!/usr/bin/env python3
"""Independent blob-level audit of PR #7628's retained OCR evidence."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


PR_REF = "473c913c2a0baa0acebd11539c9be5eaffbdc97b"
MAIN_REF = "d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6"
STUDY = "research/integration/compiled_comparison_57_4d74_20261004/a05"
PR_CHECK = (
    "research/integration/a05_ocr_crop_environment_check_20261004/"
    "OFFLINE_OCR_CHECK.json"
)


def git_blob(repo: Path, ref: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"missing git object {ref}:{path}: {result.stderr.decode().strip()}")
    return result.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse(data: bytes) -> dict:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(repo: Path) -> dict:
    check = parse(git_blob(repo, PR_REF, PR_CHECK))
    source_revision = check["source_revision"]
    readback = f"{STUDY}/independent-readback/"
    manifest_path = readback + "crop-previews/manifest.json"
    manifest_bytes = git_blob(repo, MAIN_REF, manifest_path)
    manifest = parse(manifest_bytes)
    require(
        sha256(manifest_bytes) == check["crop_manifest_sha256"],
        "crop-preview manifest digest does not match the PR record",
    )

    entries = manifest["entries"]
    require(len(entries) == 6, "expected six crop preview entries")
    outputs = []
    source_images = []
    for entry in entries:
        source = git_blob(repo, source_revision, entry["source_path"])
        require(sha256(source) == entry["source_sha256"], "source screenshot hash mismatch")
        source_images.append(entry["source_path"])

        output_path = readback + entry["output"]
        output = git_blob(repo, MAIN_REF, output_path)
        require(sha256(output) == entry["output_sha256"], "crop preview hash mismatch")
        outputs.append(output_path)

    check_rows = {(r["block"], r["task"], r["crop"]): r for r in check["rows"]}
    manifest_rows = {(e["block"], e["task"], e["crop"]): e for e in entries}
    require(set(check_rows) == set(manifest_rows), "OCR and crop manifest row sets differ")
    for key, row in check_rows.items():
        require(
            row["crop_sha256"] == manifest_rows[key]["output_sha256"],
            f"OCR row crop hash mismatch for {key}",
        )
        require(row["exact_match"] == (row["recognized"] == row["expected_token"]),
                f"exact-match flag inconsistent for {key}")
        require(row["ocr_exit"] == 0 and row["stderr"] == "",
                f"OCR execution status not clean for {key}")

    diagnostics = parse(git_blob(repo, MAIN_REF, readback + "C_FAILURE_DIAGNOSTICS.json"))
    failures = {(r["block"], r["task"]): r for r in diagnostics["failures"]}
    archived = {(r["block"], r["task"]): r for r in check["archived_ocr_input_rerun"]}
    require(len(failures) == 3 and len(archived) == 3, "expected three recorded OCR failures")
    for key, rerun in archived.items():
        failure = failures[key]
        image = git_blob(repo, source_revision, rerun["path"])
        require(sha256(image) == rerun["sha256"], f"archived OCR-input image hash mismatch for {key}")
        historical = failure["ocr_stdout"].strip()
        require(historical == rerun["historical_stdout"], f"historical stdout mismatch for {key}")
        require(rerun["local_tesseract_stdout"] == failure["expected_token"],
                f"local OCR result is not exact for {key}")
        require(len(rerun["local_tesseract_stdout"]) == len(historical) + 1
                and rerun["local_tesseract_stdout"][1:] == historical,
                f"historical/local stdout difference is not exactly the leading t for {key}")

    near_misses = check["near_miss_pairs"]
    require(len(near_misses) == check["one_character_near_miss_count"] == 3,
            "near-miss count is inconsistent")
    for pair in near_misses:
        observed, proposed = pair["recognized"], pair["near_miss_expected"]
        require(len(observed) == len(proposed), "near-miss pair length differs")
        require(sum(a != b for a, b in zip(observed, proposed)) == 1,
                "near-miss pair is not a one-character substitution")
        require(pair["rejected"] == (observed != proposed),
                "near-miss rejection is not strict equality")

    return {
        "status": "PASS_RETAINED_BLOB_LINKAGES",
        "pr_head": subprocess.check_output(
            ["git", "rev-parse", PR_REF], cwd=repo, text=True
        ).strip(),
        "audited_main": subprocess.check_output(
            ["git", "rev-parse", MAIN_REF], cwd=repo, text=True
        ).strip(),
        "source_revision": source_revision,
        "crop_manifest_sha256": sha256(manifest_bytes),
        "verified_source_screenshots": sorted(set(source_images)),
        "verified_crop_previews": sorted(outputs),
        "verified_archived_ocr_input_count": len(archived),
        "verified_historical_diagnostic_rows": len(failures),
        "verified_local_ocr_rows": len(check_rows),
        "verified_near_miss_predicate_rows": len(near_misses),
        "tesseract_on_path": shutil.which("tesseract") is not None,
        "limits": [
            "No OCR invocation was run by this audit; the local Tesseract result is checked only as a recorded field.",
            "The near-miss cases change the expected token and apply strict string equality; they do not perturb image pixels or measure OCR false acceptance.",
            "The audit verifies retained Git blob identities and record consistency, not the original live adapter or historical Tesseract environment.",
            "The source screenshots are pinned to the stated source revision; the derived crop manifest and previews are later main-branch artifacts identified by SHA-256.",
        ],
    }


if __name__ == "__main__":
    try:
        repo = Path(sys.argv[1] if len(sys.argv) > 1 else Path.cwd()).resolve()
        result = run(repo)
        print(json.dumps(result, indent=2, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        raise SystemExit(1)
