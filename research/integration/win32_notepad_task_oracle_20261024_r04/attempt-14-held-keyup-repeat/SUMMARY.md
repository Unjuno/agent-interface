# R14 — ten fixed repeats of held-keyup recovery

## Result

**10/10 trials passed** the frozen scoped recovery gate on the same blank Notepad target and generation. Each fresh supervised caller sent native SHIFT-down, blocked its producer before native SHIFT-up, independently observed SHIFT-down, then retained successful bounded recovery, replay denial, same-generation SHIFT-up, unchanged document, and a monotonic completion before deadline. All task-success fields remained null.

| Trial | owner cleanup interval, perf_counter_ns | monotonic deadline margin, ns | status |
|---:|---:|---:|---|
| 1 | 16854600 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 2 | 17698700 | 2985000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 3 | 16848700 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 4 | 17203400 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 5 | 17145800 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 6 | 17432400 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 7 | 18716100 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 8 | 16781200 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 9 | 17497800 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |
| 10 | 17504000 | 2984000000 | PASS_SCOPED_BOUNDED_RECOVERY |

High-resolution cleanup interval mean: 17368270 ns; median: 17317900 ns; range: 16781200–18716100 ns.
Monotonic deadline margin range: 2984000000–2985000000 ns. The owner interval is request acceptance through release plus neutral-readback receipt evaluation, not physical key-release latency or end-to-end task latency.

## Statistical and scope limits

The observed conditional rate is 10/10. Under an IID Bernoulli assumption, the two-sided 95% Clopper–Pearson interval is [0.692, 1.000]. That interval is illustrative: all runs reused one window, target generation, host and fixture, so independence and generalization are not established. Treat this as a ten-repeat fixed-condition diagnostic, not a broad reliability estimate.

The injected stall occurs at the producer backend-send boundary before native `SendInput` for SHIFT-up, after a real native SHIFT-down. It does not block inside the Windows API or kernel, and it does not establish arbitrary platform-I/O bounds, stdio behavior, task success, MAP01, matched efficiency, or other-app transfer. No WSLc allocation or Docker operation was used.

## Reproduction and custody

Each `replicate-NN/` directory retains its own exact program, per-call raw requests/reports, independent observations, result, preflight, screenshot, harness, and stderr. `SERIES.json` retains sequence, exit status, result/stdout hashes, per-trial gates and timing. `PLAN.md` was frozen before execution. `SHA256SUMS` at the R04 packet root covers the full packet.
