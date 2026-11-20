# MAP01 matched-v2 decision-window boundary audit (2026-10-04)

Status: **CONSTRUCTION FAIL; NO LIVE LEASE USED**

## H / T / D / C / U

**H — hypothesis.** The matched-v2 runner freezes the common planner-wait decision-window end immediately after its fixed-delay timer, before fallback cancellation and input-release cleanup.

**T — test.** Against current `origin/main` `f2aa59c8bac88f0091eb24c4f462f55a72303d2f`, compare source offsets for `timer.cancel()`, the fallback release wait, and `planner_end_ns = session.runtime_clock()` in `research/doom/map01_recovery_cover_matched_v2_runner.py`. No model, game, GUI, OS input, or formal allocation was invoked.

**D — result.** `FAIL_BOUNDARY_CONTAMINATION`: the endpoint assignment follows both the fallback release wait and cleanup. The runner therefore includes arm-dependent cleanup time in the measured planner window. It cannot support the frozen matched comparison until a prospective version moves the boundary before cleanup and tests that ordering.

**C — alternatives.** A release event may arrive before the fixed-delay timer on some runs, reducing contamination in those observations; this does not repair the source-defined boundary or guarantee equal exposure across arms. Existing v6 construction work repaired this pattern for v6, but does not establish that matched-v2 uses that repair.

**U — scope.** Static construction diagnostic only. No runtime efficacy, useful effect, release correctness, or causal arm comparison was measured. This does not authorize the reserved `map01-recovery-cover-matched-live-v2-01` allocation and does not replace Issue #59's requested same-episode useful-effect or strong-simple-reference test.

## Reproduction

PowerShell, from the repository root:

```powershell
$src = Get-Content -Raw 'research/doom/map01_recovery_cover_matched_v2_runner.py'
$start = $src.IndexOf('timer.cancel()')
$release = $src.IndexOf('session.wait(lambda r: r.get("event") in {"input_released"', $start)
$end = $src.IndexOf('planner_end_ns = session.runtime_clock()', $start)
[ordered]@{
  timer_cancel_offset = $start
  release_wait_offset = $release
  endpoint_offset = $end
  endpoint_precedes_release_wait = ($end -lt $release)
  disposition = if ($end -lt $release) { 'PASS' } else { 'FAIL_BOUNDARY_CONTAMINATION' }
} | ConvertTo-Json
```

Observed offsets: timer cancel `16311`, release wait `16563`, endpoint `16884`; predicate `false`; exit code `2` when run with the explicit fail-on-late-end predicate. The runner blob at the tested current-main commit is `59c071c3453b516ff370e1b3533511b1f3ce486f`.

**Independent audit.** Re-read the runner control flow: after `timer.cancel()`, the nonterminal branch sends cancellation, waits up to three seconds for `input_released` / `input_release_unverified`, waits for the fallback terminal, and only then samples `planner_end_ns`. This independently confirms the offset result and identifies exactly which cleanup is included.
