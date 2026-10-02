# Formal result — Issue #5694 T0

**Disposition: PASS_METHOD_SCOPED** — the frozen independent auditor accepted all eight synthetic scenarios with no errors. This is not live-controller, product, safety, or Issue #59 evidence.

## Primary inversion

The same three exogenous windows were used for both arms. Dense completed-cycle p95 was 30 ms and all 3/3 opportunities received a useful effect. Sparse p95 was 5 ms, yet only 2/3 opportunities were met: O2 expired entirely during the declared busy interval [5,210) and was retained as MISS. First useful-effect latencies were dense {35,35,35} ms and sparse {10,null,20} ms. Longest uncovered opportunity-window gaps were 35 ms and 80 ms, respectively. The no-stall control had 3/3 useful effects in both arms.

## Other frozen controls

- Safe stop remained SAFE_STOP, not a useful effect.
- Complete observation through expiry yielded MISS; right censoring yielded UNKNOWN.
- Overlapping opportunities were matched from event region/time: both-region effects met both A and B, while B-only effects did not meet A.
- Unsynchronized clocks preserved local completed-cycle p95 (5 ms) but withheld opportunity outcomes as UNKNOWN and the uncovered-gap summary as null.
- Zero exogenous opportunities were NOT_APPLICABLE, with zero denominator.

## Execution and integrity

- Construction: 12/12 unittest checks passed; py_compile passed.
- Frozen candidate: invoked once; raw output 3,335 bytes, SHA-256 b5a60694fbce4361bf2e9ac508b162eea498fb4dba157a083b62b8b379b69bba.
- Frozen auditor: invoked once in a separate process; exit 0; audit output 3,519 bytes, SHA-256 4a80bd8849b4cfe2b039b3501245aa1aab6629bcc157ca72165b18f0eb32a771.
- Candidate stdout/stderr and auditor stderr were empty; auditor stdout is the same JSON as audit.json.
- Candidate exit status was not captured reliably across the Windows-to-WSL shell boundary; successful raw generation and the subsequent independent audit are observed. Candidate was not retried.
- Frozen source hashes are listed in SHA256SUMS; FREEZE.json SHA-256 is 24437c35492f53f0532a985ee95f77dff9cca3889318c4866c8187354aa7bc5a.
- Local CPython 3.12.3, standard library only. Docker Desktop was checked but unusable (Windows read-only probe timed out at 5 seconds; WSL Docker context reported protocol unavailable). No containers or shared queue resources were used or modified.

## Limits and next step

This proves only that the frozen ledger distinguishes these authored finite traces. It does not prove that any existing benchmark exhibits coordinated omission, that real cues are exogenous, that region/effect annotations are valid, or that a live agent's safety or usefulness changes. No latency correction or posthoc MAP01 regrading follows. A live transfer needs prospectively scheduled exogenous cues, aligned clocks, and an independent task-effect oracle. Keep this result separate from Issue #59's live-control evidence gap.