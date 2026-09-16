# MAP01 OS history late binding v6 — execution-time binding result

## Decision

**PASS_EXECUTION_TIME_LATE_BIND** with `PASS_AUDIT`.

This formal block holds the rolling capture process, history classifier, initial-door task, semantic program, temporal pair contract, 450 ms planner/decision wait and 500 ms freshness gate fixed. The only arm difference is when evidence becomes execution-bound:

- `snapshot_bound`: select the freshest admissible pair before the fixed wait, then retain that pair.
- `late_bind`: keep rolling capture active during the same wait and select the freshest admissible pair only after the wait.

The high-level goal is door transit. Because the world continues advancing during the wait, the local door phase is allowed to change; success is evaluated from fresh admission plus independently scored transit, not from matching the pre-wait phase label.

## First complete result

- snapshot-bound: stale **8/8**, safe zero-input yields **8/8**, transit **0/8**, release failures **0**, median controller-start evidence age **678.057 ms**.
- late-bind: stale **0/8**, door transit **8/8**, release failures **0**, task input present only after fresh admission, median evidence age **212.750 ms**.
- paired median `(snapshot age - late-bind age)`: **459.521 ms**.

The preregistered PASS gate required 8/8 fresh late-bind goal success, zero late-bind release failures, at least 6/8 stale snapshot safe-yields with zero task input, and >=250 ms paired-median evidence-age separation. All gates passed.

## Development correction before formal

A development-only seed showed that after 450 ms an originally `opening` door can legitimately present a `closing` local phase. Therefore the formal question was frozen around the invariant high-level subgoal (transit) and execution-time binding, rather than incorrectly requiring the post-wait runtime to preserve the source phase label. Development rows are excluded from the formal denominator.

## Independent audit

The audit re-decodes every retained PNG, verifies RGB hashes, checks the 50–100 ms history-pair interval, reconstructs the freshest eligible pair from each rolling ledger, validates planner-wait timestamp ordering, enforces the 500 ms age gate, recomputes history predictions for admitted late-bind cases, verifies task input counts, transit effects and every setup/controller release record, and recomputes the frozen decision.

## Interpretation and limits

This is scoped evidence for an architectural boundary: a planning decision may name a durable subgoal, but environment-dependent local action authority should be admitted against fresh evidence at execution time. Retaining a pre-wait observation can correctly expire; a rolling observation service can supply a new no-authority evidence pair for local branch selection before input.

The 450 ms wait is a deterministic sleep, not a frontier-model call. The task is one MAP01 initial-door fixture, not MAP01 clear or long-horizon navigation. No automap, pause/save-state, controller-visible position/angle, or direct game action vectors are used for action selection. No generic speedup or model-efficacy claim is made.
