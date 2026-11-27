# Integrated-efficiency summary provenance A01

This read-only audit separates the source allocation of the standalone legacy summary from the detailed raw run currently retained under the same study label. It does not rerun the computer-control allocation or change any historic result.

## H / T / D / C / U

- **H:** The 131,517 / 136,473 / 56,403 input-token summary came from a distinct fresh Docker allocation, but the merged evidence package contains only aggregate values and no per-call receipts with which to reconstruct them.
- **T:** Verify the frozen PR #2962 and Issue #2558 records; compare their changed-file list to the merge commit; independently sum all per-call usage in the detailed retained trace plus preflights; compare both sets of values and verify call-record joins.
- **D:** `ALLOCATION_ORIGIN_IDENTIFIED_RAW_USAGE_NOT_RECONSTRUCTABLE` only if PR and issue identify a separate fresh allocation, their merged diff has exactly the broker and aggregate summary, detailed raw result usage reproduces the detailed report/reconciliation, and each summary-arm total differs. Otherwise preserve HOLD/FAIL and do not combine allocations.
- **C:** The missing per-call evidence may exist in an external archive or another unpublished location. The bounded public-repository/PR/Issue audit cannot rule that out.
- **U:** No fresh model, GUI, Docker, or formal allocation was run. This does not validate the summary token values, task outcomes, timing, correctness, or the integrated path. It resolves public-record attribution only.

## Frozen identities and reproduction

`FREEZE.json` records hashes for the candidate, captured primary API records, and detailed-run source records. The GitHub responses were captured read-only from PR #2962, its file endpoint, and the specific final #2558 result comment. The checked-out base is the observed `origin/main` commit in Git history.

WSLc is unavailable on this host: WSL package 2.7.13.0 has Ubuntu WSL2, but no `wslc.exe` exists in PATH or the known WSL installation directory. This audit needs only local file reads, so it ran natively in Ubuntu WSL and claims no container isolation. The Git-derived merge path list is frozen as an input so the WSL runner does not depend on a Windows-only `.git` pointer.

From the repository root in Ubuntu WSL:

```bash
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/freeze.py
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/audit.py --write
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/verify.py --write
python3 -B research/live_control/integrated_efficiency_summary_provenance_a01_20261009/manifest.py
```

The candidate audit writes only `result.json`. The detailed result directory, standalone summary, reconciliation, source code, and captured API inputs are read-only inputs. `verify.py` independently checks frozen input hashes, the PR API vs Git merge file list, and the per-arm raw-vs-summary arithmetic. The initial WSL Git-pointer and verifier root-path construction failures are retained in `CONSTRUCTION_FAILURE_A00.md` and `CONSTRUCTION_FAILURE_A01.md`; both corrections are separate from the provenance disposition. `MANIFEST.json` hashes every package file except itself.

## Outcome

The audit distinguishes two facts that share a study label and seed. PR #2962 and its linked Issue result say the summary came from a **new/fresh Docker allocation** against source main `9c9d7cf…`. Its merge diff adds only `formal_host_exec_broker_v1.py` and `integrated-efficiency-live-01-summary.json`. The detailed run's 14 raw model result records plus three preflights independently reproduce 63,128 / 63,779 / 26,563 tokens, not the aggregate summary values. Therefore the summary's allocation origin is identified, but its reported usage cannot be independently reconstructed from the merged public evidence. Keep both records unchanged and do not pool them.

This is an evidence-provenance result for Issue #57's integration gate. It does not satisfy the issue's finite live cold/warm/invalidation/repair comparison or overall completion checklist.
