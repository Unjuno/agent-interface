#!/usr/bin/env python3
import json
from pathlib import Path
from policy import classify_actor, validate_reclaim

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    result = load("result.json")
    control = load("register_control.json")
    other = load("register_other.json")
    same = load("register_same.json")

    assert classify_actor(control, {"owner_id": "owner-A-007", "generation": 1}) == {
        "disposition": "CURRENT_OWNER", "write": True
    }
    assert validate_reclaim(
        {"owner_id": "owner-A-007", "generation": 1},
        {"owner_id": "owner-B-007", "generation": 2},
        True,
    )
    assert validate_reclaim(
        {"owner_id": "owner-A-007", "generation": 1},
        {"owner_id": "owner-A-007", "generation": 2},
        True,
    )
    assert classify_actor(other, {"owner_id": "owner-A-007", "generation": 1}) == {
        "disposition": "FENCED_STALE", "write": False
    }
    assert classify_actor(same, {"owner_id": "owner-A-007", "generation": 1}) == {
        "disposition": "FENCED_STALE", "write": False
    }

    assert result["totals"]["old_generation_409_rejections"] == 2
    assert result["totals"]["fenced_stale_decisions"] == 2
    assert result["totals"]["fresh_sha_retries_by_fenced_writer"] == 0
    assert result["decision"] == "PASS_GENERATION_FENCE_SCOPED"
    print("PASS_GENERATION_FENCE_SCOPED")


if __name__ == "__main__":
    main()
