# R42 — WSLc 3.9 s boundary probe under a 4 s transaction deadline

**Disposition: `FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN`.** The unchanged public standard-caller test failed once at its cancel assertion. Xvfb was paused for 3900.348 ms and resumed through its retained pidfd. The public cancel call returned in 313.868 ms, but the cancellation transaction completed 4004.988 ms after admission, 4.988 ms beyond its exact 4,000 ms deadline. The owner release worker and client disconnect status were `UNKNOWN` with reason `transaction_deadline`; `release_confirmed=false`, replay remained denied, and `task_success=null`.

The test stopped at that assertion. It produced no independent release readback, late-event horizon, old-task oracle, or fresh-generation task oracle. The exact Xvfb process and container were removed. Destroying the private synthetic X server is environment teardown, not an agent release receipt, so the runtime state remains UNKNOWN. Evidence-integrity checks: 24/24; raw output and the full caller assertion are retained here. No retry was made.

## Scope

R40 and R41 passed 3,800 ms holds with 76.372 and 72.300 ms release margins. R42 at 3,900 ms exceeded its transaction deadline by 4.988 ms and the public caller test failed. This single synthetic-Xvfb result bounds the tested 4 s transaction for this host/runtime; it is not a general reliability estimate and does not establish Windows desktop, MAP01, real-app transfer, or matched efficiency.
