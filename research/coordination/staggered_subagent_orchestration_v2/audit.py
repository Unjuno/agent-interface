import hashlib, json, pathlib, sys

def main(root):
    p = pathlib.Path(root)
    data = json.loads((p / "RAW.json").read_text())
    rows = data["rows"]
    assert len(rows) == 108
    assert len({r["seq"] for r in rows}) == len(rows)
    condition = [r for r in rows if r["policy"] == "CONDITION_STAGGER"]
    assert not any(r["unsafe"] for r in condition)
    assert any(r["policy"] == "IMMEDIATE" and r["unsafe"] for r in rows)
    assert any(r["policy"] == "FIXED_STAGGER" and r["unsafe"] for r in rows)
    assert any(r["case"] == "independent_read" and r["policy"] == "CONDITION_STAGGER" and r["disposition"] == "started" for r in rows)
    required = {"admission_ts", "scheduled_ts", "actual_start_ts", "predecessor_id", "evidence_digest", "effect", "postcondition", "scheduler_overhead_ms", "completion_latency_ms"}
    assert required <= set(rows[0])
    assert (p / "MANIFEST.sha256").read_text().split()[0] == hashlib.sha256((p / "RAW.json").read_bytes()).hexdigest()
    transitions = {(r["case"], r["policy"], r["transition"]) for r in rows}
    assert len(transitions) == len(rows)
    print("PASS_STAGGERED_SUBAGENT_ORCHESTRATION_V2_SCOPED rows=108 condition_unsafe=0 integrity=1 transitions_unique=1")
if __name__ == "__main__":
    main(sys.argv[1])
