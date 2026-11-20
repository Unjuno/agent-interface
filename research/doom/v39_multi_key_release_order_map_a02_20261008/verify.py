"""Independent permutation/identity audit; does not import candidate helpers."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_SOURCE = "2c5304bd246118f8124d5f7b50b81f869fb35ea3ee76887f4682748fdf95618a"


def main():
    source = (ROOT / "session_map01_v19.py").read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED_SOURCE
    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    assert result["source"]["sha256"] == EXPECTED_SOURCE
    assert result["source"]["head"] == "7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e"
    assert result["identity_fields"] == ["id", "step", "owner_id", "intent_token",
                                         "key", "actuation_id"]
    mutations = result["mutation_checks"]
    assert len(mutations) == 10
    assert all(value is True for value in mutations.values())
    assert len(result["cases"]) == 3
    for case in result["cases"]:
        n = case["key_count"]
        keys = tuple(chr(ord("A") + i) for i in range(n))
        expected = {(tuple(a), tuple(r)) for a in itertools.permutations(keys)
                    for r in itertools.permutations(keys)}
        schedules = case["schedules"]
        observed = {(tuple(row["admission_order"]), tuple(row["release_order"]))
                    for row in schedules}
        assert observed == expected
        assert len(schedules) == len(expected) == case["schedule_count"]
        for row in schedules:
            assert row["matched"] is True
            assert row["candidate_down_key"] == row["candidate_up_key"]
            assert row["candidate_up_key"] == row["release_order"][-1]
            assert row["held_after"] == []
            assert row["ambiguous"] is False
        assert case["matched"] == len(expected)
        assert case["censored"] == 0
        assert case["match_rate"] == 1.0

    # Independent identity mutation oracle: one missing or changed identity field
    # must not produce a valid pair, even with an empty held set.
    identity = {"id": "p", "step": 1, "owner_id": "o", "intent_token": "i",
                "key": "A", "actuation_id": "a"}
    for field in identity:
        altered = dict(identity)
        altered[field] = None
        assert not _identity_valid(altered)
        changed = dict(identity)
        changed[field] = (changed[field] + "-changed"
                          if isinstance(changed[field], str)
                          else changed[field] + 1)
        assert _identity_valid(changed) and _identity_key(changed) != _identity_key(identity)
    assert not _identity_valid({**identity, "step": True})
    print("independent audit: PASS (41 schedules, 13 identity mutations, 3 event controls)")


def _identity_valid(row):
    expected = {"id": str, "step": int, "owner_id": str, "intent_token": str,
                "key": str, "actuation_id": str}
    return (type(row) is dict and set(row) >= set(expected) and
            all(type(row[field]) is kind for field, kind in expected.items()))


def _identity_key(row):
    return tuple(row[field] for field in
                 ("id", "step", "owner_id", "intent_token", "key", "actuation_id"))


if __name__ == "__main__":
    main()
