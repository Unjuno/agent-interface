"""Construction-only differential check for the #59 capture-availability boundary.

Predicates are transcribed from frozen T0 candidate.py and audit.py.
This is not a formal candidate/auditor invocation and deliberately performs no repair.
"""


def candidate(interval, available):
    lo, hi = interval
    if lo > available:
        return "YIELD_CAPTURE_NOT_AVAILABLE"
    if lo <= available < hi:
        return "YIELD_CAPTURE_ORDER_UNKNOWN"
    return "CONTINUE"


def independent_oracle(interval, available):
    lo, hi = interval
    if lo > available:
        return "YIELD_CAPTURE_NOT_AVAILABLE"
    if lo <= available <= hi:
        return "YIELD_CAPTURE_ORDER_UNKNOWN"
    return "CONTINUE"


CASES = [
    ("strictly_before", [80, 99], 100),
    ("touches_upper_endpoint", [80, 100], 100),
    ("point_at_decision", [100, 100], 100),
    ("straddles", [99, 101], 100),
    ("strictly_after", [101, 102], 100),
]


def main():
    rows = []
    for name, interval, available in CASES:
        got = candidate(interval, available)
        want = independent_oracle(interval, available)
        rows.append((name, got, want, got == want))
    for row in rows:
        print("\t".join(map(str, row)))
    mismatches = sum(not row[3] for row in rows)
    print(f"cases={len(rows)} mismatches={mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
