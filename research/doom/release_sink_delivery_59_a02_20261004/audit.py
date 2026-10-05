"""Independent classification of the six retained candidate ledger rows."""
import json
from pathlib import Path

lines = Path(__file__).with_name("RAW_STDOUT.txt").read_text(encoding="utf-8").splitlines()
assert lines[0] == (
    "source_ref=1030a47894cb4f30a8c92bd577432e7962560741 "
    "source_path=research/doom/doom_owner_thread_release_batch_backend_v1.py "
    "blob=9bd000ad5614940f2bd59e3e5e8143b3a29a77b9"
)
cases = [json.loads(line) for line in lines[1:]]
assert len(cases) == 6
for case in cases:
    failed = case["failed_position"]
    states = [row["state"] for row in case["ledger"]["positions"]]
    expected = ["confirmed"] * failed + ["unknown"] + ["confirmed_incomplete"] * (2 - failed)
    assert states == expected, (case, expected)
    assert [row["position"] for row in case["ledger"]["positions"]] == [0, 1, 2]
    assert len([row for row in case["observed"]
                if row["sink_accept"] == "accepted_then_raise"]) == int(case["accept_before_raise"])
assert {(case["accept_before_raise"], case["failed_position"]) for case in cases} == {
    (accepted, position) for accepted in (False, True) for position in range(3)
}
print("PASS_AUDIT: 6/6 ledgers classify confirmed, unknown and confirmed_incomplete positions.")
