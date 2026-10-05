# V39 shared-display owner-pair evidence

This additive package resolves one narrow integration question for PR #7974: whether two current V4/V3/V12 input owners with distinct leases can hold the same key on one X server while one owner's key-up receipt reports the server-global keymap neutral. It does not use a game, real GUI, model, physical input, or live-game allocation.

## First outcomes

| ID | Frozen source | Candidate / audit | Outcome |
|---|---|---:|---|
| A01 | main `6860b585`; PR #7974 `1627581f` | candidate 1 (exit 1); audit 0 | STOP before key-down: `query_keymap()` returned a list and candidate called `.hex()`. Partial raw retained. |
| A02 | A01 source snapshot | candidate 0; audit 0 | STOP before candidate: runner launched Xvfb `:98` but polled socket `X99`. |
| A03 | main `d9bb339b`; PR #7974 `c896362a` | candidate 1 (exit 0); audit 1 (exit 0) | CONFIRMED: A's verified single-key up cleared server-global W while B still held W in local owner bookkeeping. |
| A04 | main `ff677c7f`; PR #7974 `2a79899f` | candidate 0; audit 0 | STOP before candidate: current main and PR head moved after freeze. |
| A05 | main `2f2c83c3`; PR #7974 `b5fbfed1` | candidate 1 (exit 0); audit 1 (exit 0) | CONFIRMED: A's verified one-key `up_batch` cleared server-global W while B still held W locally. |

A03 and A05 support the scope boundary that XQueryKeymap receipts describe shared X-server state, not owner-specific held state. A05 tests one-key `up_batch`; neither experiment tests multi-key ordering in the full V15 release batch. Exclusive display ownership or a cooperative arbiter is needed before treating these receipts as isolated to one owner.

A03/A05 do not close the live threat-control, independently useful feedback, bounded recovery, or MAP01 outcome gate. A03's GitHub snapshot observed Issue #59 CLOSED/COMPLETED while its main documentation said open; the Issue was later reopened. This package makes no Issue status change.

A01 and A02 first outcomes are retained. A03, A04 and A05 freezes, setup records, raw/audit outputs and checksums live in their respective folders.
