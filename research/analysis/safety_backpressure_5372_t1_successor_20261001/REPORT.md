# Issue #5372 T1 successor, allocation 02 — scoped model result

**Disposition: `PASS_SCOPED_COUNTEREXAMPLE`** for the frozen finite queue model only. One candidate invocation completed in a network-disabled Python 3.12 Docker container on an Ubuntu 24.04 ARM64 GitHub runner; a separate ARM64 runner downloaded the candidate artifact and ran the independent auditor once in a second isolated container. Both jobs passed. Allocation 01 remains `STOP_HARNESS_IMAGE_IDENTITY_STRING_MISMATCH`; its candidate never started and was not retried.

## Main contrast

At fixed high offered load (36 tasks), BASE/FIFO (local action 2 ticks) verified 10 tasks by horizon 48, with 50 stale attempts, 26 retries and 24 UNKNOWN tasks after drain. FAST/FIFO (1 tick) verified 4 by horizon, with 64 stale attempts, 32 retries and 32 UNKNOWN. Thus the locally faster action produced a concrete overload inversion in the model.

FAST/BACKPRESSURE on the same fixed 36-task offered schedule verified 14 by horizon, with 13 stale attempts, 13 retries and zero UNKNOWN after drain. Relative to FAST/FIFO this is +10 horizon-verified tasks, 51 fewer stale attempts and no unclassified terminal work. Its normal pending peak was 3, within the preregistered bound of 4. Backpressure did not reduce horizon throughput in any of the FAST near/high/closed comparisons.

The horizon-verified p95 was 5 ticks in FAST/FIFO and 30 in FAST/BACKPRESSURE. This is a selected-survivor statistic and is not treated as an independent pass gate; it exposes a latency/throughput tradeoff among tasks completed by the horizon. In the closed-loop schedule, backpressure also lowers offered task count (FAST/FIFO 36 vs FAST/BACKPRESSURE 21), so those counts describe a completion-triggered source and are not equal-offer comparisons. Fixed high load is the equal-offer primary counterexample.

Across all 16 cells, all six mandatory safety events were serviced; maximum release-to-completion latency was 1–2 ticks (bound 3). The independent audit checked the event ledger, freshness/effect gate, retry and task disposition accounting, action/verifier timing, per-class counts, bounded pending work, safety obligations, all frozen contrasts, and rejected safety-deletion, stale-effect, and duplicate-success mutations in local construction tests. No unsafe effect was admitted.

## Reproduction and retained evidence

- Allocation: `SAFETY-BACKPRESSURE-ENDOGENOUS-DEMAND-5372-T1-20261001-02`.
- Source commit: `082e241975c9cf02cf6047c689a308847ec01e53`; intake main: `f3bf21e7d0191455596c89bd14609155407848ad`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; network disabled, read-only root, 1 CPU, 256 MiB, 64 PIDs.
- Workflow: [run 36818049053](https://github.com/Unjuno/agent-interface/actions/runs/36818049053). Candidate job `110227330896`; independent-audit job `110227689592`.
- Candidate artifact SHA-256: `f71a86dc1ec405e70d31cb277ccf1d94ebf27fe1325bfcb20eb625337a2a71ef`; raw JSONL SHA-256: `29d22764199595b322abee6c630b22b9e9afe4b4bfddf41734bc1eed817bddc7`.
- Auditor artifact SHA-256: `8dc8b5078c12a2a3d74cb9e248bf83e6dcac0c594bb1461af12c9e4d510e781b`; result: `PASS_SUCCESSOR_INDEPENDENT_AUDIT allocation=02 cells=16 safety_all_serviced=true`.
- Local construction CI: 3 successor tests passed; frozen source hashes verified; the full retained-result index check passed at 273 directories before this report was added.
- Raw candidate and audit artifacts are retained under `results/formal-02/`; `RUN_MANIFEST.json` and `SHA256SUMS` bind their execution and bytes.

## Scope boundary

This establishes a counterexample in an authored deterministic simulator—not a production/runtime effect, prevalence estimate, human benefit, or safety guarantee. Service times, workload, freshness window, telemetry delay and retry limit are fixed. This T1 compares FIFO normal work with pressure admission while a mandatory safety lane is prioritized in both. It does not test independent FIFO/deadline queues, a priority-only normal queue, or the newer route-set expansion contrast in #5372. Issue #5372 remains open for those variants and for real workload validation. Issue #5702's endogenous task-choice/mix rebound has a different estimand; its data are not pooled here.
