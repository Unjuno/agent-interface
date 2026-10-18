# A06: V13 executor cleanup after V15 alias refusal

## Question
Does current-main V13 cleanup clear the owned key when current-main V15 release-batch execution raises on duplicate resolved keycodes?

## Frozen method
One fake-X case imports pinned current-main V13/V12/V5 executor and V15/V2 backend source, plus V4/V3/V12 owner source. The candidate-only V12 guard from A03 refuses a batch after both aliases are held. Submit `a down, A down, a up, A up` with fake keycode 38. Capture event/owner records, V13 terminal release, and fake server state.

## Decision
PASS_METHOD_SCOPED only if alias refusal propagates, V13 reports failed terminal with verified cleanup, and the fake server reports no key held. FAIL if the completed case contradicts a condition. STOP if setup or candidate does not complete with raw evidence. Preserve first outcome; do not rerun or overwrite.

## Limits
Fake X is not native X11 and does not establish physical input or application behavior. Guard is candidate-only. No live game, model, threat exposure, or Issue #59 live gate.

Predecessors A04 and A05 stopped before setup/action due harness omissions. Their records remain in their separate experiment directories.
