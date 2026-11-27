# Calc transfer: saved evidence convergence

2026-10-16; checked main `0734955499d62c55c41bb5c3f71cab85a0724cf2`.
This is a saved-only recheck, with **zero new GUI/model/WSL allocations**.
It connects the completed Calc block to the current work map without repeating
the historical producer or editing any of its 568 tracked files.

## Read the final publication, not the partial snapshot

The original [README](../../../runtime/results/calc-owner-transfer-live-01/README.md)
is a retained one-case checkpoint. The later
[final report](../../../runtime/results/calc-owner-transfer-live-01/FINAL_REPORT.md),
[block result](../../../runtime/results/calc-owner-transfer-live-01/BLOCK-RESULT.json)
and [publication](../../../runtime/results/calc-owner-transfer-live-01/PUBLICATION.md)
retain all four cases. The final publication also supersedes the earlier
pending-accounting statement with **joint usage only**. Preserve those historical
snapshots; their different dates/scopes are not contradictory current grants.

The frozen recipe uses public `GuardedSessionOwner.run_compiled` versus an
ordinary callback with the same owner and local evidence. It is one familiar
Calc workflow with conditional Save, explicit primary review/modal handling,
no retry and no repair. It is not a plain/current + optimized + integrated
three-arm economics comparison, or a current-source live qualification.

| Retained case | Raw local method terminal | Independent saved workbook | Save requests | Captures / input emissions |
|---|---|---|---|---|
| ordinary-normal | SAFE_YIELD / effect_unavailable | A1=731, A2=864 | 1 | 20 / 27 |
| compiled-normal | SAFE_YIELD / effect_unavailable | A1=731, A2=864 | 1 | 20 / 27 |
| compiled-wrong | SAFE_YIELD / effect_failed | Empty | 0 | 11 / 21 |
| ordinary-wrong | SAFE_YIELD / effect_failed | Empty | 0 | 11 / 21 |

Normal saved effects are scored after the original keeper terminates; the raw
method's modal yield is not relabelled task success. Wrong-input refusal is a
successful control check, not successful completion of the requested task.
The saved auditor independently opens XLSX bytes with openpyxl; its OCR check
reuses the frozen cue over retained TSV, rather than independently rerunning OCR.

## Requirement-to-evidence and next work

| Requirement | Existing evidence retained and rechecked | Remaining boundary / decision |
|---|---|---|
| Fresh observation and conditional continuation | Exact source PNG/base64 joins, frozen observation sequence, local cell cue, Save pixel dependency stages | App-local ROI/primary-review assumptions; no atomic capture-to-input guarantee or general target generation proof |
| Task effect distinct from delivery | Saved XLSX hash/source equality and independent cell scoring; raw terminal/prefix preserved | Familiar workflow only; no general collateral/effect predicate or current-main live claim |
| Release and cleanup | Per-program neutral receipts, same-owner close, saved absent-child/termination record | Historical receipt consistency only; no blocked native-I/O physical bound or cross-process custody proof |
| Unknown/wrong evidence and recovery | Wrong value 863 stops before Save; modal yields retain prefix | No repair attempt in this block; bounded task recovery remains unmet |
| All-attempt model accounting | usage-02 reconstructs 359 retained source records and exactly 20 delivered original images | Joint preparation/development/interleaved migration/four cases/audit window; no per-route attribution, billing or immutable model attestation |
| Matched efficiency and transfer (#57) | Both routes retain their normal/wrong results with equal matching-condition event counts | HOLD efficiency gain and general readiness; cold/warm/invalidation/repair, matched model/settings, repetitions and end-to-end uncertainty remain necessary |

The next economics work should reuse this app-local recipe and the existing
#57 comparison design, qualify the chosen current source, then freeze the missing
matched phases and accounting before a permitted fresh run. Saved reconstruction
does not authorize a run. The current local/Fake X scope permits independent
reader and composition checks without consuming or restarting these four cases.

## Executed reconstruction and Windows mutation repair

`check_saved.py` checks all **567 publication manifest members**, runs the original
read-only mechanics auditor and 18 original semantic mutation assertions, then
calls the retained usage verifier with `check_original=False`. Normal and `-O`
runs pass; their JSON and stderr are retained beside this file. The private
original session is not available/checked here; its earlier check remains a
historical claim, distinct from this public projection reconstruction.

The first unmodified Windows mutation run has **5 failures out of 18**. Its
overlay uses forward-slash keys but `str(Path)` returns backslashes, so four
mutations bypassed the overlay and a fifth reached the wrong earlier check.
The separate runner overrides only `read` to normalize overlay lookup through
`Path(...).as_posix()`. All expected assertions remain unchanged, and all 18
pass. Original audit/test/source/raw remain byte-identical. First-failure and
portable-control logs are retained, not replaced by the successful runs.

The reconstructed joint totals are input **20,107,987**, cached input
**19,377,536** (included in input), uncached input **730,451**, output **99,185**,
reasoning output **30,102** (included in output), total **20,207,172**.
Never add the nested usage-01 window. Later accounting/publication work is
outside that historical window, not free. No route cost or speedup follows.

Reproduce from an exact Git archive extraction (Python, Pillow and openpyxl):

```text
python check_saved.py <extracted-root>/runtime/results/calc-owner-transfer-live-01
python -O check_saved.py <extracted-root>/runtime/results/calc-owner-transfer-live-01
```

Do not execute keeper, composition, producer or collection scripts to reproduce
this check. `SOURCE.json` pins the archive source; `SHA256SUMS` covers this new
runner/report/log packet. Current task parents #57/#59/#2789 remain open.
