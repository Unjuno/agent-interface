# Evidence-dependent compute scheduler hard dominance R0

Issue #1687. Decision: **PASS_COMPUTE_SCHEDULER_HARD_DOMINANCE_SCOPED**.

## Analytical result

Under the frozen one-job contract, a new RUN can be rejected from hard metadata alone exactly when either:

1. a declared dependency is already stale; or
2. deterministic completion would be later than the inclusive usefulness deadline.

The proof is direct. A stale-source result is forbidden from publication, so starting stale work cannot produce an admissible result. If current time plus remaining deterministic compute exceeds the hard deadline, completion has zero usefulness by contract. Conversely, when dependencies are current and deterministic completion is on or before the inclusive deadline, a stable future with no invalidation exists in which the result can be published on time; therefore hard metadata alone cannot classify RUN as infeasible.

The exact equality boundary is included. Formal enumeration found 23 current rows with completion exactly at the deadline and accepted all 23.

## RUN versus WAIT is not identified by hard metadata

One frozen current metadata tuple is `t=0,c=1,d=2,current=true`. RUN begins immediately. WAIT delays `1/2` and rechecks.

- STABLE future: RUN completes usefully at 1 with cost1; WAIT completes usefully at3/2 with cost3/2. RUN is preferred.
- INVALIDATE_SOON future: the dependency invalidates at1/4. RUN has already spent1/4 compute and cannot publish, cost41/4 including the common no-result penalty10. WAIT observes invalidation before starting, wastes0, cost10. WAIT is preferred.

The current metadata are identical, but future invalidation differs. Therefore hard currentness/deadline metadata can prune impossible RUNs but cannot universally choose RUN versus WAIT for the remaining feasible set. Such a choice requires an additional future/utility model or a stronger contract.

REUSE was never selected or analyzed; that remains separately owned.

## Formal evidence

- exact Fraction grid rows:480;
- candidate/direct hard-feasibility mismatches:0;
- stale RUN accepted:0;
- tardy RUN accepted:0;
- inclusive exact-deadline ties:23/23 feasible;
- paired-future preference reversal: present;
- REUSE decisions:0;
- formal invocation1; reruns/replacements/tuning0;
- independent audit: PASS;
- four corruption controls: all rejected.

Raw deterministic `RESULT.json` is retained losslessly as `RESULT.json.gz.b64` using `gzip -n`. Raw SHA-256 is `c34229d4f8f9821e71176336b60429325927d610d3acf11ce5199682e9e3a40b`; compressed SHA-256 is `4a057128c6570e2b5a647ba860c5bd19851446f9f3f85890414017be3ac28385`.

## Scope

This is an analytical one-job prerequisite only. It does not claim observed CPU savings, real preemption behavior, multi-job scheduling, partial-result value, soft deadlines, model quality, or a production scheduler. The next scheduler layer should estimate or bound the value of RUN versus WAIT only after this hard pruning step.
