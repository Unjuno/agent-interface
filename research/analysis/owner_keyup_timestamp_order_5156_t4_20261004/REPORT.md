# Owner key-up adjacent timestamp order — Issue #5156 T4

## H / T / D / C / U

- **H:** Direct retained-input readiness should require `admitted_ns <= input_ack_ns <= release_call_started_ns <= release_call_returned_ns`.
- **T:** Against the exact main-frozen analyzer, four synthetic inputs: ordinary order and all-equal positives, plus ACK-before-admission and release-return-before-start negative controls. One candidate invocation and one independent raw-only auditor; both negative cases are distinct from the two inversions in the earlier Issue #5156 comment 5975206814.
- **D:** `PASS_ORDER_GATE_SCOPED` requires two positive readiness rows, two negative not-ready rows, reconciled bounds, and all four auditor controls. If malformed order is still marked ready and raw integrity passes, the disposition is `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED`.
- **C:** Frozen main `2f72c6474167f93a2e1a6e2b8a497a1a8a6d266a`; analyzer blob `f3d5fe315df8f4296351f1a5fc666d50ecaa6745`, SHA-256 `163a32ce20516bdfc034eb4c6659141e53e3ef11b8526372042fb5e9d509e63a`. Host Python 3.14.5, standard library. No container, GUI, X11, input, game, model, provider, GPU, or network. OrbStack image/container inspection failed on a containerd content blob with `operation not supported`; no pull, launch, or retry.
- **U:** Whether the frozen direct analyzer enforces these two remaining adjacent monotonic relations. This experiment does not establish owner-thread timing, physical key state, live MAP01 telemetry, application effect, safety, or task success.

## First outcome

The candidate exited 0 with four rows, all `measurement_ready=true`. The independent auditor exited 0 with `audit_status=PASS_RAW_AND_CONTROLS`, no integrity errors, and all 4/4 mutations rejected. It classified the two malformed inputs—`ack_before_admission` and `release_return_before_start`—as `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED`.

This is a construction-level finding against the direct analyzer's readiness classification only. It is not a live measurement or physical-input observation. T1–T3 STOP outcomes are preserved unchanged in their own packages.

Commands, per-run counts, allocation, and raw/audit hashes are recorded in [RUN.json](RUN.json), [FREEZE.json](FREEZE.json), [`output/raw.json`](output/raw.json), and [`output/audit.json`](output/audit.json).
