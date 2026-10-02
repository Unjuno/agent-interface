# Issue #59 T1 — held-key autorepeat and focus transfer

This successor tests a distinct boundary beyond the merged T0 experiment:
after focus moves during one still-held W interval, does X11 autorepeat deliver
new `KeyPress` events to the new focused client even though its initiating press
went to the old client?

H/T/D/C/U, source identities, decision gates and limits are in `PLAN.md` and
`FREEZE.json`. The one-shot candidate, independent raw-only auditor, full event
and keymap record, stdout/stderr, run receipt and hashes are retained in
`results/formal-01/`. It uses only a private Xvfb server and XTEST. It is not a
real desktop/game, semantic-effect or MAP01 result.
