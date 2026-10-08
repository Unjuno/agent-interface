# T0 A02 preregistration — Issue #8586

## Question and delta

A01 retained one distinct non-additive joint-loss configuration for
`preserve_sibling_edit`; two raw rows represented that same loss pair, with the
second row adding an unrelated lost capability. Issue #8586 T0 asks for at least
two non-additive joint-loss configurations. A02 adds a distinct
`focused_window_action` task and tests simultaneous loss of
`window_identity` and `focus_stability`. A01 source, freeze, raw, audit, and
decision remain unchanged. Results from A01 and A02 are not pooled.

To keep each task's enumerated capability set within the Issue's small-model
scope, each task has its own three- or four-capability universe. Universal
authority/freshness/actuation hard gates remain explicit and are not degraded by
this matrix.

## H / T / D / C / U

**H.** In the authored finite model, independent edge fallback composition will
admit two distinct unsupported joint-loss configurations: loss of
`semantic_target` plus `native_effect_check` for sibling-preserving edits, and
loss of `window_identity` plus `focus_stability` for a focused-window action.
For each pair, either single loss has a separately qualified alternate route;
their combined fallback does not prove the complete task contract. The
task-conditioned envelope will stop both combinations while preserving every
route the independent oracle marks feasible. Blanket stop will reject at least
one feasible degraded route.

**T.** Exhaustively enumerate four task classes. For each task, enumerate every
subset of its frozen three- or four-capability universe across six contexts:
valid, unknown cause, stale configuration, missing compensator, changed task
intent, and expired degraded allowance. Compare independent edge-by-edge
fallback composition, blanket stop, and task-conditioned route eligibility.
An independently authored raw-only oracle reconstructs every row, route proof,
task obligation, hard gate, context decision, and both named joint-loss
witnesses. Construction tests mutate each witness, remove rows, alter task
obligations, forge compensator state, weaken UNKNOWN, and alter expiry handling.

The experiment is a deterministic, standard-library-only CPU enumeration. It
does not exercise an application, runtime, external effect, user data, GUI,
model, OS input, or shared container service. No container boundary is part of
the frozen question.

**D.** `PASS_METHOD_SCOPED` only if all expected rows are independently
reconstructed with zero errors; TDCE has zero false continuations and false
stops; edge composition has at least two distinct two-capability joint-loss
false continuations, including both named witnesses; blanket stop rejects at
least one feasible row; and every frozen mutation control is rejected.
Otherwise retain `FAIL_METHOD` or `HOLD` as observed. No post-result threshold
changes or reruns.

**C.** A fuller capability graph may already encode these dependencies; the
task contracts and proof labels are authored; and a conservative blanket stop
may be preferable when no alternate route is independently qualified.

**U.** The model does not establish that these capability failures occur in a
deployed interface, that the route proofs are valid for any real application,
or that TDCE improves live control, safety, latency, reliability, or product
behavior. A PASS supports only the two finite authored witnesses and the
enumerated task-local universes.

## Frozen model and execution boundary

`model.json` is the complete authored input. Each task declares its relevant
capability universe, primary route, per-capability fallback, qualified routes,
obligations, and hard gates. The candidate emits exactly one row per task ×
loss subset × context. The auditor does not import the candidate and holds its
own task/route oracle.

Construction tests run before formal freeze and may be repaired with retained
development records. After freeze, invoke the candidate once. Invoke the
auditor once only when the candidate exits zero and leaves a non-empty raw.
Preserve any first formal `FAIL`, `HOLD`, or `STOP`; do not rerun either command.

```sh
python3 -B -m unittest -v test_construction.py
python3 -O -B -m unittest -v test_construction.py
python3 -B candidate.py model.json results/candidate.raw.json
python3 -B auditor.py model.json results/candidate.raw.json results/audit.json
```

The first two commands are construction checks. The last two are the single
formal candidate and auditor invocations.
