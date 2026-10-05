"""Strict raw-only audit of the retained six-case release-sink sweep."""
import ast
from pathlib import Path
import re


CASE_RE = re.compile(
    r"accept_before_raise=(True|False) fail_position=([0-2]) observed=(.+)"
)


def audit_text(text):
    lines = text.splitlines()
    if len(lines) != 7 or not lines[0].startswith("source_ref="):
        raise ValueError("expected one source header and exactly six case rows")

    cases = {}
    for line in lines[1:]:
        match = CASE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"malformed raw case: {line}")
        accepted_then_raise = match.group(1) == "True"
        fail_position = int(match.group(2))
        key = (accepted_then_raise, fail_position)
        if key in cases:
            raise ValueError(f"duplicate case: {key}")
        rows = ast.literal_eval(match.group(3))
        if not isinstance(rows, list):
            raise ValueError(f"observed rows are not a list: {key}")

        expected = []
        for position in range(3):
            if position == fail_position:
                if accepted_then_raise:
                    expected.append((position, True, "accepted_then_raise"))
            else:
                expected.append((position, position < fail_position, "delivered"))
        if rows != expected:
            raise ValueError(f"position/prefix/failure/suffix mismatch for {key}: {rows!r}")
        cases[key] = rows

    expected_keys = {(accepted, position) for accepted in (False, True) for position in range(3)}
    if set(cases) != expected_keys:
        raise ValueError(f"case matrix mismatch: {sorted(cases)}")
    return {"case_count": len(cases), "status": "PASS_RAW_POSITION_MATRIX"}


def main():
    path = Path(__file__).with_name("RAW_STDOUT.txt")
    result = audit_text(path.read_text(encoding="utf-8"))
    print(f"{result['status']}: {result['case_count']}/6")


if __name__ == "__main__":
    main()
