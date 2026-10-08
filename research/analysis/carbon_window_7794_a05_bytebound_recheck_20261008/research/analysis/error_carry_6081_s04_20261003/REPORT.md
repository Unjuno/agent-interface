# S04 formal result

Allocation: `ERROR-CARRY-6081-S04-WSLC-20261003-01`. This is a synthetic finite-method result only; it does not authorize live input or support transfer to a game, GUI, physical actuator, or arbitrary runtime.

## Outcome

The independent audit disposition is **PASS_METHOD_SCOPED**. All 5,379 preregistered rows (5,376 primary, 3 formal controls) were reconstructed from candidate raw output. The all-offered mean squared position error over requested prefixes was:

| Alphabet | Error carry | Horizon nearest | Independent stochastic rounding |
|---|---:|---:|---:|
| cardinal4 | 0.195527 | 6.700054 | 4.232029 |
| eightway8 | 0.088967 | 12.350773 | 8.984490 |
| pooled (descriptive only) | 0.145381 | 9.359216 | 6.468482 |

The endpoint uses all offered nonrepresentable linear requests and requested prefixes. Fail-closed refusals count as zero movement in the remaining prefixes. Error-carry completed all 504 cardinal4 and 448 eightway8 requests; nearest completed 304/504 and 256/448; independent rounding completed 401/504 and 293/448 due to the frozen one-unit coordinate envelope. The method gate is strict and passed in both alphabet strata and pooled.

The three formal controls returned their frozen refusal dispositions; the auditor's planted omitted-release mutation was rejected. The exact-representable control gate and command legality, prefix-envelope, deadlines, and release receipts passed. The held-out acceleration+wall dynamics produced a collision and is classified `HOLD_TRANSFER_UNSUPPORTED`; it is excluded from the linear endpoint.

## Execution and deviations

- WSLc 3.0.1.0, kernel 6.18.40.1-1; cached Python 3.12.14 amd64 image pinned by digest. Candidate ran once in its own offline disposable container and exited 0. It emitted 5,379 rows.
- The first independent auditor process ran once and exited 2 with `FAIL_AUDIT` due to an oracle bookkeeping bug: the non-request sentinel `omitted_release_mutation` in truth was incorrectly counted as a formal request/control. Raw data was preserved unchanged. The auditor was corrected to handle that sentinel as a mutation test, construction tests were rerun (9/9 pass), and a fresh, separate audit container was run once more. The corrected audit exited 0 with `PASS_METHOD_SCOPED`. Thus candidate retries: 0; auditor invocations: 2 (one retained failed oracle attempt, one corrected final audit). The run is not represented as a perfectly single-audit protocol.
- Both candidate/auditor WSLc invocations emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` CPU and memory limits were requested; swap/cgroup enforcement is unverified and is not claimed.
- Construction log also records an earlier wrong-working-directory host test invocation. It ran no candidate and the corrected host plus container construction suite passed.

## Reproduction and evidence

Frozen inputs and hashes are in `FREEZE.json`. Candidate raw, both auditor results, exact exit codes, and container/host stdout and stderr are retained under `formal-20261003/`. Candidate raw SHA-256: `1ca6ece5e70f908ddeea0369ff7be2a21066ec0e4befb56ce76c28ac76474644`. Final audit JSON SHA-256: `8cd080242b05403dad486f24127705831dc0411c4c806336d6e2505d1e552568`.

Re-run only in a new, explicitly allocated successor; do not overwrite this evidence. A future transfer study needs a separately frozen calibrated actuator model, observable intermediate path safety, latency/release semantics, and independent live effects. Synthetic PASS is not evidence for any of those.
