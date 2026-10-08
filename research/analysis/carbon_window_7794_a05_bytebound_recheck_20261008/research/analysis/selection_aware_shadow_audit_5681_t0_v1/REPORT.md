# Issue #5681 T0 — retained O1 source-capture eligibility audit

## H / T / D / C / U

- **H:** At least one retained O1/O2 result may contain the full per-candidate
  source frame, gate decision and independent semantic label needed to compare
  delivered-only with full-source prevalence.
- **T:** Read-only audit of one completed retained O1 Calc episode from A1
  replicate 1 (`calc-490101-O1`), including `observations.jsonl`, `result.json`,
  the A1 protocol/report, and timestamp-producing source. No old allocation was
  rerun and no source/evidence was modified.
- **D:** `ELIGIBLE` only if every candidate capture has an identity/order,
  observation time with a known time base, delivered/suppressed decision, and
  independent per-capture semantic label. Otherwise `HOLD_NO_ELIGIBLE_SOURCE`.
- **C:** The episode's final Calc workbook oracle and the A1 report's zero
  observed false-suppression count may provide useful task/frame-level checks;
  they do not assign semantic labels to each candidate capture and cannot be
  substituted for the required full-source denominator.
- **U:** This audits one O1 episode only. It does not establish whether other
  O1/O2/O3/queue corpora are eligible, estimate bias, or revise A1's scoped
  result. No GUI or runtime claim is made.

## Result

**`HOLD_NO_ELIGIBLE_SOURCE`**.

The retained episode has 7 candidate captures, 4 delivered observations and 3
suppressed observations. Every row includes `sequence`, `action_id`,
`observed_ns`, `suppressed`, and `reason`. The caller source stamps `observed_ns`
with `time.perf_counter_ns()`, so it is a monotonic nanosecond clock within the
process; it is not a wall-clock timestamp.

However, **0/7 rows has an independent semantic/event/error label**. The episode
has one task-level final workbook oracle (`oracle.success=true`) and aggregate
`false_suppressions=0` / `missed_changes=0`; these are not per-capture labels.
Inferring every frame's semantics from the final saved workbook or from the
gate's own equality decision would violate the independent-oracle requirement.
The essential field is absent, so no delivered-only/full-source prevalence or
inverse-probability estimate is computed.

## Provenance

- Source commit: `3d2dc70a239ff41650438a7d441bb08a094d6272`.
- `observations.jsonl` blob: `408aaba941ea591b15f7506cf90c922bde864226`.
- episode `result.json` blob: `076de61e606c1e3e561cfebff367bfec3c13aca6`.
- A1 `REPORT.md` blob: `3fd79d699ef9f401e57d781b7cbb513dae4abc62`.
- A1 `PROTOCOL.md` blob: `dbd0667bd69c7311da7690d963e2704a384bb15e`.
- timestamp caller `gui_suite.py` blob: `d2e62dcbf7f1ec8ff2ecbd41f6f50475b08b5de5`.
- timestamp receiver `exact_gate.py` blob: `d2629bc94d40cc0a8e1bf9e053585549218629ed`.

Read-only commands, field counts, and exact source paths are retained in
[`AUDIT.md`](AUDIT.md); machine-readable disposition is in [`RESULT.json`](RESULT.json).

The next eligible step would need a different retained corpus with independent
per-candidate labels or a new bounded construction/empirical allocation. This
HOLD does not close Issue #5681 and does not authorize a new GUI lane.
