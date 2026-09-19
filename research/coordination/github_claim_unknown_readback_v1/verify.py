#!/usr/bin/env python3
"""Offline verifier for retained unknown-readback evidence; no GitHub I/O."""
import json
from pathlib import Path
import policy

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    plan = load("plan.json")
    result = load("result.json")
    by_name = {c["name"]: c for c in result["cases"]}

    assert result["decision"] == "PASS_BOUNDED_UNKNOWN_READBACK_SCOPED"
    assert result["measurement"]["recovery_put_count"] == 0
    assert result["measurement"]["later_full_get_count"] == 3
    assert result["measurement"]["second_later_get_count"] == 0
    assert result["measurement"]["elapsed_time_used_as_evidence"] is False

    for case in plan["cases"]:
        retained = by_name[case["name"]]
        first = policy.classify_first(case["first_observation"])
        assert first == {"classification": case["expect_first"], "write": False}
        assert retained["first_classification"] == case["expect_first"]
        assert retained["first_write"] is False

        register = load(case["register_path"])
        full = policy.classify_full(case["candidate"], register)
        assert full == {"classification": case["expect_final"], "write": False}
        assert retained["final_classification"] == case["expect_final"]
        assert retained["later_get_blob"] == retained["payload_blob"]
        assert register == load(case["payload_path"])

    print("PASS_BOUNDED_UNKNOWN_READBACK_SCOPED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
