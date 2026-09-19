# Common finite authority lifecycle across keyboard and pointer

Task: `VIRTUAL-DEVICE-COMMON-LIFECYCLE-20260917-A2`, Issue #625, scoped Rung-1 successor to #574.

**Decision: `PASS_COMMON_LIFECYCLE_KEYBOARD_POINTER_SCOPED`.**

## Frozen question
Can one modality-independent finite authority envelope preserve the same completion, owner-deadline expiry, explicit cancel, post-expiry no-revival, action-subset and deterministic release semantics when the lowering adapter changes only between an X11 keyboard key and a pointer button?

This is not a full common virtual-device substrate result: touch/multitouch, simultaneous contacts, cross-platform backends, task correctness and performance promotion are outside scope.

## Execution history
- Construction attempt 1 stopped before task input because controller-side Python-Xlib did not inherit `XAUTHORITY`. Only controller environment propagation was repaired before source freeze.
- Final excluded construction: 8/8 pass across keyboard/pointer complete/deadline/cancel plus keyboard stale continuation and pointer wrong-resource.
- A1 used one monolithic `run_formal.py` process. The outer execution tool stopped after 120 seconds: 12 complete first outcomes retained, next case partial/no result. A1 is `STOPPED_INFRASTRUCTURE_TIMEOUT`, was not resumed, and is not pooled into A2.
- A2 changed orchestration only: same semantic 40-case schedule and frozen case runner/auditor, each case executed as its own process. 40/40 first outcomes completed once; no case retry or replacement.

## Formal A2 result

| modality | scenario | n | pass | relevant presses | relevant releases |
|---|---|---:|---:|---:|---:|
| keyboard | complete | 4 | 4 | 4 | 4 |
| keyboard | deadline | 4 | 4 | 4 | 4 |
| keyboard | cancel | 4 | 4 | 4 | 4 |
| keyboard | stale_continue | 4 | 4 | 4 | 4 |
| keyboard | wrong_resource | 4 | 4 | 0 | 0 |
| pointer | complete | 4 | 4 | 4 | 4 |
| pointer | deadline | 4 | 4 | 4 | 4 |
| pointer | cancel | 4 | 4 | 4 | 4 |
| pointer | stale_continue | 4 | 4 | 4 | 4 |
| pointer | wrong_resource | 4 | 4 | 0 | 0 |

All 32 non-wrong-resource cases delivered exactly one relevant application press and one release and ended with the relevant physical state neutral. All eight wrong-resource cases returned `OUT_OF_SUBSET` and emitted zero relevant task input. All eight stale-continuation cases released at expiry and rejected the second down as `EXPIRED`; no authority revival was observed.

The frozen audit's descriptive trigger-to-application-release median over complete/deadline/cancel cases was 0.803220 ms for keyboard and 0.835279 ms for pointer; maxima were 1.421061 ms and 6.052711 ms respectively. No latency threshold or speed claim was preregistered.

## ERROR CHECK
The first direct audit invocation on A2 reported zero rows because the frozen A1 auditor globs `case-*` while A2 deliberately prefixes directories `a2-case-*`. That failed audit is retained. No case was rerun and the auditor source was not edited. A read-only namespace view stripped only the `a2-` directory prefix and the identical frozen auditor then returned 40 cases, 40 pass, errors 0 and `PASS_COMMON_LIFECYCLE_KEYBOARD_POINTER_SCOPED`.

An independent postformal verifier binds all 40 result IDs to the frozen A2 schedule, checks the original source SHA-256s, app event order, neutral terminal state, subset rejection and no-revival semantics: PASS, errors 0. Six copied-evidence corruptions are rejected 6/6: missing case, press-count mutation, neutral-state mutation, wrong-resource admission, stale authority revival and modality flip.

## H / T / D / C / U
**H:** one finite authority/release envelope can span keyboard and pointer-button adapters without weakening lifecycle correctness.

**T:** 40 fresh Xvfb/Tk cases, 2 modalities × 5 scenarios × 4 reps, actual XTEST events, independent Tk application logging and X11 final-state verification.

**D:** `PASS_COMMON_LIFECYCLE_KEYBOARD_POINTER_SCOPED`.

**C:** both modalities use XTEST and the same X server; success may reflect common X11 event semantics rather than a genuinely device-independent substrate.

**U:** no touch/multitouch or simultaneous-contact representation, no true virtual device creation, no Windows/macOS transfer, no application-level task effect, and no performance claim.

## Next rung
Do not promote #574's full substrate yet. The next discriminating experiment must use a true simultaneous-contact modality (real multi-contact touch/gesture-capable fixture) while keeping the same authority/expiry/cancel/release envelope, and must verify that contact identity cannot alias pointer identity.
