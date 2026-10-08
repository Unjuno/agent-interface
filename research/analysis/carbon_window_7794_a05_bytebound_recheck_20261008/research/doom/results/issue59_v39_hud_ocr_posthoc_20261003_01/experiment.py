#!/usr/bin/env python3
"""Post-hoc generic OCR probe over retained Issue #59 MAP01 HUD frames."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import PIL
from PIL import Image, ImageOps


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[3]
DATA = REPO / "research/doom/results/map01-v39-coast-liveness-live-01/runtime"
EVENTS_SHA256 = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
SOURCES_SHA256 = "3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8"
CROP = (423, 591, 501, 629)
SCALES = ("gray", "threshold_150", "inverted_threshold_150")
PSMS = (7, 8, 10, 13)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_health_transitions(events: list[dict]) -> list[dict]:
    observations = [row for row in events if row.get("event") == "typed_observation"]
    selected = []
    previous = None
    for row in observations:
        health = row["signals"]["health"]["value"]
        if previous is not None and health != previous:
            selected.append(row)
        previous = health
    return selected


def normalize_digits(text: str) -> str:
    return "".join(re.findall(r"[0-9]", text))


def rgb_digest(path: Path) -> str:
    with Image.open(path) as image:
        return sha256_bytes(image.convert("RGB").tobytes())


def image_variants(path: Path) -> dict[str, Image.Image]:
    with Image.open(path) as source:
        gray = source.convert("L").crop(CROP)
    enlarged = gray.resize((gray.width * 10, gray.height * 10), Image.Resampling.NEAREST)
    threshold = enlarged.point(lambda value: 255 if value > 150 else 0)
    return {
        "gray": enlarged,
        "threshold_150": threshold,
        "inverted_threshold_150": ImageOps.invert(threshold),
    }


def run_tesseract(image: Image.Image, psm: int) -> tuple[str, int]:
    executable = shutil.which("tesseract")
    if executable is None:
        raise RuntimeError("tesseract executable not found")
    encoded = io.BytesIO()
    image.save(encoded, format="PNG")
    start = time.perf_counter_ns()
    completed = subprocess.run(
        [
            executable,
            "stdin",
            "stdout",
            "--psm",
            str(psm),
            "-c",
            "tessedit_char_whitelist=0123456789%",
        ],
        input=encoded.getvalue(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    elapsed = time.perf_counter_ns() - start
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace").strip(), elapsed


def exact_counts(rows: list[dict]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for scale in SCALES:
        for psm in PSMS:
            key = f"{scale}/psm{psm}"
            exact = sum(
                row["ocr"][key]["normalized_digits"] == str(row["typed_health"])
                for row in rows
            )
            counts[key] = {"exact_matches": exact, "n": len(rows)}
    return counts


def main() -> None:
    started_utc = datetime.now(timezone.utc).isoformat()
    if sha256_file(DATA / "events.jsonl") != EVENTS_SHA256:
        raise SystemExit("STOP_SOURCE_EVENTS_HASH_MISMATCH")
    if sha256_file(DATA / "sources.json") != SOURCES_SHA256:
        raise SystemExit("STOP_SOURCE_MANIFEST_HASH_MISMATCH")

    tesseract_version = subprocess.run(
        [shutil.which("tesseract") or "tesseract", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
        text=True,
    ).stdout.splitlines()[0]
    if not tesseract_version.startswith("tesseract 5.5.2"):
        raise SystemExit(f"STOP_TESSERACT_VERSION_MISMATCH: {tesseract_version}")

    events = [json.loads(line) for line in (DATA / "events.jsonl").read_text().splitlines()]
    selected = selected_health_transitions(events)
    rows = []
    for event in selected:
        sequence = event["sequence"]
        frame = DATA / f"{sequence:03}.png"
        with Image.open(frame) as image:
            frame_size = list(image.size)
        actual_rgb_sha = rgb_digest(frame)
        recorded_rgb_sha = event["frame_rgb_sha256"]
        if actual_rgb_sha != recorded_rgb_sha:
            raise SystemExit(f"STOP_FRAME_RGB_HASH_MISMATCH sequence={sequence}")

        values = {}
        for scale, image in image_variants(frame).items():
            for psm in PSMS:
                raw_text, elapsed_ns = run_tesseract(image, psm)
                values[f"{scale}/psm{psm}"] = {
                    "raw_text": raw_text,
                    "normalized_digits": normalize_digits(raw_text),
                    "elapsed_ns": elapsed_ns,
                }
        rows.append(
            {
                "sequence": sequence,
                "capture_ns": event["capture_ns"],
                "typed_ready_ns": event["typed_ready_ns"],
                "typed_health": event["signals"]["health"]["value"],
                "frame_file": frame.name,
                "frame_file_sha256": sha256_file(frame),
                "frame_rgb_sha256_recorded": recorded_rgb_sha,
                "frame_rgb_sha256_recomputed": actual_rgb_sha,
                "frame_size": frame_size,
                "ocr": values,
            }
        )

    counts = exact_counts(rows)
    result = {
        "run_id": "issue59_v39_hud_ocr_posthoc_20261003_01",
        "status": "POSTHOC_EXPLORATORY_INDEPENDENT_OCR_GATE_NOT_ESTABLISHED",
        "base_commit": "e5270c7bfe50911225afc6c3b5273021331b2bb1",
        "runtime_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, check=True, text=True, stdout=subprocess.PIPE
        ).stdout.strip(),
        "input": {
            "events_sha256": EVENTS_SHA256,
            "sources_sha256": SOURCES_SHA256,
            "typed_observation_count": sum(row.get("event") == "typed_observation" for row in events),
            "health_transition_count": len(rows),
        },
        "method": {
            "tesseract_version": tesseract_version,
            "pillow_version": PIL.__version__,
            "crop_xyxy": list(CROP),
            "scale_factor": 10,
            "resampling": "nearest",
            "threshold": 150,
            "psm_values": list(PSMS),
            "character_whitelist": "0123456789%",
            "posthoc": True,
            "blind_labels": False,
            "independent_ground_truth": False,
        },
        "execution": {
            "command": "python3 experiment.py",
            "started_utc": started_utc,
            "python_version": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python_executable": sys.executable,
            "ocr_invocations": len(rows) * len(SCALES) * len(PSMS),
        },
        "code_sha256": {
            name: sha256_file(PACKAGE / name)
            for name in ("PLAN.md", "experiment.py", "audit.py", "test_experiment.py")
        },
        "agreement_with_recorded_typed_health": counts,
        "rows": rows,
        "scope": [
            "Agreement is measured against the same run's WAD-specific typed extractor, not independent labels.",
            "This does not establish useful-feedback onset, causal damage, control benefit, recovery efficacy, or the live Issue #59 gate.",
            "No live game, model call, input, or allocation was used.",
        ],
    }
    output = PACKAGE / "RESULT.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "rows": len(rows), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
