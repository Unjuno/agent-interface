# A04: alias refusal through V13/V15 cleanup

## Question
Does the actual V13 executor cleanup path clear an owned key after the V15 release-batch backend's `up_batch` fails on two names that resolve to one keycode?

## Frozen method
One fake-X case uses current-main V13/V15/V4/V3/V12 source snapshots and a candidate-only duplicate-resolved-keycode guard copied from A03. It submits `a down, A down, a up, A up`; both names map to keycode 38. The V15 flush should raise before a KeyRelease, V13's `finally` should call real V15 `release_all`, and the terminal should publish after cleanup. The fake server records XTest state only.

## Decision
PASS_METHOD_SCOPED only if the batch refusal is visible, V13 terminal is failed, cleanup records a verified release with no keycodes down, and fake server state is empty. FAIL if the completed case contradicts any condition. STOP if setup or the candidate does not complete with a raw record. Preserve the first outcome; do not rerun or overwrite it.

## Limits
No real X11 server, desktop, game, model, physical keyboard, application effect, threat exposure, or live allocation is tested. Guard is candidate-only. This does not satisfy Issue #59's live gate.

Predecessor: A04 stopped before setup due to a missing freeze-check helper; see ../release_batch_alias_executor_cleanup_a04_20261007/STOP.json. A05 is a new one-shot with a new freeze.
