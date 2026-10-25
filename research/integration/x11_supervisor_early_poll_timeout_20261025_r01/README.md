# X11 prestarted supervisor early-poll timeout R01

## Question

Does the prestarted cancellation supervisor incorrectly retire a completed worker when a pipe `poll(timeout)` reports `False` early, before its absolute transaction deadline?

## Source and change

- Source: current `main` before this change, `0803a9792cc4a2a2ba61d513c82d0ecab104303a`.
- A deterministic wrapper around the real result pipe returns `False` on its first poll, then delegates to the pipe. The worker has a 2 s absolute deadline and returns an accepted result immediately.
- Before the fix, the new test failed with `status=unknown`, `reason=transaction_deadline`, `worker_retired=true`, and exit code `-15`, although the deadline had not elapsed.
- `PrestartedCancellationSupervisor.run` now recomputes remaining time against the absolute monotonic deadline and polls again after a bounded 1 ms pause. It retires the one-shot worker only after the deadline is reached without a result.

## Verification

- New deterministic regression: 1/1 PASS under Python 3.13.14.
- `runtime.guarded_x11_v1.test_cancel_supervisor`: 13/13 PASS in normal and optimized mode.
- `runtime.cli_v1.test_mcp_owned_process`: 48/48 PASS in normal and optimized mode.
- `git diff --check`: PASS.

This injects an early `False` response to exercise the deadline boundary. It does not claim that a particular native Windows pipe actually returned early on this host. It is synthetic cancellation-supervisor evidence, not physical input release, task effect, WSLc/MAP01 portability, matched efficiency, or reliability. No WSLc or Docker operation was performed.

## Decision

Adopt the absolute-deadline recheck because a transient early timeout must not be misclassified as expiration. Keep all receipts UNKNOWN if no worker result arrives by the absolute deadline; this change does not grant extra time beyond that deadline.
