# MAP01 OS history late binding v7 — multi-second wait transfer

## Decision

**PASS_LONG_WAIT_LATE_BIND** with `PASS_AUDIT`.

V7 changes one scientific variable from retained V6: the deterministic planner/decision wait increases from 0.45 s to **6.5 s**. The rolling capture process, history classifier, initial-door task, local semantic program, 50–100 ms temporal contract, 500 ms freshness gate, snapshot-bound vs late-bind architecture and OS-input path are otherwise unchanged.

## First complete result

- snapshot-bound: stale **8/8**, safe zero-input yields **8/8**, transit **0/8**, release failures **0**, median controller-start evidence age **6.759 s**.
- late-bind: stale **0/8**, door transit **8/8**, release failures **0**, median evidence age **176.024 ms**.
- paired median `(snapshot age - late-bind age)`: **6.575 s**.

The preregistered PASS gate required 8/8 fresh late-bind goal success, zero late-bind release failures, at least 6/8 stale snapshot safe-yields with zero task input, and >=5 s paired-median age separation. All gates passed.

## Interpretation

This strengthens the narrow V6 mechanism result across a latency scale comparable to retained multi-second MAP01 model/coast intervals: durable planner intent can remain a subgoal while environment-dependent local input authority is derived from fresh execution-time evidence. A source-bound observation correctly expires; rolling observation retention makes a later no-authority state check available without granting input by itself.

## Important boundary

The 6.5 s delay is a deterministic local sleep, **not a frontier-model call**. No token/cost/model-quality inference follows. This is still one initial-door fixture, not live combat, long-horizon navigation or MAP01 clear. No automap, pause/save-state, controller-visible position/angle, or direct game action vectors are used for action selection.

The independent audit re-decodes retained PNGs, verifies RGB hashes and temporal pair binding, checks planner-wait ordering, freshness, task input counts, independently scored transit and all release records, then recomputes the frozen PASS/HOLD/FAIL rule.
