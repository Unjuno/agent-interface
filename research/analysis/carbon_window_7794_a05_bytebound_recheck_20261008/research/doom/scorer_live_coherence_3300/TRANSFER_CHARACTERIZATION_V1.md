# #3300 Obstac transfer characterization v1

Decision: `PASS_TRANSFER_CHARACTERIZATION_SCOPED`

This is a bounded characterization on the public bundled fixture. It is not the #3300 formal private-fixture allocation and does not modify or replace #944, #1461, or #3270.

## H/T/D/C/U

- H: The ViZDoom 35 Hz API bracket can be independently reconstructed under idle, CPU-load, and delayed-read conditions.
- T: Fresh Docker container, `vizdoom==1.2.3`, bundled `basic.wad` MAP01, hidden `ASYNC_PLAYER`, 35 Hz; six rows per stratum; up to three immediate attempts per row; retain both episode tic reads and monotonic bracket spans.
- D: Raw row summary, stratum counts, independent recomputation, and hash are retained. No scorer label is trusted by the auditor.
- C: Scoped PASS requires 18/18 rows with independent recomputation matching the recorded coherence decision and no cleanup failure. It does not qualify live phase/load reliability.
- U: Bundled fixture only; no private fixture, no production scorer integration, no phase-offset schedule, no formal episode-disjoint allocation, no model/GUI/input, no gameplay or efficacy claim.

## Results

- Container/package: `OBSTAC_VIZDOOM_IMPORT PASS version=1.2.3`
- Fixture: bundled `basic.wad`, MAP01; ticrate 35; `ASYNC_PLAYER`
- Rows: 18 total, 6 per stratum
- Idle: 6/6 coherent, 0 all-three-failed
- CPU load: 6/6 coherent, 0 all-three-failed
- Delayed read (20 ms sleep): 6/6 coherent, 0 all-three-failed
- Independent recomputation: `true`
- Raw-row SHA-256: `9711b963cbd856ae34ad2f0d43cf27e6e3ca91c4168237daaaed4a2b572ceb28`

The delayed-read rows remained within one episode tic in this fixture, so this run does not measure a nonzero live crossing distribution. That is an observation, not evidence that the production scorer is universally coherent.

## Formal #3300 gate remains open

The next formal run must use the frozen current-main scorer source, private deterministic MAP01 fixture, declared phase offsets, idle/fixed-load/delayed-read strata, three-attempt traces, independent auditor, and SHA-256 manifest. Until those conditions are met, retain `HOLD_LIVE_SPAN_UNIDENTIFIED` for the issue-level live-coherence claim.
