# A04 preregistration — V39 per-key release closure on Xvfb

**H.** Current-main V39 release-batch backend plus transition owner v4→v3→input owner v12 will produce 40 admissions, 40 joined key-up receipts, and 80 ordered XTest client events across 30 release batches. Each post-batch server keymap sample will show both test keys up. No owner `query_keymap` call will occur between explicit key-ups; only terminal owner cleanup may query it.

**T.** Run one frozen candidate under local TCP-disabled Xvfb `:126`. Create and focus one synthetic window. Execute two single-key `a` down/up batches and one chord batch (`a` down, `space` down, `space` up, `a` up), repeated ten times. Capture backend receipts, client-dispatched events, unrelated X protocol events, all keymap queries, post-batch keymaps, and shutdown. Ignore and retain unrelated non-key X events while waiting for the expected key event; any unexpected key press/release is a mismatch. Do not query keymap between any key edges. Store partial raw evidence as events arrive.

**D.** `PASS_METHOD_SCOPED` requires frozen hashes, 40 unique `(id, step, key)` admissions and matching release receipts, 80 correctly ordered client events, 30 expected batch groups with empty post-batch keymaps, full release-batch proofs, exactly one owner keymap query after all explicit key-ups, verified empty/stopped owner cleanup, and Xvfb exit 0. A complete event/order/receipt mismatch is `FAIL`; setup/import/timeout/incomplete-trace/cleanup interruption is `STOP`. Candidate once, raw-only auditor once, no rerun or overwrite.

**C.** Exercises the current-main release-batch backend and its real Xlib owner wrappers against one local Xvfb client. The immediate base backend and lease are small test shims. No desktop app, physical input, Doom, game progression, model, network, task effect, or Issue #59 private lane is involved.

**U.** This is only synthetic X-server instrumentation/receipt-order qualification. It cannot establish physical key state, target-application consumption, game latency, threat response, useful feedback, recovery, or MAP01 completion.

The base freeze is `d3a51bc4c962b223d05280225042b96a033df8bf`. All source, candidate, auditor, and exact V15 startup-closure SHA-256 values are in `FREEZE.json`.
