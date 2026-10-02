# Issue #5694 A02: event-count versus time-weighted opportunity coverage

Allocation: `EXOGENOUS-OPPORTUNITY-5694-A02-EVENT-TIME-20261003-01`
Base main: `523ff6d3ae8b9ee09b435dd7460e6582b8d0d258`
Evidence path: `research/analysis/exogenous_opportunity_5694_event_vs_time_a02_20261003/`

## H / T / D / C / U

- **H:** Event-count opportunity coverage and time-weighted control coverage are distinct estimands when opportunity durations vary. A finite ledger that reports both from one frozen stream will expose a deliberate route-ranking reversal, make the two measures coincide under an equal-duration control, and refuse event-denominator claims when no independent onset schedule exists.
- **T:** Python standard-library-only finite traces; integer time units; no sleep, model, GUI, live input, network, GPU, or runtime import. Candidate emits three fixtures: (1) four equal-duration opportunities; (2) ten disjoint 1-unit opportunities plus one disjoint 90-unit opportunity, with one route covering the long opportunity and another covering all ten short opportunities; (3) no independent onset schedule, for which opportunity coverage must be UNKNOWN/HOLD. The independent raw-only auditor re-derives eligibility, event count, and union-duration coverage from frozen raw rows, not candidate summaries. Four negative controls: omit a short opportunity; alter a duration; double-count overlapping coverage intervals; fabricate an onset schedule in the no-onset fixture. Run one candidate and one separate auditor in native WSLc, CPU-only, network none, with local cached Python image, read-only input and distinct output. No retries.
- **D:** `PASS_METHOD_SCOPED` only if both estimands are separately reconstructed; equal-duration control agrees; heterogeneous fixture yields event coverage 1/11 vs 10/11 while duration coverage is 90/100 vs 10/100; no-onset remains HOLD with no invented denominator; and all four mutations are rejected. Any denominator promotion, missing cue, double count, or mismatch is FAIL_METHOD/FAIL_AUDIT; provenance/runtime gate failure is STOP/HOLD, not scientific FAIL.
- **C:** A duration-weighted opportunity measure is not a task-value or severity measure; event count is not time occupancy. Either alone can be appropriate for a separately declared question. Synthetic schedules do not establish that either route is better in live control.
- **U:** Authored, disjoint finite schedules only. No causal route comparison, real cue acquisition, actual action/effect, independent live scorer, gameplay, human-tempo, safety, or product claim. Overlapping cue attribution and policy-dependent opportunity generation remain outside this allocation.

## Frozen source plan

Candidate: `candidate.py`; auditor: `audit.py`; construction checks: `test_contract.py`. Candidate/auditor at most 1 invocation each; retries 0. Python standard library only. The auditor uses independently authored expected raw fixture constants and recomputes both estimands. Inputs and source are read-only in the formal container; result output is written to a distinct writable mount. Preserve first outcomes exactly.

## Runtime gate

Microsoft native WSL Containers (`wslc.exe`), local image identified by immutable image ID and platform at launch; no pull/build/install; `--network none`, read-only source, 1 CPU, bounded memory/PIDs if supported. Record any WSLc cgroup/swap warning and do not infer host enforcement from requested configuration.