# Run record — BELIEF-RECOVERY-8527-T0-A02-20261008

## Pre-run state

- Allocation/source freeze: commit a2677e890f9cd1910f061da3fc29c4a40f408ea5, based on current-main snapshot a94da2c520edf566f615b1b909d5ed590a35c8f3; code/input/oracle bytes match FREEZE.json and SHA256SUMS.
- Candidate formal invocations: 0.
- Independent auditor formal invocations: 0.
- Retries: 0.
- Container invocations for this allocation: 0.
- Formal disposition: NOT_STARTED; shared WSLc ownership/exclusive-lane clearance is pending.
- This is not a scientific PASS, FAIL, STOP result, nor a completed readiness smoke.

## Construction evidence (separate from the allocation)

Windows CPython 3.12.10:

- Normal construction tests: 10/10 passed.
- Optimized-Python construction tests: 10/10 passed.
- Candidate and auditor functions were exercised only as unit-test dependencies. Neither formal CLI entry point was invoked.

The prior #8527 A01 construction outcome/STOP is unchanged. No container was started for A02.

## Start authorization boundary

The issue-specific instruction requires a separately available authorized isolated CPU lane. Current WSLc process absence is only a point-in-time observation and does not resolve prior container/session ownership. Proceed only after the user explicitly releases the shared WSLc lane or the governing owners record an equivalent clearance. If cleared, run the frozen candidate once and, only after exit 0 with its exclusive raw output present, the independent auditor once. Any first formal failure is terminal; no retry.
