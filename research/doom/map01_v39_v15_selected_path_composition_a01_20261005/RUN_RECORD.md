# A01 run record

- Allocation: A01, preregistered in Issue #59 comment 5986926684.
- Frozen main base: `f60752d0fb71595363a80977636ca74c1fd10b21`.
- Candidate: invoked once; exit 0. No retry.
- Auditor: invoked once; exit 1 with status `FAIL`. No retry or post-run modification.
- Branch intended for delivery: `research/v39-v15-selected-path-composition-a01-20261005`.

## Observation

The frozen synthetic composition selected `session_map01_v15.py`, installed the pinned release-batch backend v1 and Executor v13, and completed SPACE/F8 releases. Trace order was: UP calls at n13 and n16; no `query_keymap` between them; owner state queries at n18–n21; post-batch keymap query at n23 and result at n24; release telemetry at n26–n27; terminal cleanup keymap query at n30. Both release rows report `SAMPLED`, no down keycodes, and identity-bound owner explicit-UP receipts with server sync complete.

## Audit disposition

The sole independent auditor failed one overbroad assertion. Its `max(owner_state_after)` included terminal-cleanup query n29, which occurred after the n24 post-batch sample. Earlier owner-state queries n18–n21 do precede the sample. This explains the observed audit failure but does not convert it to PASS. The audit raw output is preserved; it was not rerun or changed.

## Scope

This is a synthetic source-composition observation only. It does not qualify full V39 startup/controller/game behavior, real X11, physical key state, application effect, threat response, latency, useful feedback, bounded recovery, or gameplay. XSync proves server synchronization only. The failed audit prevents promotion to a passing qualification.
