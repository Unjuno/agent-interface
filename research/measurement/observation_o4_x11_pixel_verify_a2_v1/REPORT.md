# #1870 O4 X11 pixel VERIFY A2 — retained batch0 source-check stop

Task: `OBSERVATION-GATING-O4-X11-PIXEL-VERIFY-A2-20260919-002`

Disposition: **`STOP_BATCH0_PARENT_SOURCE_CHECK_NO_RESULT` / scientific `NONE`**.

#1847 was not rerun. This successor changed only formal packaging from one monolithic 56-row process to eight immutable contiguous 7-row batch processes.

The canonical successor source bundle was frozen after a mandatory readback repair. The first consumed formal batch (batch0, schedule indices0..6) exited in 0.66 s with `parent source mismatch` before any X11 scientific row was durably serialized. `BATCH_00.json` is absent. Per the frozen contract, batch0 was not rerun and batches1..7 were not started.

A read-only post-stop diagnostic over the same reconstructed `formal_source` directory recomputed all five parent science source hashes (`fixture.py`, `runner.py`, `audit.py`, `PLAN.md`, `SCHEDULE.json`) and found exact equality with the embedded expected hashes. The mismatch therefore could not be reproduced after the consumed invocation. This inconsistency is retained rather than repaired in-place.

- logical formal allocations: 1;
- consumed batch process invocations: 1;
- durable formal rows: 0;
- batch reruns/replacements/tuning: 0/0/0;
- scientific disposition: NONE.

A legitimate successor may change one harness factor: perform source identity verification once as a frozen immutable preflight before any batch allocation, then run batches from the verified read-only source directory without the redundant in-batch parent-source equality guard. Scientific rows, schedule, fixture and O4 gates remain unchanged.
