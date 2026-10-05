"""Independent raw-output classification for the finite sink-boundary probe."""
import ast
from pathlib import Path
import re

raw = Path(__file__).with_name("RAW_STDOUT.txt").read_text(encoding="utf-8").splitlines()
cases = {}
for line in raw[1:]:
    match = re.fullmatch(
        r"accept_before_raise=(True|False) fail_position=([0-2]) observed=(.+)", line
    )
    assert match, f"malformed raw case: {line}"
    accepted = match.group(1) == "True"
    position = int(match.group(2))
    rows = ast.literal_eval(match.group(3))
    cases[(accepted, position)] = rows

assert len(cases) == 6
for position in range(3):
    rejected_rows = cases[(False, position)]
    assert position not in [row[0] for row in rejected_rows]
    assert sorted(row[0] for row in rejected_rows) == [i for i in range(3) if i != position]
    ambiguous_rows = cases[(True, position)]
    accepted = [row for row in ambiguous_rows if row[0] == position]
    assert accepted == [(position, True, "accepted_then_raise")]
    assert all(row[2] != "delivery_unknown" for row in ambiguous_rows)

print("PASS_AUDIT: 6/6 cases; rejected row absent in all fail-before-accept cases;")
print("accepted-then-raise rows appear as complete but no delivery-unknown status exists.")
