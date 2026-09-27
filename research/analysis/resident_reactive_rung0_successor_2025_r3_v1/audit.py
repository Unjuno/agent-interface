import json

def expected_edges(trace):
    return sum(1 for i,state in enumerate(trace) if state and (i == 0 or not trace[i-1]))

def main():
    with open("RESULT.json", encoding="utf-8") as f:
        rows=json.load(f)["rows_detail"]
    assert len(rows) == 64
    for row in rows:
        trace=tuple(row["trace"]); expected=expected_edges(trace)
        effects=[event for event in row["resident"] if event[0] == "effect"]
        assert len(effects) == expected
        assert row["stale_rejections"] == 1
        assert row["resident"][-1] == ["release", 4, 1]
        assert row["valid"] is True
    assert sum(row["stale_rejections"] for row in rows) == 64
    print("independent_audit=PASS rows=64 stale_rejections=64 terminal_release=PASS")
if __name__ == "__main__": main()
