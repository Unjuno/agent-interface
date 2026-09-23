import json, pathlib, sys

def main(path):
    rows = json.loads(pathlib.Path(path).read_text())["rows"]
    assert len(rows) == 12
    expected = {"complete_current": True, "stale": False, "partial": False, "wrong_region": False, "ambiguous": False, "forged_xid": False}
    for row in rows:
        assert row["gate"]["admitted"] is expected[row["case"]]
        if not expected[row["case"]]:
            assert row.get("input_emitted", 0) == 0
    assert {r["app"] for r in rows} == {"app_a", "app_b"}
    assert all(r["effect_present"] for r in rows if r["case"] == "complete_current")
    print("PASS_O3_SOURCE_WINDOW_FIX_REVALIDATED_SCOPED rows=12 apps=2 denied_emissions=0 mutation_controls=5")
if __name__ == "__main__":
    main(sys.argv[1])
