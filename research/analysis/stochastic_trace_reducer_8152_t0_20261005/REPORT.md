# Issue #8152 T0 — formal result

**Disposition: `METHOD_PASS_SCOPED`.** The frozen OrbStack candidate and independent raw-only auditor each ran once and exited 0. The auditor reconstructed all outcomes and reported zero errors. This top-level report is an additive interpretation; the frozen protocol, raw candidate output, audit, invocation record and their checksums under `results/` are unchanged.

## Result

The experiment compared A (single-run screening), B (fixed 64 repetitions), and C (sequential 8–64 repetitions in steps of eight) on 12 seeded instances across four declared strata. All three arms used the same 512 paired, held-out seeds per instance; confirmation seeds were disjoint from every baseline/search seed.

| Arm | Screening-stage replays | All oracle executions, including confirmation | Shorter traces | Held-out non-inferiority |
|---|---:|---:|---:|---:|
| A — single run | 864 | 13,152 | 11/12 | 5/12 |
| B — fixed 64 | 6,912 | 19,200 | 12/12 | 12/12 |
| C — sequential | 4,184 | 16,472 | 12/12 | 12/12 |

Screening calls include the shared 64-per-instance baseline. C used 2,728 fewer screening calls than B (39.5% less); including the same 12,288 held-out baseline/final replays in each arm, total oracle executions fell by 2,728 (14.2%). The fixed and sequential arms ended with 7–8 events versus 13 initially (71 fewer events across the 12 final traces). Their exact-target held-out success count was 5,059/6,144 versus 4,639/6,144 for the original traces. The most conservative per-instance simultaneous lower bound on the final-minus-original rate was about -0.0828, above the preregistered -0.20 margin.

The single-run comparator shortened 11 traces but met the held-out bound in only five; in several instances it removed warmup and substantially reduced recurrence. Its held-out outcomes included 117 competing-fingerprint failures across three instances. These were reconstructed as `COMPETING_WIDGET_CRASH` (exit code 17), never credited as the target. This demonstrates why exit-code equality and a lucky one-shot replay are inadequate preservation tests in this model.

## Gate and scope

All B/C accepted traces retained mandatory reset, lease and release, respected the frozen event grammar, and passed held-out exact-target non-inferiority with Bonferroni-adjusted one-sided exact Clopper–Pearson bounds. Raw replay reconstruction, candidate thresholds/look sequences, seed separation and query counts all passed the independent auditor. No model, GUI, live repository failure, user data, or external effect was involved.

This is a method result only for the authored stationary synthetic hash oracle. It establishes neither production utility nor live GUI safety, causal root cause, general minimality, or robustness to nonstationary hidden state. It is a bounded transfer motivated by stochastic delta debugging work in CPSs ([Valle, Ali & Arrieta, arXiv:2607.25695](https://arxiv.org/abs/2607.25695)); it does not claim a new general stochastic delta-debugging algorithm.

## Evidence

- Freeze and source/input digests: [`FREEZE.json`](FREEZE.json)
- Frozen machine report: [`results/REPORT.md`](results/REPORT.md)
- Independent audit: [`results/AUDIT.json`](results/AUDIT.json)
- Candidate raw output: [`results/candidate.raw.json`](results/candidate.raw.json)
- One-shot invocation record: [`results/RUN.json`](results/RUN.json)
- Integrity checks: [`results/SHA256SUMS`](results/SHA256SUMS)
