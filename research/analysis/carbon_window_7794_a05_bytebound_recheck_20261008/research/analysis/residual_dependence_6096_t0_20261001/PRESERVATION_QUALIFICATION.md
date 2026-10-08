# Preservation qualification (2026-10-02)

Retain this host-only synthetic record with its original `FAIL_METHOD_NO_ZERO_FALSE_YIELD_DETECTION_FRONTIER` disposition. This is historical failure/corroboration evidence, not a successful detector, live-system result or runtime promotion. Source, preregistration, raw outputs, audit, report, hashes and chronology remain unchanged.

Two static-review qualifications apply:
- PLAN.md states a running-mean threshold of 1/5, while public.json, candidate.py, audit.py and REPORT.md use 1/4. The executed baseline therefore does not exactly match that PLAN statement; no result for a 1/5 rerun is claimed.
- The raw calibrated-dependence row for the danger case says `CONTINUE_TO_HORIZON` with `seen_samples=8`. The `calibrated_danger_stop_sample` / `calibrated_sentinel_stop_sample` fields naming 8 in the audit/run record denote the observed horizon in this case, not an actual stop or alarm at sample 8.

The original finite no-zero-false-YIELD frontier failure and the report's parallel-evidence coordination qualification are preserved. The candidate and independent auditor were not rerun, no replacement output was generated, and no new allocation was consumed. Issue #6096 remains open; this merge does not establish general sentinel failure, calibrated statistical validity, GUI/game behavior, safety, or product benefit.
