# R45 result — 2026-10-24

**Disposition: FAIL_OR_UNKNOWN; phase 2 was correctly not started.** This is one new native-Windows standard-caller attempt, frozen as `win32-supervised-recovery-fresh-generation-task-20261024-r45-5f1e0c03c59e4455bcec72ca3dbf6797`. No retry, threshold change, or phase-2 task was made.

The input-free preflight passed 12/12 checks on main `e6192a4294aac0d94d51e75b24583216c718d654`. The exact fixture foreground receipt matched the returned CUA window and independently observed foreground HWND. One public dispatch and one cancel were issued. A same-generation reader confirmed Q-down before cancel; the callback stayed blocked while the caller made 79 exact-call polls. After cancel returned, the exact recovery Q-up `SendInput` returned at +617.6489 ms and the independent same-generation sampler collected 59 eligible Q-up samples while the callback remained held.

The frozen strict release audit passed 10/11 checks. The held callback returned 1,245.0446 ms after the cancel response, 4.9554 ms short of the preregistered 1,250 ms minimum. This single gate failure prevents phase 2 under the frozen runner. Producer and observer retired, the fixture exited with code 0, the public session closed, and the original foreground was restored. The runtime task outcome is unknown/null; there is no task-oracle result for R45.

The frozen combined auditor reports 1/13 because its phase-2 checks are also false when phase 2 is absent. The additive raw-only interpretation audit records 8/8 evidence-integrity and stop-rule checks, while preserving the scientific disposition as FAIL_OR_UNKNOWN and phase 2 as NOT_STARTED. Neither audit changes the first outcome. The attempt did not reach the new fixture write-timing instrumentation, so it adds no effect-latency evidence.

The unique attempt ID is R45; the inherited phase-1 program and lease labels still contain `r44`. This naming reuse is retained as a setup-quality note and is not hidden by the new attempt ID. Per-call IDs and target generation are retained in raw. Do not pool this run with R44 or treat it as a reliability estimate.

Raw, frozen conditions, source hashes, audit outputs, exact-call receipts, independent state samples, cleanup evidence, and both auditors are retained beside this result. `SHA256SUMS` covers the packet. WSLc/Docker, MAP01, matched efficiency, and provider/model usage were not involved.
