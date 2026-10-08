#!/usr/bin/env python3
"""Independent provenance and arithmetic audit for RESULT.json."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from PIL import Image


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[3]
DATA = REPO / "research/doom/results/map01-v39-coast-liveness-live-01/runtime"
EXPECTED_EVENTS_SHA256 = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
EXPECTED_SOURCES_SHA256 = "3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8"
EXPECTED_SEQUENCES = [37, 62, 76, 81, 90, 97, 103, 115, 144, 154, 167, 193, 200, 218]
CONFIGURATIONS = [
    f"{scale}/psm{psm}"
    for scale in ("gray", "threshold_150", "inverted_threshold_150")
    for psm in (7, 8, 10, 13)
]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recorded_health_transitions(events: list[dict]) -> list[dict]:
    previous = None
    result = []
    for event in events:
        if event.get("event") != "typed_observation":
            continue
        health = event["signals"]["health"]["value"]
        if previous is not None and health != previous:
            result.append(event)
        previous = health
    return result


def verify(result: dict, events_path: Path, package: Path) -> list[str]:
    events_hash = file_hash(events_path)
    sources_hash = file_hash(DATA / "sources.json")
    if events_hash != EXPECTED_EVENTS_SHA256 or result["input"]["events_sha256"] != events_hash:
        raise ValueError("retained events hash mismatch")
    if sources_hash != EXPECTED_SOURCES_SHA256 or result["input"]["sources_sha256"] != sources_hash:
        raise ValueError("retained source manifest hash mismatch")
    for name in ("PLAN.md", "experiment.py", "audit.py", "test_experiment.py"):
        if result["code_sha256"].get(name) != file_hash(package / name):
            raise ValueError(f"package source hash mismatch: {name}")

    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    expected = recorded_health_transitions(events)
    typed_count = sum(event.get("event") == "typed_observation" for event in events)
    if typed_count != 218 or result["input"]["typed_observation_count"] != typed_count:
        raise ValueError("typed observation count mismatch")
    if [event["sequence"] for event in expected] != EXPECTED_SEQUENCES:
        raise ValueError("selected frame sequence set mismatch")
    if result["input"]["health_transition_count"] != len(expected):
        raise ValueError("health transition count mismatch")

    result_rows = result["rows"]
    if len(result_rows) != len(expected):
        raise ValueError("result row count mismatch")
    audited_counts = {configuration: 0 for configuration in CONFIGURATIONS}
    for row, source_event in zip(result_rows, expected, strict=True):
        sequence = source_event["sequence"]
        health = source_event["signals"]["health"]["value"]
        if row["sequence"] != sequence or row["typed_health"] != health:
            raise ValueError(f"typed source mismatch at sequence {sequence}")
        if row["capture_ns"] != source_event["capture_ns"] or row["typed_ready_ns"] != source_event["typed_ready_ns"]:
            raise ValueError(f"typed timing mismatch at sequence {sequence}")
        if row["frame_rgb_sha256_recorded"] != source_event["frame_rgb_sha256"]:
            raise ValueError(f"recorded RGB digest linkage mismatch at sequence {sequence}")
        image_path = DATA / f"{sequence:03}.png"
        if row["frame_file"] != image_path.name or row["frame_file_sha256"] != file_hash(image_path):
            raise ValueError(f"PNG file hash mismatch at sequence {sequence}")
        with Image.open(image_path) as image:
            actual_rgb = hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
            actual_size = list(image.size)
        if row["frame_rgb_sha256_recorded"] != actual_rgb or row["frame_rgb_sha256_recomputed"] != actual_rgb:
            raise ValueError(f"RGB digest mismatch at sequence {sequence}")
        if row["frame_size"] != actual_size:
            raise ValueError(f"image dimensions mismatch at sequence {sequence}")
        if set(row["ocr"]) != set(CONFIGURATIONS):
            raise ValueError(f"OCR matrix incomplete at sequence {sequence}")
        for configuration in CONFIGURATIONS:
            prediction = row["ocr"][configuration]
            if not isinstance(prediction["raw_text"], str) or not isinstance(prediction["elapsed_ns"], int):
                raise ValueError(f"malformed OCR record at sequence {sequence}")
            if prediction["elapsed_ns"] < 0:
                raise ValueError(f"negative OCR duration at sequence {sequence}")
            normalized = "".join(re.findall(r"[0-9]", prediction["raw_text"]))
            if prediction["normalized_digits"] != normalized:
                raise ValueError(f"OCR normalization mismatch at sequence {sequence}")
            audited_counts[configuration] += prediction["normalized_digits"] == str(health)

    expected_counts = result["agreement_with_recorded_typed_health"]
    for configuration, exact in audited_counts.items():
        if expected_counts[configuration] != {"exact_matches": exact, "n": len(expected)}:
            raise ValueError(f"agreement count mismatch for {configuration}")
    if result["method"]["blind_labels"] is not False or result["method"]["independent_ground_truth"] is not False:
        raise ValueError("scope boundary was weakened")
    if result["method"]["posthoc"] is not True:
        raise ValueError("post-hoc status missing")
    if result["execution"]["ocr_invocations"] != len(expected) * len(CONFIGURATIONS):
        raise ValueError("OCR invocation count mismatch")
    if len(result["code_sha256"]) != 4:
        raise ValueError("unexpected source hash set")
    return [
        "PASS_SOURCE_AND_FRAME_PROVENANCE",
        "PASS_COMPLETE_OCR_MATRIX_AND_COUNT_RECONSTRUCTION",
        "PASS_POSTHOC_SCOPE_BOUNDARY_RETAINED",
    ]


def main() -> None:
    result = json.loads((PACKAGE / "RESULT.json").read_text())
    checks = verify(result, DATA / "events.jsonl", PACKAGE)
    print(json.dumps({"status": "PASS_POSTHOC_ARTIFACT_AUDIT", "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
