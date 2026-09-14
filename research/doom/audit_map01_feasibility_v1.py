"""Audit retained continuously advancing MAP01 feasibility evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


parser = argparse.ArgumentParser()
parser.add_argument("result", type=Path)
args = parser.parse_args()
root = args.result.resolve()
events = rows(root / "events.jsonl")
report = read(root / "report.json")
score = read(root / "score.json")
sources = read(root / "sources.json")

assert report["passed"] is False
assert report["claim"] == "pre-formal exploration failure"
assert score["map"] == "MAP01" and score["map_exit"] is False
assert report["score"] == score
assert report["input_admissions"] == sum(row["event"] == "input_admission" for row in events)
assert report["accepted_programs"] == sum(row["event"] == "accepted" for row in events)
assert report["rejected_commands"] == sum(row["event"] == "rejected" for row in events)
assert all(row.get("focus_samples_match", True) for row in events)
assert any(row["event"] == "clock_probe" and row["no_advance_calls_during_wait"] for row in events)
assert any(row["event"] == "post_control_score" and
           all(row.get(key) == value for key, value in score.items()) for row in events)

repo = Path(__file__).resolve().parents[2]
for relative, expected in sources.items():
    candidate = repo / "research" / relative
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == expected, relative

result = {
    "audit_passed": True,
    "result": root.name,
    "input_admissions": report["input_admissions"],
    "accepted_programs": report["accepted_programs"],
    "observations": sum(row["event"] == "observation" for row in events),
    "map_exit": score["map_exit"],
    "player_dead": score["player_dead"],
    "continuous_wall_seconds": score["wall_control_ns"] / 1e9,
}
(root / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
