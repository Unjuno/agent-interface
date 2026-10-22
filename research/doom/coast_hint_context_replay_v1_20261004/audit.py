"""Independent integrity, timeline, and scope audit for replay output."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
report = json.loads((BASE / "report.json").read_text(encoding="utf-8"))
events = [json.loads(line) for line in (BASE / "events.jsonl").read_text(encoding="utf-8").splitlines()]
audit = json.loads((BASE / "audit-v2.json").read_text(encoding="utf-8"))
replay = json.loads((BASE / "coast-hint-exact-stream-replay.json").read_text(encoding="utf-8"))
assert audit["formal_pass"] is True and audit["completed"] is True
assert len(events) == 634
assert sum(row.get("event") == "typed_observation" for row in events) == 218
assert sum(row.get("event") == "observation" for row in events) == 218
assert replay["inputs"] == {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest()
                            for name in ("report.json", "events.jsonl", "audit-v2.json")}
assert replay["candidate_sha256"] == hashlib.sha256((BASE / "coast_hint_candidate.py").read_bytes()).hexdigest()
assert len(replay["decisions"]) == len(report["decisions"]) == 6
by_decision = {row["decision"]: row for row in replay["decisions"]}
for decision in report["decisions"]:
    result = by_decision[decision["iteration"]]
    assert result["final_admission"] == decision["final_action_admission"]["status"]
    source = next(row for row in events if row.get("event") == "observation" and
                  Path(row.get("image", "")).name == Path(decision["source_image"]).name)
    assert result["source_sequence"] == source["sequence"]
    for hint in result["historical_context"]:
        assert hint["grants_input_authority"] is False and hint["task_success_verified"] is False
        typed = next(row for row in events if row.get("event") == "typed_observation" and row.get("sequence") == hint["sequence"])
        full = next(row for row in events if row.get("event") == "observation" and row.get("sequence") == hint["sequence"])
        assert full.get("exact") is True
        assert all(typed.get(key) == full.get(key) for key in
                   ("id", "step", "sequence", "capture_ns", "pointer_binding", "frame_rgb_sha256"))
        assert all(typed["signals"][name]["value"] == hint[name]
                   for name in ("health", "ammo"))
        producers = [prior for prior in report["decisions"]
                     if prior["iteration"] < decision["iteration"]
                     and prior["cover_validity_admission"]["monitor_mode"] == "unauthored_coast_no_policy"
                     and prior["controller_model_started_ns"] < typed["emit_ns"] < prior["controller_model_ended_ns"]]
        assert producers, (decision["iteration"], hint["sequence"])
        assert typed["sequence"] < source["sequence"]

assert by_decision[1]["baseline_prior_soft_event_summary"] is None
assert [row["health"] for row in by_decision[1]["historical_context"]] == [97, 97, 97]
assert by_decision[3]["baseline_prior_soft_event_summary"] is None
assert [row["health"] for row in by_decision[3]["historical_context"]] == [76, 73]
assert by_decision[4]["baseline_prior_soft_event_summary"] is None
assert [row["health"] for row in by_decision[4]["historical_context"]] == [68, 68, 68]
assert all(not row["historical_context"] for row in (by_decision[0],))
print("PASS: hashes, retained audit, 634-event counts, exact joins, prior-coast provenance, no-authority flags, and all six admission outcomes")
