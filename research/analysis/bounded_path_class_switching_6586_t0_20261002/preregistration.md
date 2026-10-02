# Preregistration — bounded path-class switching (Issue #6586)

Allocation: `PATH-CLASS-6586-T0-20261002-01`\
Starting main: `f1d8f6319ad6a1d6fd7f0219c17bb13f48fae7aa`

## H/T/D/C/U

- **H — Hypothesis:** on the authored `blocked_class_gain` graph, a policy may use a current, source-bound, complete cutset receipt to exclude the blocked route and switch to an already observed alternate route. It will observe the goal with strictly fewer counted observations plus input actions than both novelty-first and visited-edge/backtrack policies, without switching on viable same-class, recoverable same-class dead-end, false-binding, stale-epoch, or single-class controls.
- **T — Test:** six fixed visible finite graphs × three deterministic policies (`novel_cell`, `visited_edge_backtrack`, `class_aware`), at most 64 observations and 64 input actions per row, zero model calls. Record every observation, transition, reversal, certificate decision, terminal state, and cost. A separate raw-only auditor will enumerate simple paths from the fixture and check receipt contracts, task result, costs, controls, and mutations.
- **D — Decision:** `PASS_METHOD_HOST_SCOPED` only if all 18 rows are present and independently replayable; class-aware reaches the target on the primary case at strictly lower counted cost than both baselines; all specified controls preserve their expected outcomes without a forced switch; false-binding and stale-epoch receipts are rejected; the single-class case yields rather than inventing an alternate; and every mutation control is rejected. Otherwise record `FAIL_OR_HOLD` and do not claim a method pass.
- **C — Confounders:** hand-authored graph structure and perfect evaluator-provided receipts may favor the candidate; novelty and DFS are deliberately simple deterministic controls; route tokens are supplied by the fixture and are not inferred; a “complete cutset” receipt is a synthetic contract rather than a demonstrated perception capability.
- **U — Uncertainty:** no proof that geometric homotopy classes can be inferred from images, no real dynamic-world behavior beyond epoch invalidation control, no GUI/DOOM or task-effect evidence, no model/runtime/performance result, and no container isolation. The local host result cannot establish product progress or the formal container gate.

## Freeze and execution

The visible fixture, evaluator-only oracle, candidate, runner, auditor, tests, this preregistration, and README are SHA-256 frozen in `FREEZE.json` before the one-shot candidate invocation. Construction checks may be repeated before that freeze. After the formal run, do not alter frozen sources or rerun this allocation. The evaluator oracle is read only by the separate auditor; the candidate runner receives only visible fixtures.

Host: macOS local Python; container/WSLc was not allocated because the available shared OrbStack container belongs to another active task. This execution is explicitly host-scoped.

## Expected interpretation

A passing result supports only the bounded synthetic method contract described above. A failure or hold is retained as evidence and is not repaired by relabeling or repeating the run. Real environment work requires a separately authorized, prospectively specified test under the relevant Issue.
