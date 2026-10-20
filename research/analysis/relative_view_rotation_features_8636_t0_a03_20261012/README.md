# Issue #8636 T0 A03 — fresh-seed rotation-feature allocation

**State before formal run: frozen candidate package; formal invocations = 0.**

A03 is a new deterministic CPU-only allocation with seeds 30060–30089 in each of four strata. It preserves A01 and A02's `HOLD_UNCERTAIN` outcomes and does not reuse their formal inputs or raw outputs. The controller, equations, thresholds, fixtures, action budgets, and primary hypothesis remain fixed. The only method correction is in the independent auditor: its ViewState-oracle replay now matches the frozen runner, which emits clamped corrections until step 12 without applying the image arms' stop tolerance.

Read `PROTOCOL.md` and `FREEZE.json` before running. The exact CPython executable, package sources, source hashes, one-run commands, and empty formal-invocation counter are frozen before either formal invocation. Only the commands in `FREEZE.json` are authorized; candidate and auditor each have a one-invocation limit, with no retry.

No WSLc, container, GUI, model, OS input, external service, or live effect is used. This synthetic method result cannot establish screenshot tracking, real GUI/game task effect, physical release, safety, human benefit, or portability.
