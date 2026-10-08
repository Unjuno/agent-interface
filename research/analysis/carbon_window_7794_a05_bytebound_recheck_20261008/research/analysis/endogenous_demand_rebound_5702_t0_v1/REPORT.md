# Endogenous task-demand rebound — finite T0

**Disposition: `PASS_METHOD_SCOPED` for the frozen three-case subdesign; the broader Issue T0 remains incomplete.** The finite opportunity table demonstrates that fixed-workload cost improvement and session-level outcomes can diverge in either direction when optional task initiation changes. This is a synthetic accounting/method result only—not evidence that a deployed or real agent exhibits rebound.

The candidate produced 22 rows covering every offered opportunity in three paired cases. A separate raw-only auditor returned `PASS`, zero errors, and rejected all 8/8 preregistered corruptions.

| Case | Slow route | Fast route | Scoped interpretation |
|---|---:|---:|---|
| Frozen-start / no extensive margin | 2 started, 1 completed, 1 UNKNOWN; resource 6; net useful value 4 | 2 started, 1 completed, 1 UNKNOWN; resource 4; net useful value 6 | Same task mix and outcomes; per-route resource cost fell. UNKNOWN was not counted as completion/value. |
| Beneficial expansion | 1/3 offered started; net useful value 7 | 2/3 offered started; net useful value 12 | Lower action cost admits a positive optional task within the fixed budget. |
| Adverse task mix | A+C started; net useful value 11 | A+B started; net useful value 6 | Fast-route B is ex-ante positive in the frozen rule but has an independently fixed lower realized endpoint and consumes verifier/budget capacity, displacing higher-value C. |

All six high-value-but-forbidden `D` rows were retained and blocked; forbidden effects were zero in every arm. Every offered-but-skipped opportunity remains in the raw denominator. The result validates only that this frozen decision table, scorer and audit preserve those distinctions. It does not estimate real task demand, causal welfare, safety probability, or a transferable rebound coefficient. T1 needs a separately approved matched live cohort and independent endpoint scorer.

The one-shot execution was host-only CPython 3.12.13 on macOS arm64, as the Issue's T0 requests no container/GPU allocation and Obstac is unavailable in this runtime. It is not container evidence. Exact commands, versions, exits, hashes and limitations are in [RUN.md](RUN.md); raw candidate and audit outputs are retained under `results/formal-host-01/`.

## Issue-wide T0 coverage qualification

The Issue's original T description also calls for treating **route-induced state occupancy as a confound**. This frozen three-case subdesign does not independently vary or measure that occupancy process; its verifier demand is a finite shared capacity in the decision table, not a state-occupancy model. Accordingly, the reported PASS applies only to the explicitly frozen no-rebound / beneficial-expansion / adverse-mix accounting gates. It does not complete the broader Issue T0 or resolve the occupancy confound. Preserve this result unchanged; any occupancy-specific test needs a distinct prospective successor design/allocation.
