"""Audit the first derived real-MAP01 threat fixture."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "fixtures/map01-threat-contact-v2"
PARENT = HERE / "fixtures/map01-threat-contact-v1"
sys.path.insert(0, str(HERE))
from doom_hud_signal_v1 import DoomStatusNumberReader
from session_map01_v8 import validate_fixture_manifest


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prereg = read(HERE / "map01_threat_fixture_v2_prereg.json")
    for path, expected in prereg["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    manifest = read(ROOT / "retention-manifest.json")
    assert manifest["fixture_id"] == "map01-threat-contact-v2"
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
    assert fixture["episode_tic"] == 1366 > 1263
    assert fixture["source_observation"]["sequence"] == 17
    parent = fixture["parent_fixture"]
    assert parent["manifest_sha256"] == sha(PARENT / "fixture.json")
    assert parent["save_sha256"] == sha(PARENT / "save.png")
    assert parent["source_episode_tic"] == parent["loaded_episode_tic"] == 1263
    assert sha(ROOT / "source.png") != sha(PARENT / "source.png")

    build = read(ROOT / "provenance/build-report.json")
    assert build["passed"] and build["programs"] == build["verified_releases"] == 2
    assert build["model_calls"] == 0 and build["episode_tic"] == 1366
    events = [json.loads(line) for line in
              (ROOT / "provenance/build-events.jsonl").read_text().splitlines()]
    counts = Counter(row.get("event") for row in events)
    assert counts["accepted"] == counts["terminal"] == 2 and counts["fixture_saved"] == 1
    assert all(row["release"]["verified"] and not row["release"]["keys_down"] and
               not row["release"]["buttons_down"]
               for row in events if row.get("event") == "terminal")

    candidate = ROOT / "provenance/candidate-fixture.json"
    load = read(ROOT / "load-probe/report.json")
    assert load["passed"] and load["model_calls"] == 0
    assert load["fixture"]["manifest_sha256"] == sha(candidate)
    assert load["fixture"]["source_episode_tic"] == load["fixture"]["after_load_tic"] == 1366
    assert load["initial_observation"]["sequence"] == 1 and load["initial_observation"]["exact"]
    assert sha(ROOT / "load-probe/initial.png") == load["initial_image_sha256"]
    assert not load["score"]["player_dead"]

    reader = DoomStatusNumberReader(REPO / "_vizdoom/vizdoom/freedoom2.wad",
                                    image_resolver=lambda value: ROOT / Path(value).name)
    source_signal = reader.read(fixture["source_observation"])
    loaded_observation = dict(load["initial_observation"])
    loaded_observation["image"] = "initial.png"
    loaded_reader = DoomStatusNumberReader(
        REPO / "_vizdoom/vizdoom/freedoom2.wad",
        image_resolver=lambda value: ROOT / "load-probe" / Path(value).name)
    loaded_signal = loaded_reader.read(loaded_observation)
    assert source_signal["status"] == loaded_signal["status"] == "observed"
    assert source_signal["value"] == 100 and loaded_signal["value"] == 97

    review = read(ROOT / "review.json")
    assert review["threat_exposed"] is True and review["visible_enemy_count_lower_bound"] >= 1
    assert review["source_health"] == source_signal["value"]
    assert review["loaded_health"] == loaded_signal["value"]
    assert review["source_ammo"] == review["loaded_ammo"] == 48
    assert review["source_frame_sha256"] == sha(ROOT / "source.png")
    assert review["loaded_frame_sha256"] == sha(ROOT / "load-probe/initial.png")

    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]
    audit = {
        "schema": "map01_threat_fixture_audit_v2",
        "passed": True,
        "disposition": "PROMOTED_DISTINCT_THREAT_FIXTURE",
        "fixture_id": manifest["fixture_id"],
        "parent_fixture_id": "map01-threat-contact-v1",
        "parent_episode_tic": 1263,
        "episode_tic": 1366,
        "source_frame_differs_from_parent": True,
        "build_model_calls": 0,
        "build_os_input_programs": 2,
        "verified_build_releases": 2,
        "fresh_process_load": True,
        "loaded_tic_matches_source": True,
        "source_exact_health": 100,
        "loaded_exact_health": 97,
        "source_and_loaded_visible_enemy_reviewed": True,
        "source_and_loaded_ammo": 48,
        "credential_pattern_matches": 0,
        "authority": "benchmark start-state evidence only; grants no runtime input authority",
        "limits": prereg["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
