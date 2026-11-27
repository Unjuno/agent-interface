# Semantic dependency changes after compiled admission

2026-10-16 JST. Selected main `05e2a2197668246502810ed023724c4ee914828e`.
Decision: **RETAIN_SEMANTIC_RECHECK_COUNTEREXAMPLE**. No runtime patch adopted.

## Question and actual path

The previous [native-bridge composition](../compiled_native_caller_composition_20261016/README.md)
covered process-generation changes, but did not change a semantic value after
graph admission while preserving target texture and generation. Can a Submit
dependency selected True remain unexamined when the native bridge's newer
pre-input capture would show False or unknown?

The probe runs that actual caller/form/graph/guarded-adapter/handle-store/bridge/
backend/session composition. It wraps `_Adapter.execute` only at Submit entry:
the selected graph observation already has value True; before calling the
unchanged original execute method it changes one synthetic RGB marker outside
both target patches. No admission decision or input result is mocked. The
unknown case extends the trusted perception callback to map marker 3 to unknown.
The synthetic environment advances its phase on a fake completed chord, so
post-action observation can match even though the pre-input condition did not.

FakeX still replaces platform/backend construction, capture/XTest transport,
keymap and process-identity reads. This is not a real form, text recognizer or
independent app scorer. All input emissions are fake. No display/input, model,
provider, WSL/container or formal allocation was run.

## Observed comparison, eight cells per normal / actual optimized mode

| Arm | Change after Submit admission | First native pre-input value | Fake chords / prefix | Core outcome |
|---|---|---|---|---|
| Current | Stable | True | 2 / 2 | TASK_SUCCEEDED |
| Current | Value becomes False | False | 2 / 2 | TASK_SUCCEEDED |
| Current | Value becomes unknown | unknown | 2 / 2 | TASK_SUCCEEDED |
| Current | Process generation changes | True | 1 / 1 | SAFE_YIELD |
| Explicit keyboard dependency guard | Stable | True | 2 / 2 | TASK_SUCCEEDED |
| Explicit keyboard dependency guard | Value becomes False | False | 1 / 1 | SAFE_YIELD |
| Explicit keyboard dependency guard | Value becomes unknown | unknown | 1 / 1 | SAFE_YIELD |
| Explicit keyboard dependency guard | Process generation changes | True | 1 / 1 | SAFE_YIELD |

Each complete fake chord is CTRL press, `a` press, `a` release, CTRL release.
All fake keys finish up; no probe outcome is caller TASK_SUCCEEDED. Current
stable/False/unknown cells are TASK_NOT_VERIFIED because the separate outer
effect remains unavailable. Thus these are two **pre-input semantic condition
counterexamples**, not a demonstrated false independent application score.

The control uses the existing `NativeHandleBridge.input_guard` for the exact
keyboard binding, with a read-only callback requiring exact True. It adds no
retry/remint/lease renewal and does not change the native writer. False and
unknown are rejected before the second chord, preserving the first prefix.
Generation refusal remains effective in both arms. This control is not a
general production repair: current input_guard accepts only keyboard programs
with a nonempty tail, whereas compiled bindings also support click and move.

## Root cause, interpretation and next repair

`_Adapter.admit` checks symbol identity/dependencies against its last graph
observation. `_Adapter.execute` consumes that authorization and invokes the
native method without an additional semantic input guard. NativeHandleBridge
captures and validates alias texture, scope, generation and deadline, but does
not know the graph's semantic predicates. The newer capture therefore blocks
generation change but cannot itself reject the changed value.

This does not refute #8980's eight stated cases or imply that the current API
already promises continuous semantic checks. It demonstrates a missing
qualification needed before using exact-value Submit as a live task safeguard.
Post-action matching and independent outer verification cannot retract an input
already sent under a now-False/unknown semantic dependency.

The concrete next repair is to connect symbol identity/dependencies to the
ordinary native input-check captures, using an explicitly frozen interaction,
offset, tail and original deadline for click/move/keyboard. Preserve the current
keyboard API by default; never silently omit checks on an unsupported bridge.
Recheck only declared input dependencies, not post-action effects or all branch
conditions throughout an action. Record the fresh evidence and refusal reason;
unknown/exception must stop later task input while releases bypass the callback.
Test stable controls, wrong/unknown/presence changes before and within a chord,
callback failure, changed source/expiry, and releases. Do not claim this removes
the unobserved interval between capture and press or bounds blocked native I/O.

## Evidence

[SOURCE_PINS.json](SOURCE_PINS.json) records 91 selected current Git/worktree
joins, inherited as the prior composed-path source selection and checked against
this main. This is not a complete import closure. The two raw record archives
include retained native bridge files as exact hex, selected graph observations,
all newer native frames and callback/control witnesses. Process IDs, optimization,
commands, conditions and complete streams are retained. Source refs are inert
`.py.txt` files with original local bindings; no failing probe is registered as
a passing runtime regression.

The saved-only reader reopens retained PNG bytes, verifies artifact hashes,
decodes the marker separately from the callback, and checks all eight outcomes,
emissions, prefixes and control rows. Six copied contradictions are rejected in
each reader mode. It imports no candidate and performs no application scoring.
Historical results remain immutable; #57/#59/#17 remain open. Real semantics,
native timing, finite semantic recovery and matched economics remain unqualified.
