# R44 — WSLc 3.875 s pause under a 4 s transaction deadline

**Disposition: `FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN` (24/24 evidence checks).** The unchanged public standard-caller test failed once in the digest-pinned, network-disabled Ubuntu container. Xvfb paused for 3875.379 ms and resumed through its retained pidfd. The public cancel response took 312.743 ms; the transaction elapsed 4000.466 ms against its exact 4,000 ms deadline, overrun 0.466 ms. The supervisor release status was UNKNOWN (`unretired_or_late_supervisor`), `release_confirmed=false`, replay denied, and `task_success=null`.

The test stopped at the caller assertion. No independent release readback, late-event horizon, or task oracle was completed. The Xvfb process and exact container were removed. This is a single synthetic-Xvfb boundary probe, not a reliability estimate or evidence of Windows desktop, MAP01, real-app transfer, or matched efficiency. No retry was made.
