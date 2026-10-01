# Observation Epoch XTerm Focus ABA A2 — retained result

Issue #1639. Direct predecessor #1625 remains an immutable construction failure.

## Disposition

**PASS_OBSERVATION_EPOCH_XTERM_FOCUS_ABA_A2_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## One changed factor

The scientific arms, two candidates, observer semantics and frozen 2 ms noncritical budget are unchanged from #1625.

A2 adds only pre-science readiness:

1. both discovered stock-XTerm top-level windows must be `IsViewable` on two consecutive polls;
2. before row0, a discarded A→B→A focus preflight must produce exactly
   `FocusOut(A), FocusIn(B), FocusOut(B), FocusIn(A)`;
3. those events are drained before scientific generation is snapshotted.

The failed #1625 rows are not pooled.

## Formal result

320 rows, 64 per arm.

- generation-witnessed/oracle mismatch: **0/320**
- equality-only FOCUS_ABA joins: **64/64**
- generation-witnessed FOCUS_ABA joins: **0/64**
- FOCUS_ABA rows with focus-event witness: **64/64**
- FOCUS_CHANGE rows with focus-event witness: **64/64**
- generation-witnessed FOCUS_CHANGE joins: **0/64**
- generation-witnessed IDENTITY_MISMATCH joins: **0/64**
- generation-witnessed STABLE+PAINT joins: **128/128**
- stable/paint focus-event contamination: **0/128**
- all noncritical image/title age within frozen 2 ms: **320/320**
- image payload exactly1024 bytes: **320/320**
- focus restored after every row: **320/320**

Event-generation distributions are exact:

- STABLE: 64 rows with 0 focus events / generation delta0
- PAINT_ONLY: 64 rows with 0 / delta0
- FOCUS_ABA: 64 rows with 4 / delta4
- FOCUS_CHANGE: 64 rows with 2 / delta2
- IDENTITY_MISMATCH: 64 rows with 0 / delta0

The largest image/title noncritical age in any arm is0.821 ms, below the unchanged2 ms budget.

Primary audit passes four corruption controls. Independent audit imports no experiment implementation and checks all320 rows from raw focus-event/readback evidence; errors[].

## Interpretation

#1625 demonstrated that endpoint equality alone is unsafe and that an event witness can itself fail if the observed XTerm is not ready to receive focus.

A2 supports the narrower claim:

> after an explicit viewability/focus-event readiness boundary, a runtime-owned FocusChange generation distinguishes A→B→A from stable A even though initial and final focus values are identical.

Thus an observation epoch cannot generally extend critical-field validity from endpoint equality alone. It needs a continuity witness such as a generation/event lineage, or an equivalent stronger mechanism.

## Source integrity

Formal authority is bound to four exact Git blobs frozen before formal:

- `source/PLAN.md` → `e3ba4e98433c44f7556bdbfb556b16378e58052b`
- `source/run.py` → `aa1f8d7ff873b1ba41dde374582738694803161a`
- `source/audit.py` → `e52ed2cafba369f0b17a2af71e64995fe20abcc5`
- `source/independent_audit.py` → `747d2bae20262df5823707e0528c172f0a46a747`

The earlier tar/base64 construction bundle remains supplemental only because its publication blob identity did not match the local bundle identity; it is not used as formal source authority.

## Evidence limit

The exact 611,682-byte formal row JSON was SHA-256 identified and independently audited locally. This branch retains the exact source Git blobs, full aggregate metrics, witness distributions and both audit outputs, but not every raw row byte. Therefore the repository evidence supports the scoped aggregate claim but is not a standalone byte-for-byte reconstruction of all320 rows.

## Non-claims

Private same-host X11/XTerm only. Focus events prove observed focus transitions, not semantic task effects. No model/token/task-success/latency-saving/human-tempo/general-GUI claim.

## Next boundary

The semantic requirement is now clearer than a numeric skew threshold: **critical observation validity needs an uninterrupted-currentness witness**. A future runtime should likely bind focus/surface generation to observation epochs rather than maintain an ad hoc focus-only counter. Before runtime promotion, transfer the same rule to one second application/substrate and include surface/process incarnation changes, not only focus ABA.
