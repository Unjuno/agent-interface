# Slack reclamation for sporadic control deadlines

- **Source:** Closed [Issue #7778](https://github.com/Unjuno/agent-interface/issues/7778), with merged evidence [PR #7788](https://github.com/Unjuno/agent-interface/pull/7788) and dispatch-overhead companion [PR #7792](https://github.com/Unjuno/agent-interface/pull/7792).
- **Related questions:** #7722 tested priority, backpressure, and fixed reservation; #7748/#7762 covered finite processor-demand witnesses; #8061/#8070 corrected fail-closed handling of unknown job classes. These results remain separate.
- **Transfer sources:** Tia's [slack-time scheduling dissertation](https://hdl.handle.net/2142/20444) and Kim et al.'s [modified-laEDF simulation](https://www.mdpi.com/2079-9292/8/11/1286) motivate the finite CPU model; they do not establish Agent Interface host or input guarantees.

## Question and proposed mechanism

Can a single-processor scheduler lend idle service to optional work while preserving all feasible future deadlines for sporadic cancel/release jobs? The proposal compares priority-only, a fixed `Q=2/P=8` reservation, and demand-guarded slack stealing. It is a scheduler-model question. A unit-slot simulation cannot establish operating-system enforcement, backend acknowledgements, physical key-up, or GUI safety.

## Results

The zero-overhead T0 covered 9 traces and 27 policy rows; its corrected independent exhaustive audit reported zero errors and rejected 6/6 frozen mutations. The guarded policy met all modeled deadlines and delivered 21/22/22/21 optional service units on four positive-slack traces, compared with 18/18/18/9 for fixed reservation. The audit correction reread unchanged inputs and candidate output; it did not rerun the candidate.

The separate dispatch-overhead T0b covered 18 traces × 3 policies × 2 overhead factors (108 rows). Its independent exhaustive auditor reported zero errors, passed all three refusal controls, and found no guarded-policy deadline misses on oracle-feasible workloads. At zero overhead on the preregistered positive-slack subset, guarded service was 222 units versus 192 for fixed reservation (+15.625%). Across the full zero-overhead matrix, however, priority-only delivered 502 units, guarded slack 475, and fixed reservation 432. The result supports the narrow comparison against a non-borrowing fixed reservation, but does not justify adopting slack stealing over the simpler priority policy.

Both results are finite, synthetic, single-CPU integer-time analyses. The overhead factor is a modeled unit per job start, not measured machine overhead. The T0b run used local CPython on ARM64 after OrbStack image inspection stopped before a container ran. The exact evidence and its limits are retained in the linked PRs and [T0 result](../../research/analysis/slack_reclamation_7778_t0_20261005/RESULT.md), [T0b report](../../research/analysis/slack_reclamation_7778_dispatch_sensitivity_t0_20261005/REPORT.md). No runtime scheduler, host resource guarantee, physical release result, or performance claim follows.

## Disposition

The scoped synthetic hypothesis passed against fixed reservation on its preregistered subset, while priority-only was the stronger simple baseline on the full zero-overhead matrix. Keep the result as method evidence; make no runtime promotion. Preserve #7722's distinct consumed outcome and #7748/#8061's separate witness and metadata-boundary results.
