# Needle checkpoint worker studies

This evidence bundle contains two distinct records:

- Issue [#4698](https://github.com/Unjuno/agent-interface/issues/4698): pre-freeze full-path treatment consumed on its exact seeds. Typed `STOP_PRE_FREEZE_FULL_TREATMENT_CONSUMED`; no scientific formal PASS/FAIL/HOLD. Raw construction run, independent audit, sources and stop chronology are retained at `research/system1/needle_online_snapshot_resident_worker_4698_v1/`.
- Issue [#4714](https://github.com/Unjuno/agent-interface/issues/4714): successor matched resident-worker storage-path experiment. H/T/D/C/U is in `research/system1/needle_native_volume_checkpoint_4714_v1/PREREGISTRATION.md`; source hashes and one-shot commands are in `FREEZE.json`.

The frozen formal run on seeds 6842731/33/37 completed once. Independent audit passed all 72 arm snapshots with zero errors and rejected 5/5 corruption controls. Final decision is `HOLD_LATENCY_BUDGET`: native-volume request→ack p95 was 104.592 / 104.898 / 180.214 ms, all over 60 ms and only 0.947 / 0.783 / 0.983× the bind arm. The volume did reduce durable-commit p95 to 20.089 / 19.848 / 19.919 ms from 100.934 / 121.152 / 114.109 ms. Thus the storage-write stage improved but the full request→ack hypothesis failed its gates. See `FORMAL_RESULT.md` and the machine-readable `FORMAL_RESULT.json`.

The formal volume is a fresh Docker local volume; the container root/source are read-only, and the separate auditor saw raw results and the volume read-only. The runner and auditor have independent implementations. Construction failures/corrections and their exact boundaries are in `src/CONSTRUCTION_HISTORY.md`; raw formal outputs, audit report, final volume snapshot copies and compact Docker logs are retained beside the source. The local formal volume remains available for inspection.
