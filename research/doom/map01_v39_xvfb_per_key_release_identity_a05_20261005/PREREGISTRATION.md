# A05 preregistration — V39 release-batch identity on Xvfb

**H.** Exact current-main release backend composed with transition owner v4→v3→input owner v12 will produce 40 admissions, 40 identity-joined key-up receipts and 80 ordered X client events over 30 batches. Every batch ends with both keys up. Owner keymap samples occur after the ordered original releases in each batch; there is no sample between original release edges. A bounded per-key retry is permitted only after post-batch sampling reports a key still down.

**T.** One frozen run on TCP-disabled Xvfb `:127`: create and focus one mapped synthetic window with `_NET_ACTIVE_WINDOW`, title, and geometry, then run two `a` down/up batches and one `a`/`space` chord ten times. Record client events, owner query intervals, receipts, observer keymaps, and cleanup. Drain Xlib's pending queue before socket waits; retain partial evidence.

**D.** `PASS_METHOD_SCOPED` requires frozen hashes, 40 distinct admissions and joined per-key receipts, 80 correctly ordered client events, 30 empty observer samples, complete receipt and batch proofs, no owner query between original ordered release edges, verified stopped/empty owner cleanup, and Xvfb exit 0. A complete mismatch is `FAIL`; setup/import/timeout/incomplete trace/cleanup interruption is `STOP`. Candidate once; auditor once if raw exists; no rerun or overwrite.

**C.** Exact current-main owner and release-batch production code against a local synthetic X server; immediate parent is a deterministic shim. No game, model, physical input, network, task effect, or private live lane.

**U.** This qualifies software receipt and synthetic X-server ordering only. It does not establish physical key state, target application consumption, game latency, threat response, useful feedback, recovery, or MAP01 completion.

Base main: `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`. Production source and V15 startup closure hashes are in `FREEZE.json`.
