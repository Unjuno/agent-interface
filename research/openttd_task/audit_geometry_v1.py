"""Audit the new OpenTTD geometry fixture without launching the model loop."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
from guarded_score_v2 import score


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    return [
        json.loads(line.split("AIT ", 1)[1])
        for line in (path / "stderr.txt").read_text().splitlines()
        if "AIT {" in line
    ]


def audit(root):
    manifest = json.loads((root / "manifest.json").read_text())
    for name, digest in manifest["sources"].items():
        assert sha(HERE.parent / name) == digest, name
    plan = manifest["plan"]
    assert plan["seed"] == 991002
    saved = root / "baseline.sav"
    save_digest = sha(saved)
    setup = records(root / "setup")
    restored = records(root / "restore-1")
    assert setup and restored
    setup_record = setup[0]
    baseline = restored[0]
    assert {
        key: setup_record[key]
        for key in ("x", "y", "width", "tiles", "edges")
    } == {
        key: baseline[key]
        for key in ("x", "y", "width", "tiles", "edges")
    }
    initial = score(baseline, baseline)
    assert initial["success"] is False
    assert initial["checks"] == {
        "target_owned_roads": False,
        "bidirectional_connections": False,
        "forbidden_row_clear": True,
        "surrounding_road_owner_unchanged": True,
    }
    assert initial["changed_surrounding_tiles"] == []
    assert initial["contract"]["target"] != [678, 679, 680]
    expected = {key: value for key, value in baseline.items() if key != "stage"}
    phases = {}
    for phase in ("setup", "unsaved", "restore-1", "restore-2"):
        directory = root / phase
        result = json.loads((directory / "result.json").read_text())
        assert result["all_owned_processes_exited"] and "error" not in result
        assert sha(directory / "screen.png") == result["screen_sha256"]
        assert result["save_after"] == save_digest
        if phase == "setup":
            assert result["save_created"] == save_digest
            assert result["target_contract"]["target"] == initial["contract"]["target"]
        else:
            assert result["save_before"] == save_digest
        if phase == "unsaved":
            assert result["ready"] is False
            assert records(directory) == []
            assert "AIT_ERROR saved contract required" in (directory / "stderr.txt").read_text()
            continue
        current = records(directory)
        assert current
        if phase == "setup":
            phases[phase] = len(current)
            continue
        for observation in current:
            assert {key: value for key, value in observation.items() if key != "stage"} == expected
            assert score(observation, baseline)["success"] is False
        phases[phase] = len(current)
    old_save = HERE / "results/cohort-03/baseline.sav"
    assert sha(old_save) != save_digest
    observer = "\n".join(path.read_text() for path in sorted((HERE / "observer_v2").glob("*.nut")))
    for token in ("BuildRoad", "RemoveRoad", "BuildSign", "ScrollCompanyClients"):
        assert token not in observer
    return {
        "audit_passed": True,
        "scope": "new geometry fixture preparation; no model or shared-runtime task control",
        "seed": 991002,
        "save_sha256": save_digest,
        "different_from_old_save": True,
        "contract": initial["contract"],
        "initial_checks": initial["checks"],
        "matching_observations": phases,
        "unsaved_observer_rejected": True,
        "observer_mutation_tokens_absent": True,
        "all_owned_processes_exited": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    (args.root / "audit.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, indent=2))
