"""Audit the promoted real-MAP01 threat contact fixture."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE / "fixtures/map01-threat-contact-v1"
sys.path.insert(0, str(HERE))
from session_map01_v7 import validate_fixture_manifest


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = read(ROOT / "retention-manifest.json")
    assert manifest["fixture_id"] == "map01-threat-contact-v1"
    assert manifest["excluded_derived_files"] == ["retention-manifest.json", "audit.json"]
    assert manifest["total_files"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(row["bytes"] for row in manifest["files"])
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], row["path"]
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()}
    actual.discard("audit.json")
    assert actual == {row["path"] for row in manifest["files"]} | {"retention-manifest.json"}

    fixture, save = validate_fixture_manifest(
        ROOT / "fixture.json", "1.3.0",
        "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b", 1)
    assert save == (ROOT / "save.png").resolve()
    assert fixture["fixture_id"] == manifest["fixture_id"]
    assert fixture["episode_tic"] == 1263
    assert fixture["source_observation"]["sequence"] == 119

    build = read(ROOT / "provenance/build-report.json")
    assert build["passed"] and build["programs"] == build["verified_releases"] == 7
    assert build["model_calls"] == 0 and build["episode_tic"] == 1263
    events = [json.loads(line) for line in (ROOT / "provenance/build-events.jsonl").read_text().splitlines()]
    counts = Counter(row.get("event") for row in events)
    assert counts["accepted"] == counts["terminal"] == 7 and counts["fixture_saved"] == 1
    assert all(row["release"]["verified"] and not row["release"]["keys_down"] and
               not row["release"]["buttons_down"] for row in events if row.get("event") == "terminal")

    load = read(ROOT / "load-probe/report.json")
    assert load["passed"] and load["model_calls"] == 0
    assert load["fixture"]["source_episode_tic"] == load["fixture"]["after_load_tic"] == 1263
    assert load["initial_observation"]["sequence"] == 1 and load["initial_observation"]["exact"]
    assert sha(ROOT / "load-probe/initial.png") == load["initial_image_sha256"]
    assert not load["score"]["player_dead"]

    review = read(ROOT / "review.json")
    assert review["threat_exposed"] is True and review["visible_enemy_count_lower_bound"] >= 1
    assert review["source_health"] == review["loaded_health"] == 100
    assert review["source_ammo"] == review["loaded_ammo"] == 50
    assert review["source_frame_sha256"] == sha(ROOT / "source.png")
    assert review["loaded_frame_sha256"] == sha(ROOT / "load-probe/initial.png")
    assert review["loaded_frame_original_sha256"] == load["initial_image_sha256"]

    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]
    audit = {
        "schema": "map01_threat_fixture_audit_v1", "passed": True,
        "fixture_id": manifest["fixture_id"], "map": "MAP01", "skill": 1,
        "vizdoom": "1.3.0", "episode_tic": 1263,
        "build_model_calls": 0, "build_os_input_programs": 7,
        "verified_build_releases": 7,
        "fresh_process_load": True, "loaded_tic_matches_source": True,
        "source_exact": True, "loaded_observation_exact": True,
        "visible_enemy_reviewed_in_source_and_loaded_frame": True,
        "visible_enemy_count_lower_bound": 1,
        "initial_health": 100, "initial_ammo": 50,
        "credential_pattern_matches": 0,
        "authority": "benchmark start-state evidence only; grants no runtime input authority",
        "limits": "single experimental ViZDoom save/load fixture; no gameplay, control-quality, reliability or human-speed claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
