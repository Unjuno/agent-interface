# Bounded compiled methods over the shared X11 bridge

`runtime.guarded_x11_v1.compiled.run` connects the existing shared
`runtime.core_v1.compiled_gui` graph to a caller-owned `NativeHandleBridge`.
This is an opt-in portable Python API for Linux/X11. It imports no research
implementation, does not spawn a model, and does not change MCP routing.

Ground the existing aliases from a reviewed bridge observation. Author the
bounded graph with `session_scope=bridge.scope` and
`surface=compiled.surface(bridge)`. For each graph action, provide an exact
binding with `interaction` (`click`, `move`, or `keyboard`), its alias-local
`offset`, and an explicit `tail` list using the existing bridge contract.
Native target references must match `[a-z][a-z0-9_]{0,31}`, the same alias
contract as the handle store. For example, use `sheet_context`. Graph symbol
labels remain separate and may use the graph's broader naming contract.
The adapter rejects invalid native aliases before capture or any callback.
Bindings and graph are copied before any perception callback can change them.

```python
from runtime.guarded_x11_v1 import compiled
receipt = compiled.run(
    bridge, interface, bindings,
    perceive=perceive, verify_effect=verify_effect,
    cancelled=lambda: False,
)
```

`perceive(native_observation, rgb)` returns declared scalar predicates from
copies of the newly captured observation and its exact RGB. Symbol identity
and dependencies in this adapter are boolean prerequisites: all must be True.
Unknown/false prerequisites cannot be overridden by a matching action branch.
The adapter uses the existing handle store against that same capture, then
passes a one-use authorization and the original minimum method/admission
deadline to the bridge's ordinary click/move/keyboard path. The ordinary
captures, pixel/focus checks, admission, partial execution and release remain.
A plan cannot remint a reference, renew the scope or replay an uncertain action.

`verify_effect(payload, native_observation, rgb)` supplies the graph's typed
`status` and `evidence_ref` verdict. The graph checks its declared expected
predicates first. Branch conditions and expected effects require both the same
scalar type and value: boolean `true` does not satisfy integer `1`, and boolean
`false` does not satisfy integer `0`. A branch mismatch yields `unknown_state`;
an effect mismatch yields `effect_failed`, preserves the completed prefix and
pending effect, and stops before the verifier or any next action.
The callback must establish the intended effect for that
application; returning succeeded without an adequate contract does not verify
text or durable saving. Both callbacks are trusted caller code, not sandboxed,
not an independent oracle and not a generic vision/OCR service. Scope/sequence
changes in either callback prevent continuation or completion. They are
synchronous per-iteration reads, not installed or background sensors.

Every graph iteration retains a fresh native image and metadata through the
bridge. Its output directory also retains the fixed plan, graph events,
reference resolutions, admissions, full input receipts, effect verdicts and
final graph receipt. These files are not fsync-backed crash durability. Keep
the raw bridge artifacts with their recorded paths/hash links. Retained receipts
or authorization strings cannot resume a finished invocation. A callback or
I/O exception is retained and propagated; inspect completed/uncertain input
before choosing a new action. There is no automatic retry or release claim
when an execution supplies no actual release evidence.

`TASK_SUCCEEDED` is a local graph verdict. Independently score application task
and collateral effects after the controller is terminal. Method deadline
checks remain cooperative; blocking X11/callback I/O is not preempted.
Primary use, raw evidence and limits are recorded in
[the main integration trial](../results/compiled-x11-live-01/README.md).
Its private fixture has an application-specific accepted/saved cue and stable
canvas Save control. General GUI text verification, hover recovery, comparable
model token/cost savings and human-tempo performance remain unproven.

## Comparison with an existing method

The [finite primary comparison](../results/compiled-composition-comparison-01/README.md)
uses the existing `form.fill_and_submit` with an explicit read-only on_step
callback that retains receipts, checks neutral release and fresh application
cues, and can raise before Save. In the fixed two-stage fixture, both this
composition and the graph conditionally continued in one caller invocation with
the same inputs, captures and primary images. Graph structure alone did not
reduce roundtrips. Descriptive timings and whole-context usage do not justify
speed/token/default-route promotion. The unmodified form helper still does not
verify text or saving; an adequate application callback and independent scoring
remain necessary. Choose the existing method or graph according to the needed
control/evidence contract, rather than assuming that the graph is faster.

## Refusal immediately before input

A native target/sequence change after admission can refuse execution before any
input. The adapter preserves explicit `input_dispatched: false` evidence and the
graph stops with `SAFE_YIELD / execution_refused`. It retains completed actions,
records `release_verified: false` if no release occurred, and does not continue
or automatically retry. This is a typed abstention, not proof of neutral input or
of task completion. Read the retained raw refusal before choosing a new action.

The optional terminal field is strict boolean. A false value is valid only with
`status: refused`; malformed or contradictory metadata is rejected. Missing
no-input evidence, actual delivery, held keys/buttons, native execution metadata or failed release or
recovery-required state keep the existing stricter failure handling. Existing
adapter terminal shapes remain supported. [Boundary regression evidence](../results/compiled-refusal-integration-01/README.md)
uses deterministic adapters, not a live GUI performance comparison.

## Pixel-only effect callbacks and deadlines

The [real Calc pixel admission](../results/calc-pixel-effect-admission-02/README.md)
read two visible cell values from an exact delivered capture using caller-grounded
regions and a fixed OCR rule. A blank control produced a spurious word that the
rule classified unknown. This supplies narrow feasibility evidence for common
read-only assistance; it does not qualify a generic text verifier, saved effect,
all comparison arms or this compiled adapter on Calc. The primary workflow's
final confirmation expired and its independent saved-task score failed.

Keep input expiry separate from the entire task's elapsed time. The existing
compiled adapter checks each action's current reference and clamps its deadline
to the method/reference minimum. Neither pixel recognition nor a fresh clock
renews authority. After a model wait, use the ordinary target/dependency review
and admission; preserve a refusal instead of replaying input with a longer lease.
A useful visible predicate is separate from independently scored persisted effects.
