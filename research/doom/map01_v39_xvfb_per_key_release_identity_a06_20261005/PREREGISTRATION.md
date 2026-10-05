# A06 preregistration — V39 release-batch identity on Xvfb

**H.** Exact current-main release backend composed with transition owner v4→v3→input owner v12 will produce 40 admissions, 40 identity-joined key-up receipts and 80 ordered X client events over 30 batches. Every batch ends with both test keys up. Original release edges in a batch have no owner keymap query between them; bounded retries occur only after the post-batch sample.

**T.** One run on TCP-disabled Xvfb `:128`; create/focus one mapped synthetic window with `_NET_ACTIVE_WINDOW`, title and geometry; execute two `a` down/up batches and one `a`/`space` chord repeated ten times. Record owner-query times, client events, backend receipts, observer samples and teardown. The results parent may already exist, but the A06 output leaf must not: pass it directly to the candidate, which creates it.

**D.** PASS_METHOD_SCOPED requires frozen hashes, 40 distinct admissions and joined receipts, 80 expected client events, 30 empty observer keymaps, full receipt and batch proofs, no owner query between original ordered releases, stopped/empty owner cleanup, and Xvfb exit 0. Complete mismatch is FAIL; setup/import/timeout/incomplete trace/cleanup interruption is STOP. Candidate once; auditor once if RAW exists; no rerun or overwrite.

**C.** Exact current-main production owner/backend code against a local synthetic X server; immediate parent is a deterministic shim. No game/model/physical input/network/task effect or private live lane.

**U.** Does not establish physical key state, target application consumption, game latency, threat response, useful feedback, recovery or MAP01 completion.

Base main `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`. Exact production source and V15 startup closure hashes are in `FREEZE.json`.
