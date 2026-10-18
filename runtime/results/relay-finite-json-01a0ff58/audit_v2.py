"""Independent raw-only audit against the authored finite/numeric case oracle."""
import copy
import hashlib
import json
from pathlib import Path


def verify(raw, cases, root):
    assert raw["cases_sha256"] == hashlib.sha256((root / "cases.json").read_bytes()).hexdigest()
    assert raw["sources"] == {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (root / "source").glob("*.py")}
    expected = {(variant, case["name"]): case
                for variant in ("baseline", "candidate") for case in cases}
    assert len(raw["rows"]) == len(expected)
    seen = set()
    for row in raw["rows"]:
        key = (row["variant"], row["case"])
        assert key not in seen
        seen.add(key)
        case = expected[key]
        dispatch = case["baseline_dispatch"] if key[0] == "baseline" else case["finite"]
        assert row["line"] == '{"id":1,"tool":"interface_dispatch","arguments":{"value":' + case["literal"] + '}}'
        response = row["response"]
        followup = row["same_id_followup"]
        assert type(row["call_count"]) is int and row["call_count"] == int(dispatch)
        assert type(response["next_id"]) is int and response["next_id"] == (2 if dispatch else 1)
        assert response["status"] == ("returned" if dispatch else "refused")
        assert followup["status"] == ("refused" if dispatch else "returned")
        assert type(followup["next_id"]) is int and followup["next_id"] == 2
        assert type(row["total_calls"]) is int and row["total_calls"] == 1
        if dispatch:
            assert type(response["id"]) is int and response["id"] == 1
            assert response["tool"] == "interface_dispatch"
        else:
            assert type(followup["id"]) is int and followup["id"] == 1
            assert followup["tool"] == "interface_dispatch"
        if dispatch and case["finite"]:
            expected_value = json.loads(case["literal"])
            assert row["received_json"] == json.dumps({"value":expected_value}, allow_nan=False, sort_keys=True)
            assert row["serialization"] == "finite"
        else:
            assert row["received_json"] is None
            assert row["serialization"] == ("nonfinite" if dispatch else "not_dispatched")
        if not dispatch:
            assert response["dispatched"] is False
    assert seen == set(expected)


def main():
    root = Path(__file__).resolve().parent
    cases = json.loads((root / "cases.json").read_bytes())
    raw_bytes = (root / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    verify(raw, cases, root)
    mutations = []
    for name, mutate in [
        ("missing_row", lambda r:r["rows"].pop()),
        ("duplicate_row", lambda r:r["rows"].__setitem__(0, r["rows"][1])),
        ("false_refusal", lambda r:r["rows"][0]["response"].__setitem__("status", "refused")),
        ("consumed_refusal_id", lambda r:r["rows"][16]["response"].__setitem__("next_id", 2)),
        ("changed_source", lambda r:r["sources"].__setitem__("candidate_relay.py", "0"*64)),
        ("boolean_call_count", lambda r:r["rows"][0].__setitem__("total_calls", True)),
        ("boolean_request_id", lambda r:r["rows"][0]["response"].__setitem__("id", True)),
        ("wrong_followup_id", lambda r:r["rows"][0]["same_id_followup"].__setitem__("next_id", 9)),
    ]:
        changed = copy.deepcopy(raw)
        mutate(changed)
        try:
            verify(changed, cases, root)
        except (AssertionError, KeyError, ValueError):
            mutations.append({"case":name, "rejected":True})
        else:
            raise AssertionError("mutation accepted: " + name)
    print(json.dumps({"status":"PASS_CONSTRUCTION_SCOPED", "rows":len(raw["rows"]),
                      "raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),
                      "mutations":mutations}, indent=2))


if __name__ == "__main__":
    main()
