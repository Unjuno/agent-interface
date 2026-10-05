# V39 shared-display owner-pair evidence

This additive package resolves one narrow integration question for PR #7974: whether two current V4/V3/V12 input owners with distinct leases can hold the same key on one X server while one owner's key-up receipt reports the server-global keymap neutral. It does not use a game, real GUI, model, physical input, or live-game allocation.

## First outcomes

| ID | Frozen source | Candidate / audit | Outcome |
|---|---|---:|---|
| A01 | main `6860b585`; PR #7974 `1627581f` | candidate 1 (exit 1); audit 0 | STOP before key-down: `query_keymap()` returned a list and candidate called `.hex()`. Partial raw retained. |
| A02 | A01 source snapshot | candidate 0; audit 0 | STOP before candidate: runner launched Xvfb `:98` but polled socket `X99`. |
| A03 | main `d9bb339b`; PR #7974 `c896362a` | candidate 1 (exit 0); audit 1 (exit 0) | CONFIRMED: A's verified single-key up cleared server-global W while B still held W in local owner bookkeeping. |

A03 supports the scope boundary that XQueryKeymap receipts describe shared X-server state, not owner-specific physical state. Exclusive display ownership or a cooperative arbiter is needed before treating them as isolated to one owner. PR #7974 advanced after A03 and now uses `up_batch`; A03 did not test that later batch API.

A03 does not close the live threat-control, independently useful feedback, bounded recovery, or MAP01 outcome gate. GitHub currently reports Issue #59 CLOSED/COMPLETED while main's `docs/CURRENT_GOAL.md` at A03's base says it remains open; this package makes no Issue status change.

A01 and A02 files are retained unchanged. A03 freeze, setup, raw, audit and output checksums live in `A03/`.
