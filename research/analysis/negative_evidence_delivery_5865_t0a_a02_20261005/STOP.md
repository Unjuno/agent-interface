# A02 disposition: STOP — independent auditor error

The frozen candidate ran once and wrote `run-01`. The independent auditor was
invoked once and exited with `KeyError: 'A'` at `audit_result.py:211` while
applying the failure-cooldown mutation control. The frozen output represents
the route failure snapshot as an empty map (`failure_snapshot: {}`), while the
auditor assumes a nested route entry exists. No audit JSON was produced.

Candidate invocations: 1. Auditor invocations: 1. Retries: 0. No scientific
PASS/FAIL disposition is assigned: the candidate output remains unaudited and
cannot support a promoted result. Frozen files and the first candidate output
are preserved unchanged. Do not rerun this allocation. Any successor must have
a distinct allocation identity and independently repaired controls before its
own freeze.

Candidate output SHA-256:

- `events.jsonl`: `7801f3ed49bb5e720ee158b3bf08472c636aad029a1716de0a608cb38e8965ba`
- `results.json`: `a2ed0f25decdf4f7bed2f51e7845c854659050920f6c4ae92b6ebb5eb396560e`
