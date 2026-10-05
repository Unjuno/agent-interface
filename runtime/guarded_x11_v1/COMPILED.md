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
or authorization strings cannot resume a finished invocation. Capture and
perception exceptions are retained, then returned by the graph as
`RUNTIME_FAILED / observation_failed` with the verified prefix; inspect
completed/uncertain input before choosing a new action. Failures outside the
observation boundary propagate after retention. There is no automatic retry or
release claim when an execution supplies no actual release evidence.

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

## Native cleanup receipts before execution

Backend validation may refuse a program before execution and return its verified
cleanup in the top-level `release` field. The adapter preserves that receipt along
with any execution releases. Neutrality requires all provided receipts to be
verified and empty and the session to require no recovery. Reported held input
is retained; malformed or unverified cleanup cannot become a safe abstention.
A missing receipt still does not invent neutrality. No-input evidence is not
inferred from counters or from a release receipt, and a refusal remains incomplete.

Bindings use the backend's actual key names. Linux/X11 keysym names are
case-sensitive: `Home` is valid, while `HOME` is rejected unless explicitly
supported as an alias. Backend preflight can refuse such a program before
execution; read its retained detail and cleanup rather than claiming an action
completed or blindly retrying it.

## Binding changes during capture

If the bridge detects a different focus/surface/geometry before and after a
capture, it retains the public report and a `capture-binding-changed-*.json`
record, requires explicit window review, and raises `CaptureBindingChanged`
(an `X11BackendError` subtype). The compiled graph recognizes only its typed
`ObservationAssociationChanged` boundary and returns `SAFE_YIELD /
association_changed`, preserving completed transitions and pending effects.
No valid observation sequence/history entry is published for that capture.
The latest evidence still refers to the last valid frame, not the changed
capture. Review the actual window and obtain fresh grounding before new input.
There is no automatic window selection, retry, confirmation or effect success.
Untyped errors during observation still retain an exception record, then return
`RUNTIME_FAILED / observation_failed`; failures outside observation propagate
and are retained.

[Primary Calc successor](../results/calc-compiled-pixel-admission-05/README.md)
exercised the actual capture binding change and returned this typed receipt.
After explicit primary modal review/new grounding/confirmation, the independently
read saved workbook matched317/529. The preceding startup failure is retained.
This qualifies the boundary and one saved task, not a speed or token improvement.

## Failed Inkscape keyboard transfer

[Guarded Inkscape transfer](../results/inkscape-guarded-transfer-03/README.md)
compared this actual adapter with a strong ordinary conditional keyboard
callback. Both completed input but observed no intended movement and stopped
before Save; independently persisted task success was 0/2. Startup and context
refusal predecessors remain retained. This does not qualify the move recipe or
second-domain performance. Actual keyboard receipts established admission/focus
guards, not per-key revalidation. Hold the recipe pending separately frozen
application-effect diagnosis; do not infer task completion from input delivery.

## Explicit application interaction before keyboard continuation

[Inkscape canvas diagnosis](../results/inkscape-explicit-canvas-01/README.md)
found one independently saved ordinary task after a separately grounded
rectangle click. Immediate, 100ms-gap and separately reviewed keyboard selection
predecessors all failed to move the rectangle. Window focus and visible object
selection alone did not establish the successful keyboard context in those
cases. The mechanism is not isolated; this is not a generic click repair or a
qualified compiled transfer. Explicit pointer input needs its own current target
and authority. Do not silently insert a click into keyboard continuation. A
fresh matched graph comparison must include the same application interaction
and independent effect scoring in its strong ordinary baseline.

## Canvas-prepared Inkscape comparison

[The fixed ordinary/guarded comparison](../results/inkscape-canvas-comparison-02/README.md)
completed one normal saved task per route with identical persisted SVG bytes.
Both undertravel controls stopped before Save and preserved the original file.
An explicitly grounded rectangle click and primary selection review are common
preparation outside the graph. This qualifies the canvas-prepared keyboard
move/check/Save method, not orchestration of the entire pointer workflow.
The strong ordinary callback uses the same inputs, captures and caller commands;
the graph reduced none of those counts. Actual whole-context model usage is
retained with explicit windows and preparation failure, without causal route
savings, billing or human-tempo claims. Correctness is scoped; efficiency and
default-route promotion remain HOLD.
