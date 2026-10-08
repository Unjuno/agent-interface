# Observation Epoch XTerm Focus ABA R3 — retained construction failure

Issue #1625. Parent #42. Predecessors #1580/#1594.

## Disposition

**FAIL_FOCUS_ABA_VALIDITY_LEAK**

Construction1 / formal0 / reruns0 / replacements0 / tuning0. This allocation is not retried.

## Analytical premise

Endpoint equality cannot establish continuous focus validity: both stable A→A and ABA A→B→A produce the same initial/final focus value. The experiment therefore added a separate FocusIn/FocusOut event-generation witness.

## Construction result

40 stock-XTerm/private-Xvfb rows, eight per arm.

- equality-only FOCUS_ABA joins: 8/8
- generation-witnessed FOCUS_ABA joins: **1/8** → failure
- ABA rows with observed focus events: **7/8**
- FOCUS_CHANGE event witness: 8/8
- generation-witnessed FOCUS_CHANGE joins: 0/8
- generation-witnessed identity-mismatch joins: 0/8
- stable+paint generation-witnessed joins: 16/16
- stable+paint focus-event contamination: 0/16
- noncritical image/title age within frozen 2 ms: 40/40
- candidate/oracle metric mismatch: 0

The failing row is the first FOCUS_ABA case. Initial and final focus were both A, observer generation stayed1→1, and no focus events were received, so the event-generation candidate falsely treated the ABA interval as continuously valid.

Every later FOCUS_ABA row observed the expected four-event sequence:
`FocusOut(A) → FocusIn(B) → FocusOut(B) → FocusIn(A)`.

All eight persistent A→B FOCUS_CHANGE rows also produced events.

## Failure diagnosis

During the same construction process Xlib emitted `BadMatch` for `SetInputFocus` on the B XTerm resource. Window discovery used root-child appearance, which does not prove the new XTerm is already viewable/focus-ready. The first ABA row occurs early; later B focus transitions succeed.

Leading explanation: **first-use XTerm-B readiness is insufficiently gated**, not a demonstrated failure of generation semantics once events are observable.

This remains a hypothesis. The failure is not relabeled or excluded.

A legal successor may change exactly one harness condition: require both XTerm windows to be `IsViewable` and pass an excluded pre-science focus A→B→A witness check before starting construction. It must use a new task/allocation identity and keep the ABA arm and 2 ms noncritical budget unchanged.

## Evidence

The exact executed source, 40-row construction raw, failed primary audit and independent audit are stored in `retained_failure_bundle.tar.gz.b64`.

- tar.gz SHA-256: `f7c0ddeffc2e788bd1655bc5dd68cda66fbda3f3aa3dd77ab71115d93e594125`
- base64 SHA-256: `46571ea5a8517442731f8b034485dfef3d4790158c783c6fd4ad66690815a33d`

Use `reconstruct_bundle.py` to recover the exact retained files.

## Scope

No task action, model/provider/network/user desktop/shared-runtime mutation. PAINT_ONLY uses XClearArea/Expose as presentation-only fixture mutation. No model/token/task-success/latency/general-GUI claim.
