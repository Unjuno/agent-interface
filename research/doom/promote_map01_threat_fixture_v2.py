"""Retain the first derived MAP01 threat fixture and its fresh-load evidence."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BUILD = REPO / "results-local/doom/map01-threat-fixture-v2-build-01"
LOAD = REPO / "results-local/doom/map01-threat-fixture-v2-load-01"
SOURCE = REPO / "results-local/doom/fixtures"
TARGET = HERE / "fixtures/map01-threat-contact-v2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main():
    if TARGET.exists():
        raise FileExistsError(TARGET)
    TARGET.mkdir(parents=True)
    source_stem = "map01-threat-contact-v2-dev-01"
    copy(SOURCE / f"{source_stem}.png", TARGET / "save.png")
    copy(SOURCE / f"{source_stem}.source.png", TARGET / "source.png")
    copies = {
        SOURCE / f"{source_stem}.json": TARGET / "provenance/candidate-fixture.json",
        BUILD / "continuation.json": TARGET / "provenance/continuation.json",
        BUILD / "report.json": TARGET / "provenance/build-report.json",
        BUILD / "stderr.txt": TARGET / "provenance/build-stderr.txt",
        BUILD / "runtime/events.jsonl": TARGET / "provenance/build-events.jsonl",
        BUILD / "runtime/owner-events.json": TARGET / "provenance/build-owner-events.json",
        BUILD / "runtime/environment.json": TARGET / "provenance/build-environment.json",
        BUILD / "runtime/sources.json": TARGET / "provenance/build-sources.json",
        LOAD / "report.json": TARGET / "load-probe/report.json",
        LOAD / "stderr.txt": TARGET / "load-probe/stderr.txt",
        LOAD / "runtime/001.png": TARGET / "load-probe/initial.png",
        LOAD / "runtime/events.jsonl": TARGET / "load-probe/events.jsonl",
        LOAD / "runtime/environment.json": TARGET / "load-probe/environment.json",
    }
    for source, target in copies.items():
        copy(source, target)

    fixture = json.loads((SOURCE / f"{source_stem}.json").read_text())
    fixture["fixture_id"] = "map01-threat-contact-v2"
    fixture["save_file"] = "save.png"
    fixture["source_frame"] = "source.png"
    fixture["source_observation"]["image"] = "source.png"
    fixture["runtime_events"] = "provenance/build-events.jsonl"
    (TARGET / "fixture.json").write_text(
        json.dumps(fixture, indent=2) + "\n", encoding="utf-8", newline="\n")
    load_report = json.loads((LOAD / "report.json").read_text())
    review = {
        "schema": "map01_threat_fixture_manual_review_v2",
        "fixture_id": fixture["fixture_id"],
        "reviewer": "Codex GPT-6 primary agent",
        "review_basis": "direct inspection of the lossless derived source and fresh-process loaded initial X11 frame",
        "threat_exposed": True,
        "visible_enemy_count_lower_bound": 1,
        "source_health": 100,
        "source_ammo": 48,
        "loaded_health": 97,
        "loaded_ammo": 48,
        "source_frame_sha256": sha(TARGET / "source.png"),
        "loaded_frame_sha256": sha(TARGET / "load-probe/initial.png"),
        "loaded_frame_original_sha256": load_report["initial_image_sha256"],
        "health_difference_reason": "the real-time game advances after load and before the first exact capture; both values are retained",
        "limits": "manual threat/ammo classification plus exact HUD-health extraction; fixture grants no action authority and is not gameplay success",
    }
    (TARGET / "review.json").write_text(
        json.dumps(review, indent=2) + "\n", encoding="utf-8", newline="\n")
    files = []
    for path in sorted(TARGET.rglob("*")):
        if path.is_file() and path.name != "retention-manifest.json":
            files.append({"path": path.relative_to(TARGET).as_posix(),
                          "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {
        "schema": "map01_threat_fixture_retention_v2",
        "fixture_id": fixture["fixture_id"],
        "copy_contract": "first frozen derived fixture, parent-bound OS-input provenance and fresh-process load evidence; manifest excludes itself and post-promotion audit",
        "excluded_derived_files": ["retention-manifest.json", "audit.json"],
        "total_files": len(files),
        "total_bytes": sum(row["bytes"] for row in files),
        "files": files,
    }
    (TARGET / "retention-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: manifest[key] for key in
                      ("fixture_id", "total_files", "total_bytes")}, indent=2))


if __name__ == "__main__":
    main()
