# Quarantined idle owner close versus a later held key

Two fresh WSLc cells test the unmerged [#10074](https://github.com/Unjuno/agent-interface/pull/10074) candidate at `da3545ad` after an idle read-only observation timed out with its private Xvfb stopped. The source snapshot matches the [preceding owned-RPC trial](../wslc_idle_owned_rpc_recovery_20261101) byte for byte. After server resume and completion of the late RPC, a **separate test client** pressed and held `a`; the test did not use an old-owner held input.

| Cell | Intervention during hold | Readback before / after | Explicit fixture release |
|---|---|---|---|
| hold-a01 | Close quarantined old owner | down / down after 352.105 ms | key up |
| hold-a02 | Withhold old close until after release | down / down after 350.608 ms | key up |

Both cells observed the server stopped and an owner RPC pending before the 500 ms timeout. After resume, the owner remained failed/review-required. In the intervention cell its close retired the old process, attempted no automatic release and reported cleanup `UNKNOWN`; the control closed the old owner only after the test client released. The separate synthetic target recorded one `a` press and release and value `a` in each cell. Both private servers and targets exited zero. The target was changed from the earlier fixture only to accept the selected display name.

These are two sequential, fixed-order, one-sample cells on different X servers. Key state was sampled before and after the interval, not continuously; the target event record supplies an additional observation but does not prove events cannot be missed. The old operation was a read-only capture, and no old owner held a key across the stop. Therefore this is evidence about preserving a later client's hold in these cells, not proof of cleanup of an old held input, absence of all delayed events, hard timing, general reliability, MAP01 completion, or production readiness. WSLc reported that the 1 GiB memory limit excluded swap.

`public.zip` retains frozen sources, conditions, screenshots, owner/target receipts and raw timestamps; SHA-256 `01bd7abe6c2a1003b5af5671578d68f228537f00c2a71f1c50671b626d325509`. With commit `f429fa73d5673c902c6939bac76a68a66ee48e27` available, run `python research/integration/wslc_idle_owned_late_close_hold_20261101/audit.py` without `-O`. It checks archive/source hashes, the target's display-only change, close/withhold ordering, recorded key states, target events and old `UNKNOWN` receipts. It cannot independently recreate historical X event delivery.
