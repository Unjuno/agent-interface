# Needle checkpoint worker studies

This evidence bundle contains two distinct records:

- Issue [#4698](https://github.com/Unjuno/agent-interface/issues/4698): pre-freeze full-path treatment consumed on its exact seeds. Typed `STOP_PRE_FREEZE_FULL_TREATMENT_CONSUMED`; no scientific formal PASS/FAIL/HOLD. Raw construction run, independent audit, sources and stop chronology are retained at `research/system1/needle_online_snapshot_resident_worker_4698_v1/`.
- Issue [#4714](https://github.com/Unjuno/agent-interface/issues/4714): successor matched resident-worker storage-path experiment. H/T/D/C/U is in `research/system1/needle_native_volume_checkpoint_4714_v1/PREREGISTRATION.md`; source hashes and one-shot commands are in `FREEZE.json`.

At initial publication, #4714 formal seeds 6842731/33/37 have not run. Construction-only seed 6842703 passed 24/24 independent snapshot/request/prediction/final-byte checks with zero auditor errors and 5/5 corruption controls rejected. In that one construction seed, the Docker-native volume reduced durable-commit p50/p95 to 15.578/18.788 ms from host-bind 33.602/105.506 ms, but did not improve request→ack p95 (181.310 vs 148.593 ms). This does not meet the 60 ms gate and is not formal inference.

The formal volume is a fresh Docker local volume; the container root/source are read-only, and the separate auditor sees raw results and the volume read-only. The runner and auditor have independent implementations. Construction failures and corrections are summarized in `CONSTRUCTION_HISTORY.md` in the #4714 evidence directory; raw formal outputs and audit will be added after the single frozen run.
