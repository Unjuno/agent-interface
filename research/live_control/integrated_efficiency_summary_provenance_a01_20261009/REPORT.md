# Legacy integrated-efficiency summary: provenance and raw-usage audit

Run `integrated-efficiency-live-01-summary-provenance-a01` checked whether the three conflicting token totals were an arithmetic error in the retained detailed run or a separately published allocation without call-level receipts.

## Result

Disposition: `ALLOCATION_ORIGIN_IDENTIFIED_RAW_USAGE_NOT_RECONSTRUCTABLE`.

| Arm | Detailed trace + preflight | Existing raw reconciliation | Legacy summary from separate allocation | Difference |
|---|---:|---:|---:|---:|
| Plain | 63,128 | 63,128 | 131,517 | 68,389 |
| Ephemeral | 63,779 | 63,779 | 136,473 | 72,694 |
| Persistent | 26,563 | 26,563 | 56,403 | 29,840 |

The detailed side has 14 raw `result.json` records plus three preflight records, and the raw records join the trace. Its totals match the detailed report and prior reconciliation. The other values belong to a distinct fresh Docker allocation: the merged PR #2962 description and its final Issue #2558 result record both say so. The PR merge changed exactly two files: the host usage broker and the aggregate summary. It did not publish per-call result/event files for the summary allocation.

## H / T / D / C / U

- **H:** The standalone aggregate came from a separate allocation, and its actual token usage cannot be reconstructed from the merged public evidence.
- **T:** Frozen PR/Issue API records and merge paths were checked against the same-study retained detailed trace, report, summary, and prior raw reconciliation. A second script verifies all frozen hashes and independently recounts the token totals.
- **D:** PASS for separate-allocation attribution; HOLD for the aggregate usage values as an independently unverifiable measurement. Do not overwrite, pool, or relabel either record.
- **C:** The separate run's call receipts may be retained outside this public repository. This audit only establishes what is available in the examined public record.
- **U:** No model or GUI was called. No computer-control task success, efficiency gain, speed, correctness or product claim is made. Issue #57's integrated live comparison remains outstanding.

## Execution

Frozen repository base: `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`; PR source-main label: `9c9d7cf2bea50e47638c63effa72a5059fdb4e58`; provenance merge: `13d0ccbf2559cc1f70aa2652497ae941ceb13eb7`. WSL package was 2.7.13.0; WSLc was not installed. The audit ran as native Ubuntu WSL Python 3.12.3 because it reads local evidence and requires no container boundary. Freeze hashes and the structured candidate result are in `FREEZE.json` and `result.json`.

Commands, from the repository root in Ubuntu WSL:

```bash
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/freeze.py
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/audit.py --write
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/verify.py --write
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/manifest.py
```

Candidate audit exit code: 0. Independent verifier exit code: 0. No model, GUI, container, networked benchmark, or formal allocation ran.
