# A06 partial result and retained STOP

The frozen candidate started Xvfb and executed all 30 batches. Its per-batch rows retain 40 admissions and 40 identity-joined V12 key-up receipts. The client trace contains 80 expected X events, and the independent observer sampled an empty keymap after every batch. A separate read-only partial auditor verified all 30 batches had pre/post owner keymap samples, zero owner keymap queries between original release edges, verified joined receipts, and empty post-batch observer keymaps. Raw SHA-256: `f3d38b746fd3c1905fc4385840220824a57b47f160eb73553711b0fe941880d8`.

A06 remains **STOP**, as required by the frozen auditor: after the final batch, harness bookkeeping looked for a nonexistent extra wrapper depth (`owner._inner._inner`) and raised `owner wrapper chain changed`. It therefore did not call owner.close, did not export the owner’s underlying `owner_explicit_keyup` records or terminal `owner_release` receipt, and cannot verify owner thread shutdown. Xvfb itself exited 0 after teardown. The 30/30 ordering characterization is retained in `results/A06/PARTIAL_AUDIT.json`; it supplements but does not override `results/A06/AUDIT.json` STOP.

The partial evidence qualifies release ordering and synthetic server state for this Xvfb run only. It does not establish shutdown success, physical input state, application consumption, game behavior, latency under load, or Issue #59 completion.

For the next distinct construction, correct the wrapper path to the direct inner V12 owner, call the V4 wrapper's `close()` in `finally`, retain its records and thread state, and separately confirm a held-key owner close emits a verified terminal release on Xvfb. No A06 rerun.
