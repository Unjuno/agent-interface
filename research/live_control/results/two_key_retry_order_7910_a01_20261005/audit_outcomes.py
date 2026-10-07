"""Independent consistency audit of the frozen two-key synthetic outcome."""
import json
from pathlib import Path

result = json.loads((Path(__file__).parent / "outcomes.json").read_text(encoding="utf-8"))
trace = result["trace"]
assert trace["admission_up"] == [74, 65]
assert trace["explicit_deliveries"] == "both dropped by fake display"
assert trace["cleanup_retry_up"] == [65, 74]
assert trace["cleanup_retry_up"] != trace["admission_up"]
assert trace["terminal_down"] == []
assert trace["verified"] is True
runs = {run["label"]: run for run in result["runs"]}
assert runs["current-main baseline normal"]["exit_code"] == 1
assert runs["current-main baseline optimized"]["exit_code"] == 1
assert runs["candidate normal"]["exit_code"] == 0
assert runs["candidate optimized"]["exit_code"] == 0
assert all(runs[label]["disposition"] == "PASS"
           for label in ("candidate normal", "candidate optimized"))
print("PASS: raw dispositions and candidate fake-X release-order trace are internally consistent")
print("LIMIT: this auditor verifies retained synthetic evidence only; no live/X11/task-effect claim")
