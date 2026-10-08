"""Audit a changed-seed five-tile L fixture without model evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
from guarded_l_score_v1 import contract_from_baseline, score


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(directory):
    return [
        json.loads(line.split("AIT ", 1)[1])
        for line in (directory / "stderr.txt").read_text().splitlines()
        if "AIT {" in line
    ]


def rejected(observation, baseline, mutate):
    candidate = copy.deepcopy(observation)
    mutate(candidate)
    try:
        score(candidate, baseline)
    except (ValueError, KeyError, TypeError):
        return True
    return False


def audit(root):
    manifest = json.loads((root / "manifest.json").read_text())
    for name, digest in manifest["sources"].items():
        assert sha(HERE.parent / name) == digest, name
    seed = manifest["seed"]
    assert seed == 991004
    old = json.loads((HERE / "results/l-geometry-01/audit.json").read_text())
    assert old["audit_passed"] and old["seed"] == 991003
    saved = root / "baseline.sav"
    save_digest = sha(saved)
    assert save_digest != old["save_sha256"]

    baseline = records(root / "restore-1")[0]
    contract = contract_from_baseline(baseline)
    assert contract["target"] != old["contract"]["target"]
    assert (contract["x"], contract["y"]) != (old["contract"]["x"], old["contract"]["y"])
    assert len(contract["target"]) == 5
    assert len(contract["forbidden"]) == 4
    assert len(contract["guard"]) == 49
    initial = score(baseline, baseline)
    assert initial == {
        "success": False,
        "checks": {
            "target_owned_roads": False,
            "ordered_bidirectional_connections": False,
            "forbidden_tiles_clear": True,
            "surrounding_road_owner_unchanged": True,
        },
        "changed_surrounding_tiles": [],
        "contract": contract,
    }

    expected = {key: value for key, value in baseline.items() if key != "stage"}
    counts = {}
    for phase in ("setup", "restore-1", "restore-2"):
        directory = root / phase
        result = json.loads((directory / "result.json").read_text())
        assert result["ready"] is True
        assert result["all_owned_processes_exited"] is True
        assert "error" not in result
        assert result["save_after"] == save_digest
        assert sha(directory / "screen.png") == result["screen_sha256"]
        if phase == "setup":
            assert result["save_created"] == save_digest
            assert result["target_contract"] == {
                "x": contract["x"], "y": contract["y"],
                "width": contract["width"], "target": contract["target"],
            }
        current = records(directory)
        assert current
        for observation in current:
            assert {key: value for key, value in observation.items() if key != "stage"} == expected
            assert score(observation, baseline)["success"] is False
        counts[phase] = len(current)

    assert rejected(baseline, baseline, lambda row: row["edges"].pop())
    assert rejected(baseline, baseline, lambda row: row["guard"].pop())
    assert rejected(
        baseline, baseline,
        lambda row: row["tiles"][0].update({"road": not row["tiles"][0]["road"]}),
    )
    assert rejected(baseline, baseline, lambda row: row.update({"x": row["x"] + 1}))
    observer = "\n".join(path.read_text() for path in sorted((HERE / "observer_l_v1").glob("*.nut")))
    for token in ("BuildRoad", "RemoveRoad", "BuildSign", "ScrollCompanyClients"):
        assert token not in observer
    return {
        "audit_passed": True,
        "scope": "changed L geometry fixture calibration; no model or task input after save",
        "seed": seed,
        "save_sha256": save_digest,
        "contract": contract,
        "prior_geometry": {
            "seed": old["seed"],
            "save_sha256": old["save_sha256"],
            "target": old["contract"]["target"],
        },
        "different_save": True,
        "different_origin": True,
        "different_target": True,
        "initial_checks": initial["checks"],
        "matching_observations": counts,
        "observer_mutation_tokens_absent": True,
        "malformed_controls": {
            "missing_edge_rejected": True,
            "missing_guard_rejected": True,
            "contradictory_overlap_rejected": True,
            "changed_geometry_rejected": True,
        },
        "all_owned_processes_exited": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    (args.root / "audit.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, indent=2))
