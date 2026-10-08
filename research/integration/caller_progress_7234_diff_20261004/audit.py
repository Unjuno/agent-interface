#!/usr/bin/env python3
"""Independent checks over the saved source-bound regression outputs."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
candidate = json.loads((HERE / "CANDIDATE_ROWS.json").read_text())
control = json.loads((HERE / "CURRENT_MAIN_ROWS.json").read_text())
hashes = json.loads((HERE / "SOURCE_HASHES.json").read_text())

assert hashes["main_commit"] == "abb6f6f9c71f7c61db77070f0ced3c4bc2439dcd"
assert hashes["candidate_commit"] == "52d6b295c68e6c175d25aa9f52a58936c341983f"
assert hashes["current_main_sha256"] == "8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca"
assert hashes["candidate_sha256"] == "77cf5905c48ff4302d32007eeff5e75fcdbd5b2c5d88b00ec8d3def51b529130"
assert hashes["candidate_test_sha256"] == {
    "test_adaptive_acquisition_caller_terminal_v3.py": "014c79a5e6d9ce717196439a754c4e5cf76a347a77cd6cd9dd7a1109f21915cb",
    "test_adaptive_acquisition_caller_v3.py": "99e231fe9ed1c16b278785900213ec7e6272040df1a84df0ae8062f9860da693",
    "test_adaptive_acquisition_caller_verify_progress_v3.py": "e1db4b4c76481c4b53f221a607ed0cfcd1ec7d0ad5e56c510a936bed4155634e",
}

assert len(candidate) == 4
for row in candidate:
    effect = row["effect"]
    failed_journal = row["journal_fails"]
    result = row["result"]
    assert effect in {"failed", "unavailable"}
    assert result["execution_progress"] == {"status": "completed"}
    assert result["task_effect"] == effect
    assert result["delivery"] == "confirmed"
    assert result["outcome"] == ("CALLER_FAILED" if failed_journal else "TASK_NOT_VERIFIED")
    assert result["input_authority"] == "consumed_by_recorded_execute_stage"
    assert row["calls"] == ["execute", "verify"]
    assert sum(event["event"] == "adaptive_route_finished" for event in row["events"]) == 1
    assert result["accounting"]["attempted_calls"] == 0

assert len(control) == 2  # Both healthy-journal current-main subcases reach assertions.
assert {row["effect"] for row in control} == {"failed", "unavailable"}
assert all(row["result"]["execution_progress"] is None for row in control)

for name, marker in (("candidate-normal.txt", "Ran 14 tests"),
                     ("candidate-optimized.txt", "Ran 14 tests"),
                     ("CURRENT_MAIN_CONTROL.txt", "FAILED (failures=2, errors=2)")):
    assert marker in (HERE / name).read_text()

print("PASS_SOURCE_REGRESSION_SCOPED: candidate 4/4 rows retained progress; main 2/2 healthy controls omitted it; candidate 14/14 in both Python modes; main control 2 failures + 2 journal-path errors.")
