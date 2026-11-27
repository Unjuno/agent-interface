# R24 result — fresh Win32 generation after R23 recovery

## Decision

The frozen R24 trial outcome is `FAIL_OR_UNKNOWN` (10/14 strict audit checks).
The public dispatch returned `pending` after its 8,000 ms response wait. The
immediate public `interface_close` returned `busy` with
`release_confirmed=false`; the persisted session-close record later says
`closed`, also with `release_confirmed=false`. No replay, cancellation, or
second dispatch was attempted.

An additive audit of the already-written runtime report and independent fixture
records confirms that the same dispatch later completed, released all observed
keys and buttons with empty unknown sets, exited its producer with code 0, and
passed a neutral state readback. The independent fixture file and event journal
show exactly one click, all 26 expected character events, one save, and the
expected sentinel. The owned fixture exited with code 0 and the prior
foreground window was restored. This narrows the R24 result to a caller
response/close timing failure: it does not satisfy the frozen public-close
criterion, although the persisted action report documents eventual completion
and release.

## Timing

From the public dispatch start, the public pending response arrived at
8,004.047 ms; the independently journaled effect commit occurred at
8,799.587 ms; the verified release receipt was recorded at 8,823.826 ms; and
producer exit with neutral readback was recorded at 8,885.826 ms. The separate
effect-file read began after release and returned in 4.383 ms. These are one
fixture trial measurements, not a general latency bound.

The frozen raw field `release_receipt_returned_with_dispatch_monotonic_ns`
copies the public response timestamp, but the persisted runtime receipt places
release 819.780 ms later. The follow-up audit rejects that raw timing
annotation; use the persisted receipt's own monotonic timestamp for this
comparison.

## Scope and next decision

R24 demonstrates one new target generation and supervised public session after
R23, a matched public observation, one accepted action, independently verified
effect, and eventual all-up release. It does not demonstrate a timely public
completion response or close with release confirmation. Runtime `task_success`
remains null. The R23 raw/manifest hash discrepancy remains recorded in the
input-free preflight limitation; R23 is unchanged. No WSLc or Docker resource
was used.

The next discriminating experiment should use a fresh fixture, generation,
session, program ID, and sentinel, with a public result wait longer than the
observed 8.886 s producer completion (for example 12 s). Its probe must retrieve
and timestamp the public terminal report before closing, and must timestamp the
actual release receipt rather than infer it from dispatch return. R24 remains
immutable and is not retried.
