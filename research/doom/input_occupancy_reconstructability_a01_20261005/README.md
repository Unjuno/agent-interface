# Retained MAP01 input occupancy reconstructability

## H/T/D/C/U

- **H:** The retained v38 and v39 traces do not contain enough identity-linked
  physical down/up evidence to reconstruct per-key held occupancy, despite
  containing aggregate `keys_held` snapshots and verified-empty terminal
  releases.
- **T:** Freeze the two reports, event streams, owner-release ledgers, and prior
  posthoc analysis. Count per-key admissions, physical down brackets, release
  measurements, matching actuation IDs, program/step correlation, and aggregate
  cleanup. Do not rerun either allocation.
- **D:** PASS for the hypothesis only if neither run has a complete one-to-one
  down/up actuation record with conservative physical sample intervals and
  program identity. Report `FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE` if either
  run lacks that chain.
- **C:** Existing program intervals and `keys_held` snapshots can bound when a
  program was motor-capable, but they do not prove exact physical edge times or
  per-key occupancy. Aggregate empty release proves final neutral state, not
  each earlier up edge.
- **U:** This audit cannot say that input was stuck, unsafe, or task-effective;
  it only measures what the retained logs can support. First useful task
  feedback also remains unavailable because the effect receipts are viewport
  changes and the independent scorer runs at episode end.

## Result

The two raw traces have 11 and 39 `input_admission` rows, with 11 and 28
`keys_held` snapshots respectively. Their admissions lack actuation IDs,
program IDs, step indices, and physical-down sample brackets. Neither stream
contains `input_release_measurement`; owner ledgers contain only aggregate
`owner_release` records, with no per-key up measurements. Every terminal still
verifies empty input. The hypothesis passes as an evidence-sufficiency finding:
`FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE`.

The minimum future instrumentation is a per-key actuation identity tied to
intent/program/step, conservative physical-down and physical-up sample
intervals, and retention of ordinary as well as emergency up records. First
useful task feedback needs a separate independent effect receipt tied to its
source frame and program. None of this supplies permission to spend a live
allocation.

Reproduce the read-only analysis and independent audit with:

```powershell
python research/doom/input_occupancy_reconstructability_a01_20261005/freeze_a01.py
python research/doom/input_occupancy_reconstructability_a01_20261005/analyze_a01.py
python research/doom/input_occupancy_reconstructability_a01_20261005/audit_a01.py
```
