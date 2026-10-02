# Allocation-01 recovery and disposition

This directory preserves the original eight-file candidate package from remote
branch `research/3311-termination-report-v2-20260928` at commit
`037f9ffdb45d0a52ba76436b7f46584c62b21f58`. Those files were copied without
editing. The original branch remains the provenance source; this recovery is
additive and does not alter either the original allocation or its later
successors.

## Observed allocation outcome

Issue #3311 records that allocation
`ISSUE3311-TERMINATION-REPORT-20260928-01` stopped before unittest discovery.
The frozen `run_tests.py` resolved `REPO = HERE.parents[3]` to the parent Codex
folder rather than the checkout root. Its first `git rev-parse HEAD` subprocess
exited 128; the exception occurred before output-directory creation.
`results/local-01` is absent and `test_count=0`. The Issue classifies this as
`STOP_CONSTRUCTION_OR_PROVENANCE`, not a scientific FAIL and not a PASS.

Authoritative Issue record:
[comment #5861676994](https://github.com/Unjuno/agent-interface/issues/3311#issuecomment-5861676994)
(2026-09-28 01:23:13 UTC).

## Freeze/result discrepancy retained

The original `FREEZE.json` is preserved byte-for-byte and contains
`"formal_runs": 1` and expected disposition
`PASS_TERMINATION_HOLD_CONTRACT_SCOPED`. The Issue's execution record instead
says the runner stopped before any test ran (`test_count=0`) and records a
construction/provenance STOP. This package does not reconcile or reinterpret
that discrepancy, and does not treat the frozen expectation as an observed
result. No raw test output or `RESULT.json` was present in the source branch.

The later allocation-02 and allocation-03 results are separate successor
evidence already preserved under
[`issue3311_termination_report_v2/`](../issue3311_termination_report_v2/)
and its Docker successor. They do not rewrite this predecessor STOP.

## No rerun / scope

The frozen `run_tests.py`, `test_supervisor.py`, supervisor, and auditor were
not executed during recovery. Allocation-01 is consumed and its first outcome
is retained; no retry, post-freeze repair, Docker substitution, or scientific
inference was made. This archival recovery adds no experimental result and
does not satisfy Issue #3311's cold/warm/invalidation/repair comparison.

Machine-readable transcription of the Issue's STOP is in
[`recovery/ALLOCATION_01_STOP.json`](recovery/ALLOCATION_01_STOP.json).
